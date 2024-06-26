from abc import ABC, abstractmethod

from tools.tool_parameter import ToolParameter


class Tool(ABC):

    @property
    @abstractmethod
    def tool_name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def parameters(self) -> list[ToolParameter]:
        raise NotImplementedError

    @property
    def json_definition(self):
        return {
            "type": "function",
            "function": {
                "name": self.tool_name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties":
                        {p.name: p.json_definition for p in self.parameters},
                    "required": [p.name for p in self.parameters]
                }
            }
        }

    @abstractmethod
    def execute(self, **kwargs):
        raise NotImplementedError
