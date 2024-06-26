from .messages.assistant_message import AssistantMessage
from .messages.tool_message import ToolMessage
from .messages.user_message import UserMessage
from .messages.message import Message
from .tool_call import ToolCall


class Conversation:
    def __init__(self, messages: list[Message]=None):
        try:
            self.messages = messages if messages is not None else []
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")

    def _new_message(self, message: Message):
        try:
            self.messages.append(message)
        except Exception as e:
            raise Exception(f"_new_message: {e}")

    def new_user_message(self, content: str):
        try:
            self._new_message(UserMessage(content))
        except Exception as e:
            raise Exception(f"new_user_message: {e}")

    def new_assistant_message(self, content: str, tool_calls: list[ToolCall] = None):
        try:
            self._new_message(AssistantMessage(content, tool_calls))
        except Exception as e:
            raise Exception(f"new_assistant_message: {e}")

    def new_tool_message(self, tool_call: ToolCall):
        try:
            message = ToolMessage(tool_call.tool_call_id, tool_call.function_name, tool_call.result)
            self._new_message(message)
        except Exception as e:
            raise Exception(f"new_tool_message: {e}")

    def to_openai_conversation(self):
        try:
            return [message.to_openai_message() for message in self.messages]
        except Exception as e:
            raise Exception(f"to_openai_conversation: {e}")
