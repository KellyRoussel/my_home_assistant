import json
from config import Config
from models.logs import LogMessage, AppMessage, ErrorMessage, ConversationMessage

# Re-export for backwards compatibility
__all__ = ["Logger", "logger", "LogMessage", "AppMessage", "ErrorMessage", "ConversationMessage"]


class Logger:

    def __init__(self, log_file: str = None):
        self._log_file = str(log_file or Config.LOGS_FILE)

    def get_json_file(self) -> list:
        try:
            with open(self._log_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def log(self, message: LogMessage):
        logs = self.get_json_file()
        logs.append(message.model_dump())

        with open(self._log_file, 'w') as f:
            json.dump(logs, f, indent=4)

    def reset(self):
        with open(self._log_file, 'w') as f:
            json.dump([], f)


logger = Logger()
