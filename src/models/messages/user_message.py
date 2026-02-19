from .message import Message


class UserMessage(Message):
    role: str = "user"
