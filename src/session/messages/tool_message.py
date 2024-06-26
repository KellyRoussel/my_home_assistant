from .message import Message


class ToolMessage(Message):

    def __init__(self, tool_call_id: str, name: str, content: str):
        try:
            self._tool_call_id = tool_call_id
            self._name = name
            super().__init__("tool", content)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")

    @property
    def tool_call_id(self):
        return self._tool_call_id

    @property
    def name(self):
        return self._name

    def to_openai_message(self):
        try:
            base_message = super().to_openai_message()
            base_message["tool_call_id"] = self._tool_call_id
            base_message["name"] = self._name
            return base_message
        except Exception as e:
            raise Exception(f"to_openai_message: {e}")
