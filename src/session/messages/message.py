from abc import ABC


class Message(ABC):
    def __init__(self, role: str, content: str):
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
