from enum import Enum
from .conversation import Conversation

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




