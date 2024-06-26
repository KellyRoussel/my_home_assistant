from .message import Message
from ..tool_call import ToolCall


class AssistantMessage(Message):

    def __init__(self, content: str, tool_calls: list[ToolCall] = None):
        try:
            self._tool_calls = tool_calls if tool_calls is not None else []
            super().__init__("assistant", content)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")

    @property
    def tool_calls(self):
        return self._tool_calls

    def to_openai_message(self):
        try:
            base_message = super().to_openai_message()
            if self.tool_calls:
                base_message["tool_calls"] = [tool_call.to_openai_tool_call() for tool_call in self._tool_calls]
            return base_message
        except Exception as e:
            raise Exception(f"to_openai_message: {e}")
