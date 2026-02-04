from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str

    def to_openai_message(self) -> dict:
        return {"role": self.role, "content": self.content}
