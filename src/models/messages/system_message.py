from .message import Message


class SystemMessage(Message):
    role: str = "system"
