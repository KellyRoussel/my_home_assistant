from models.tools import ToolParameter
from tools.todo_list.todo_tool import TodoTool
from logger import logger, ErrorMessage


class GetMealsList(TodoTool):

    @property
    def tool_name(self) -> str:
        return "get_meals_list"

    @property
    def description(self) -> str:
        return (
            "Retrieve all meals from the 'Meals' Microsoft To Do list. "
            "Each meal includes its name and list of ingredients (checklist items). "
            "Use this to get meal candidates before suggesting options to the user."
        )

    @property
    def parameters(self) -> list[ToolParameter]:
        return []

    def execute(self) -> str:
        try:
            token = self._get_access_token()
            meals_list = self._get_todo_list_from_name("meals")
            meals = meals_list.get_items_with_checklist(token)
            if not meals:
                return "The Meals list is empty."
            lines = []
            for meal in meals:
                ingredients = ", ".join(meal["ingredients"]) if meal["ingredients"] else "no ingredients listed"
                note = f" (recipe: {meal['note']})" if meal["note"] else ""
                lines.append(f"- {meal['title']}: {ingredients}{note}")
            return "Available meals:\n" + "\n".join(lines)
        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : execute: {e}"))
            raise Exception(f"{self.__class__.__name__} : execute: {e}")
