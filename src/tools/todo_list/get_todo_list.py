from .entities.items import TodoItem
from .entities.todo_list import TodoList
from .todo_tool import TodoTool
from ..tool_parameter import ToolParameter


class GetTodoListTool(TodoTool):

    @property
    def tool_name(self) -> str:
        return "get_todo_list_items"

    @property
    def description(self) -> str:
        return "Get Todo List Items from its name"

    @property
    def parameters(self) -> list[ToolParameter]:
        return [ToolParameter("list_name", "The name of the list", "string", required=True, enum=['courses'])]

    def execute(self, name: str) -> list[TodoItem]:
        try:
            todo_list: TodoList = self._get_todo_list_from_name(name)
            return todo_list.get_items(self._get_access_token())
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : get_todo_list_items: {e}")

