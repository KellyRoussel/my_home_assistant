import json

from tools.tool import Tool
from tools.tools_library import tools


class ToolCall:
    def __init__(self, tool_call_id: str, function_name: str, arguments: dict):
        try:
            self._tool_call_id = tool_call_id
            self._function_name = function_name
            self._arguments = arguments
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")

    @property
    def tool_call_id(self):
        return self._tool_call_id

    @property
    def function_name(self):
        return self._function_name

    @property
    def arguments(self):
        return self._arguments

    def to_openai_tool_call(self):
        try:
            return {
                "id": self.tool_call_id,
                "type": "function",
                "function": {
                    "name": self.function_name,
                    "arguments": json.dumps(self.arguments)
                }
            }
        except Exception as e:
            raise Exception(f"to_openai_tool_call: {e}")

    @property
    def tool(self) -> Tool:
        try:
            return tools[self.function_name]
        except Exception as e:
            raise Exception(f"tool: {e}")

    @property
    def result(self):
        return self.tool.execute(**self.arguments)
