from .message import Message


class UserMessage(Message):

    def __init__(self, content: str):
        try:
            super().__init__("user", content)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")
