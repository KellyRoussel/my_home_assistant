import os
from openai import OpenAI
from jinja2 import Template
from session.assistant_context import Conversation
from tools.tool import Tool
from groq import Groq

class LLMEngine:
    def __init__(self, tools: list[Tool] = None):
        try:
            #self._client = OpenAI()
            #self._model = "gpt-4o"
            self._client = Groq()
            self._model = "llama3-70b-8192"
            self.tools = tools if tools is not None else []
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")

    @property
    def client(self):
        return self._client

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
            prompt = self.prompt_template.render(age=os.environ['age'],
                                                 boyfriend_name=os.environ['boyfriend_name'],
                                                 city=os.environ['city'],
                                                 family_city=os.environ['family_city'])
            return prompt
        except Exception as e:
            raise Exception(f"_get_prompt: {e}")

    def gpt_call(self, conversation: Conversation):
        try:
            prompt = self._get_prompt()
            response = self.client.chat.completions.create(
                model=self._model,
                messages=[
                             {"role": "system", "content": prompt}
                         ] + conversation.to_openai_conversation(),
                tools=[tool.json_definition for tool in self.tools]
            )
            response_message = response.choices[0].message
            return response_message
        except Exception as e:
            raise Exception(f"gpt_call: {e}")
