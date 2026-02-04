from .message import Message


class ToolMessage(Message):
    role: str = "tool"
    tool_call_id: str
    name: str

    def to_openai_message(self) -> dict:
        base = super().to_openai_message()
        base["tool_call_id"] = self.tool_call_id
        base["name"] = self.name
        return base
