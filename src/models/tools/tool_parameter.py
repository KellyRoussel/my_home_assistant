from typing import Optional
from pydantic import BaseModel


class ToolParameter(BaseModel):
    name: str
    description: str
    type: str
    required: bool = False
    enum: Optional[list[str]] = None

    @property
    def json_definition(self) -> dict:
        definition = {
            "description": self.description,
            "type": self.type
        }
        if self.enum:
            definition["enum"] = self.enum
        return definition
