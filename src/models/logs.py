from datetime import datetime
from pydantic import BaseModel, Field


class LogMessage(BaseModel):
    role: str
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class AppMessage(LogMessage):
    role: str = "app"


class ErrorMessage(LogMessage):
    role: str = "error"


class ConversationMessage(LogMessage):
    pass
