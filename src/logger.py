import datetime
from pydantic import BaseModel
import json
from datetime import datetime

class Message(BaseModel):
    role: str
    content: str
    timestamp: str = datetime.now().isoformat()

class AppMessage(Message):
    role: str = "app"

class ErrorMessage(Message):
    role: str = "error"

class ConversationMessage(Message):
    ...

class Logger:

    def get_json_file(self) -> list:
        try:
            with open('./logs.json', 'r') as f:
                return json.load(f)
        except:
            return []

    def log(self, message: Message):
        logs = self.get_json_file()

        # add message to logs
        logs.append(message.model_dump())

        # save logs.json
        with open('./logs.json', 'w') as f:
            json.dump(logs, f, indent=4)

    def reset(self):
        with open('./logs.json', 'w') as f:
            json.dump([], f)

logger = Logger()