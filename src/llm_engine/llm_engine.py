import os
from openai import OpenAI
from session.assistant_context import Conversation
from tools.tool import Tool
from logger import logger, ErrorMessage


class LLMEngine:
    def __init__(self, tools: list[Tool] = None):
        try:
            self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self._model = "gpt-4o"
            self.tools = tools if tools is not None else []
        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : __init__: {e}"))
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")

    @property
    def client(self):
        return self._client

    def gpt_call(self, conversation: Conversation):
        try:
            response = self.client.chat.completions.create(
                model=self._model,
                messages=conversation.to_openai_conversation(),
                tools=[tool.json_definition for tool in self.tools]
            )
            response_message = response.choices[0].message
            return response_message
        except Exception as e:
            logger.log(ErrorMessage(content=f"gpt_call: {e}"))
            raise Exception(f"gpt_call: {e}")
