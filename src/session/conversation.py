import json
from datetime import datetime
import os
from jinja2 import Template

from models.messages import (
    Message,
    UserMessage,
    AssistantMessage,
    SystemMessage,
    ToolMessage,
)
from models.tools import ToolCall
from logger import logger, ErrorMessage, ConversationMessage


class Conversation:
    def __init__(self, messages: list[Message] = None):
        try:
            self.messages = messages if messages is not None else [SystemMessage(content=self._get_prompt())]
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")

    @property
    def prompt_template(self):
        return Template("""Your name is JARVIS. You are the best AI home assistant ever. You are very nice, enthusiastic, cool, and helpful.
    You are Kelly's digital AI assistant.
    Kelly is a {{age}}-year-old woman. She is an AI engineer passionate about her job, loves programming, and enjoys startup success stories.
    She lives with her boyfriend {{boyfriend_name}} in {{city}}, France, and adores the city.
    Kelly strives for an eco-friendly lifestyle, delights in music, cooking, dancing, and wine.
    She also loves sports, running weekly (schedule permitting) and going to the gym on Tuesday evenings.
    Kelly treasures spending time with her family and friends, scattered across France with her family in {{family_city}}. Consequently, she often spends weekends out of the city.

    When Kelly asks you something, do your best to help her.
    Always be fun and empathetic.
    """)

    def _get_prompt(self):
        try:
            prompt = self.prompt_template.render(
                age=os.environ['age'],
                boyfriend_name=os.environ['boyfriend_name'],
                city=os.environ['city'],
                family_city=os.environ['family_city']
            )
            return prompt
        except Exception as e:
            logger.log(ErrorMessage(content=f"_get_prompt: {e}"))
            raise Exception(f"_get_prompt: {e}")

    def _new_message(self, message: Message):
        try:
            self.messages.append(message)
        except Exception as e:
            raise Exception(f"_new_message: {e}")

    def _internal_system_message_content(self):
        return f"Now datetime is: {datetime.now()}."

    def new_user_message(self, content: str):
        try:
            system_message_content = self._internal_system_message_content()
            self._new_message(SystemMessage(content=system_message_content))
            logger.log(ConversationMessage(role='system', content=system_message_content))
            self._new_message(UserMessage(content=content))
            logger.log(ConversationMessage(role='user', content=content))
        except Exception as e:
            raise Exception(f"new_user_message: {e}")

    def new_assistant_message(self, content: str, tool_calls: list[ToolCall] = None):
        try:
            if content:
                content = content.encode("utf-8").decode("utf-8")
            self._new_message(AssistantMessage(content=content or "", tool_calls=tool_calls or []))
            if tool_calls:
                json_tool_calls = [f"Calling tool {tool_call.function_name} with args: {tool_call.arguments}" for tool_call in tool_calls]
                logger.log(ConversationMessage(role='tool', content=json.dumps(json_tool_calls, indent=4)))
            else:
                logger.log(ConversationMessage(role='assistant', content=content))
        except Exception as e:
            raise Exception(f"new_assistant_message: {e}")

    def new_tool_message(self, tool_call: ToolCall):
        try:
            result = self._execute_tool_call(tool_call)
            message = ToolMessage(
                tool_call_id=tool_call.tool_call_id,
                name=tool_call.function_name,
                content=result
            )
            logger.log(ConversationMessage(role='tool', content=result))
            self._new_message(message)
        except Exception as e:
            raise Exception(f"new_tool_message: {e}")

    def _execute_tool_call(self, tool_call: ToolCall) -> str:
        from tools.tools_library import tools
        tool = tools[tool_call.function_name]
        return tool.execute(**tool_call.arguments)

    def to_openai_conversation(self):
        try:
            return [message.to_openai_message() for message in self.messages]
        except Exception as e:
            raise Exception(f"to_openai_conversation: {e}")
