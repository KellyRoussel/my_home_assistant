from typing import Optional
from .message import Message
from models.tools import ToolCall


class AssistantMessage(Message):
    role: str = "assistant"
    tool_calls: list[ToolCall] = []

    def to_openai_message(self) -> dict:
        base = super().to_openai_message()
        if self.tool_calls:
            base["tool_calls"] = [tc.to_openai_tool_call() for tc in self.tool_calls]
        return base
