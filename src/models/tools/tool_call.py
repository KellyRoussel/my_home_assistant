from typing import Any
import json
from pydantic import BaseModel


class ToolCall(BaseModel):
    tool_call_id: str
    function_name: str
    arguments: dict[str, Any]

    def to_openai_tool_call(self) -> dict:
        return {
            "id": self.tool_call_id,
            "type": "function",
            "function": {
                "name": self.function_name,
                "arguments": json.dumps(self.arguments)
            }
        }

    @property
    def tool(self):
        from tools.tools_library import tools
        return tools[self.function_name]

    @property
    def result(self) -> str:
        return self.tool.execute(**self.arguments)
