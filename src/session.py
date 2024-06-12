# enum AssistantState { OFF, IDLE, RECORDING, TRANSCRIBING, SPEAKING }
from enum import Enum
AssistantState = Enum('AssistantState', ['OFF', 'IDLE', 'RECORDING', 'TRANSCRIBING', 'SPEAKING', 'THINKING'])

class AssistantContext:
    def __init__(self):
        try:
            self._conversation_history = []
            self._running_conversation = Conversation()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")

    @property
    def conversation_history(self):
        return self._conversation_history

    @property
    def running_conversation(self):
        return self._running_conversation

class Conversation:
    def __init__(self, messages=None):
        if messages is None:
            messages = []
        try:
            self.messages = messages
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")

    def _new_message(self, role, content):
        try:
            message = Message(role, content)
            self.messages.append(message)
        except Exception as e:
            raise Exception(f"_new_message: {e}")

    def new_user_message(self, content):
        try:
            self._new_message("user", content)
        except Exception as e:
            raise Exception(f"new_user_message: {e}")

    def new_assistant_message(self, content):
        try:
            self._new_message("assistant", content)
        except Exception as e:
            raise Exception(f"new_assistant_message: {e}")

    def to_openai_conversation(self):
        try:
            return [message.to_openai_message() for message in self.messages]
        except Exception as e:
            raise Exception(f"to_openai_conversation: {e}")


class Message:
    def __init__(self, role, content):
        try:
            self._role = role
            self._content = content
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")

    @property
    def role(self):
        return self._role

    @property
    def content(self):
        return self._content

    def to_openai_message(self):
        try:
            return {"role": self._role, "content": self._content}
        except Exception as e:
            raise Exception(f"to_openai_message: {e}")