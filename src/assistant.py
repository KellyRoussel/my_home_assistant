import subprocess

from config import Config
from llm_engine.real_time_engine import RealTimeEngine
from logger import logger, AppMessage, ErrorMessage
from session.assistant_context import AssistantContext, AssistantState
from tools.tools_library import tools
from actions_listener.wake_word_listener import WakeWordListener


class Assistant:
    """Coordinates the home assistant capabilities: wake word detection, recording, and response."""

    def __init__(self):
        try:
            self.action_listener = WakeWordListener()
            self.real_time_engine = RealTimeEngine(tools=tools.values())
            self.action_listener.set_detection_callback(self._real_time_listening)
            self.context = AssistantContext()
            self.state = AssistantState.OFF
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")

    def notify_sound(self):
        player_command = ["ffplay", "-nodisp", "-autoexit", str(Config.NOTIFICATION_SOUND)]
        subprocess.run(player_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    async def _real_time_listening(self):
        try:
            self.action_listener.pause()
            self.state = AssistantState.THINKING
            await self.real_time_engine.start(
                on_user_transcript=self.context.running_conversation.new_user_message,
                on_assistant_transcript=lambda text: self.context.running_conversation.new_assistant_message(
                    text.encode("latin-1", errors="ignore").decode("latin-1")
                ),
            )
            print("Done")
        except Exception as e:
            logger.log(ErrorMessage(content=f"_real_time_listening: {e}"))
        finally:
            self.state = AssistantState.IDLE
            self.action_listener.resume()


    async def start(self):
        try:
            self.state = AssistantState.IDLE
            print("Assistant started. Listening for wakeword...")
            logger.log(AppMessage(content="Start listening for wakeword"))
            await self.action_listener.start_listening()
        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : start: {e}"))
            raise Exception(f"{self.__class__.__name__} : start: {e}")

    def stop(self):
        try:
            self.action_listener.stop_listening()
            self.state = AssistantState.OFF
        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : stop: {e}"))
            raise Exception(f"{self.__class__.__name__} : stop: {e}")
