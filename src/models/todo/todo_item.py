from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class TodoItem(BaseModel):
    id: str
    title: str
    importance: str
    is_reminder_on: bool
    status: str
    created_date_time: datetime
    last_modified_date_time: datetime
    has_attachments: bool
    categories: list[str]

    @classmethod
    def from_api_response(cls, data: dict) -> "TodoItem":
        return cls(
            id=data["id"],
            title=data["title"],
            importance=data["importance"],
            is_reminder_on=data["isReminderOn"],
            status=data["status"],
            created_date_time=datetime.fromisoformat(data["createdDateTime"].replace("Z", "+00:00")),
            last_modified_date_time=datetime.fromisoformat(data["lastModifiedDateTime"].replace("Z", "+00:00")),
            has_attachments=data["hasAttachments"],
            categories=data["categories"],
        )

    def __str__(self) -> str:
        return self.title
