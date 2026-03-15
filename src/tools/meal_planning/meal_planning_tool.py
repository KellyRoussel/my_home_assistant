from datetime import datetime
from typing import Optional

from models.tools import ToolParameter
from tools.todo_list.add_todo_item_to_list import AddTodoItemToList
from tools.todo_list.todo_tool import TodoTool
from tools.meal_planning.meal_plan_state import MealPlanState
from logger import logger, ErrorMessage


class MealPlanningTool(TodoTool):

    def __init__(self):
        super().__init__()
        self._shopping_tool = AddTodoItemToList()

    @property
    def tool_name(self) -> str:
        return "meal_planning"

    @property
    def description(self) -> str:
        return (
            "Manage a multi-turn meal planning session. "
            "Use 'start' or 'new_session' to begin, 'get_state' to resume an existing session "
            "(only when the user explicitly asks to continue), 'validate_meal' to confirm a meal "
            "(automatically adds its ingredients to the shopping list and saves new meals to the "
            "'Meals' list), 'reject_meal' to decline a suggestion, and 'finish' when done."
        )

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="action",
                description="The action to perform.",
                type="string",
                required=True,
                enum=["start", "get_state", "validate_meal", "reject_meal", "finish", "new_session"],
            ),
            ToolParameter(
                name="meal_name",
                description="Name of the meal (required for validate_meal and reject_meal).",
                type="string",
                required=False,
            ),
            ToolParameter(
                name="target_count",
                description="Number of meals to plan (required for start and new_session).",
                type="integer",
                required=False,
            ),
            ToolParameter(
                name="ingredients",
                description=(
                    "Comma-separated ingredient list for a new meal not yet in the 'Meals' list. "
                    "Only needed for validate_meal when the meal is new."
                ),
                type="string",
                required=False,
            ),
            ToolParameter(
                name="recipe_url",
                description="Optional recipe URL for a new meal. Stored as a note in the 'Meals' list.",
                type="string",
                required=False,
            ),
        ]

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    def execute(
        self,
        action: str,
        meal_name: Optional[str] = None,
        target_count: Optional[int] = None,
        ingredients: Optional[str] = None,
        recipe_url: Optional[str] = None,
    ) -> str:
        try:
            if action == "start":
                return self._start(target_count or 7)
            elif action == "new_session":
                return self._new_session(target_count or 7)
            elif action == "get_state":
                return self._get_state()
            elif action == "validate_meal":
                if not meal_name:
                    return "Error: meal_name is required for validate_meal."
                return self._validate_meal(meal_name, ingredients, recipe_url)
            elif action == "reject_meal":
                if not meal_name:
                    return "Error: meal_name is required for reject_meal."
                return self._reject_meal(meal_name)
            elif action == "finish":
                return self._finish()
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : execute: {e}"))
            raise Exception(f"{self.__class__.__name__} : execute: {e}")

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _start(self, target_count: int) -> str:
        state = MealPlanState(
            active=True,
            target_count=target_count,
            started_at=datetime.now().isoformat(),
        )
        state.save()
        return (
            f"Meal planning session started. Target: {target_count} meals. "
            "Call get_meals_list to see available options, then suggest meals one by one."
        )

    def _new_session(self, target_count: int) -> str:
        existing = MealPlanState.load()
        if existing:
            existing.clear()
        return self._start(target_count)

    def _get_state(self) -> str:
        state = MealPlanState.load()
        if state is None or not state.active:
            return "No active meal planning session. Use action='start' to begin one."
        return state.summary()

    def _validate_meal(self, meal_name: str, ingredients: Optional[str], recipe_url: Optional[str]) -> str:
        state = MealPlanState.load()
        if state is None or not state.active:
            return "No active meal planning session. Use action='start' first."

        token = self._get_access_token()
        meals_list = self._get_todo_list_from_name("meals")

        # Look up the meal in the 'Meals' list
        existing_meals = meals_list.get_items_with_checklist(token)
        matched = next(
            (m for m in existing_meals if m["title"].lower() == meal_name.lower()),
            None,
        )

        if matched:
            ingredient_list = matched["ingredients"]
        else:
            # New meal — add it to the 'Meals' list with ingredients and optional recipe URL
            if not ingredients:
                return (
                    f"'{meal_name}' is not in the Meals list. "
                    "Please provide the ingredients (comma-separated) to add it."
                )
            ingredient_list = [i.strip() for i in ingredients.split(",") if i.strip()]
            note = recipe_url or ""
            task_id = meals_list.add_item_with_note(token, meal_name, note)
            for ingredient in ingredient_list:
                meals_list.add_checklist_item(token, task_id, ingredient)

        # Add each ingredient to the shopping list
        for ingredient in ingredient_list:
            self._shopping_tool.execute(list_name="shopping", item_name=ingredient)

        state.planned_meals.append(meal_name)
        state.save()

        added_info = f"{len(ingredient_list)} ingredient(s) added to shopping list."
        if state.is_complete():
            state.active = False
            state.save()
            return (
                f"'{meal_name}' validated. {added_info} "
                f"All {state.target_count} meals are now planned: {state.planned_meals}. "
                "Meal planning complete! Use action='finish' to close the session."
            )
        remaining = state.target_count - len(state.planned_meals)
        return (
            f"'{meal_name}' validated. {added_info} "
            f"{len(state.planned_meals)}/{state.target_count} meals planned. "
            f"{remaining} more to go."
        )

    def _reject_meal(self, meal_name: str) -> str:
        state = MealPlanState.load()
        if state is None or not state.active:
            return "No active meal planning session. Use action='start' first."
        state.rejected_meals.append(meal_name)
        state.save()
        return f"'{meal_name}' rejected. Suggest another meal."

    def _finish(self) -> str:
        state = MealPlanState.load()
        if state is None:
            return "No meal planning session found."
        summary = (
            f"Meal planning session finished. "
            f"Planned meals ({len(state.planned_meals)}): {state.planned_meals}."
        )
        state.active = False
        state.save()
        return summary
