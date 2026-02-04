from pydantic import BaseModel


class TodoListModel(BaseModel):
    id: str
    display_name: str
    is_owner: bool
    is_shared: bool

    @classmethod
    def from_api_response(cls, data: dict) -> "TodoListModel":
        return cls(
            id=data["id"],
            display_name=data["displayName"],
            is_owner=data["isOwner"],
            is_shared=data["isShared"],
        )

    @property
    def tasks_url(self) -> str:
        return f"https://graph.microsoft.com/v1.0/me/todo/lists/{self.id}/tasks"
