from .entities.todo_list import TodoList
from .todo_tool import TodoTool
from ..tool_parameter import ToolParameter


class AddTodoItemToList(TodoTool):

    @property
    def tool_name(self) -> str:
        return "add_todo_item_to_list"

    @property
    def description(self) -> str:
        return "Add an item to a todo list"

    @property
    def parameters(self) -> list[ToolParameter]:
        return [ToolParameter("list_name", "The name of the list", "string", required=True, enum=['shopping']),
                ToolParameter("item_name", "The name of the item", "string", required=True)]

    def execute(self, list_name: str, item_name: str):
        try:
            todo_list: TodoList = self._get_todo_list_from_name(list_name)
            return todo_list.add_item(self._get_access_token(), item_name)

        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : get_todo_list_items: {e}")
