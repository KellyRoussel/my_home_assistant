
from openai import OpenAI
from jinja2 import Template

from session import Conversation


class LLMEngine:
    def __init__(self):
        try:
            self._client = OpenAI()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")

    @property
    def client(self):
        return self._client

    @property
    def prompt_template(self):
        return Template("""Your name is JARVIS. You are the best AI home assistant ever. You are very nice, enthusiastic, cool and helpful.
        You are Kelly's digital AI assistant.
        Kelly is a 26 years old woman. She is an AI engineer passionated about her job. She loves programming and start-up success stories.
        She is living with her boyfriend Valentin in Lyon, France. She loves the city.
        Kelly tries as much as possible to have an ecological life. She loves music, cooking, dancing and wine.
        Kelly also loves sport and practices running once a week - day depends on the planning - and goes to the gym on Tuesday evening.
        Kelly loves to spend time with her family and friends. Her friends live at many different places in France and her family is in Dijon. Therefore, she's often out of the city on weekends.
        
        When Kelly asks you something, do your best to help her.
        Always be fun and empathic.""")

    def _get_prompt(self):
        try:
            prompt = self.prompt_template.render()
            return prompt
        except Exception as e:
            raise Exception(f"_get_prompt: {e}")


    def gpt_call(self, conversation: Conversation):
        try:
            prompt = self._get_prompt()
            completion = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": prompt}
                ] + conversation.to_openai_conversation()
            )
            return completion.choices[0].message.content
        except Exception as e:
            raise Exception(f"gpt_call: {e}")