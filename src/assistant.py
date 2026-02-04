import asyncio
import json
import os
import subprocess
import time

from config import Config
from llm_engine.real_time_engine import RealTimeEngine
from llm_engine.llm_engine import LLMEngine
from logger import logger, AppMessage, ErrorMessage
from models.tools import ToolCall
from session.assistant_context import AssistantContext, AssistantState
from tools.tools_library import tools
from tts.openai_speaker import OpenaiSpeaker
from stt.recorder import Recorder
from stt.transcriber import Transcriber
from actions_listener.wake_word_listener import WakeWordListener


class Assistant:
    """Coordinates the home assistant capabilities: wake word detection, recording, and response."""

    def __init__(self):
        try:
            self.audio_recorder = Recorder()
            self.transcriber = Transcriber()
            self.action_listener = WakeWordListener()
            self.llm_engine = LLMEngine(tools=tools.values())
            self.real_time_engine = RealTimeEngine(tools=tools.values())
            self.enable_real_time = True
            self.speaker = OpenaiSpeaker()
            if self.enable_real_time:
                self.action_listener.set_detection_callback(self._real_time_listening)
            else:
                self.action_listener.set_detection_callback(self._start_recording)
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
            response = await self.real_time_engine.start()
            if response:
                sanitized_text = response.encode("latin-1", errors="ignore").decode('latin-1')
                self.context.running_conversation.new_assistant_message(sanitized_text)
            print("Done")
        except Exception as e:
            logger.log(ErrorMessage(content=f"_real_time_listening: {e}"))
        finally:
            self.state = AssistantState.IDLE
            self.action_listener.resume()

    async def _start_recording(self):
        try:
            self.action_listener.pause()

            if self.state != AssistantState.IDLE:
                return
            self.state = AssistantState.RECORDING
            print("Space pressed: starting recording.")
            logger.log(AppMessage(content="Start recording"))
            output_filename = f"recording_{int(time.time())}.wav"

            ended_record = self.audio_recorder.record(output_filename)
            print(f"ended_record: {ended_record}")

            if self.enable_real_time:
                self.state = AssistantState.THINKING
                response = await self.real_time_engine.start(ended_record)
                sanitized_text = response.encode("latin-1", errors="ignore").decode('latin-1')
                self.context.running_conversation.new_assistant_message(sanitized_text)
                print("Done")
                self.state = AssistantState.IDLE
                self.action_listener.resume()
            else:
                self._stop_recording(ended_record)
        except Exception as e:
            logger.log(ErrorMessage(content=f"_start_recording: {e}"))
            raise Exception(f"_start_recording: {e}")

    def _stop_recording(self, ended_record):
        try:
            if self.state != AssistantState.RECORDING:
                return
            print("Space released: stopping recording.")
            logger.log(AppMessage(content="Stop recording"))
            if ended_record is None:
                self.state = AssistantState.IDLE
                self.action_listener.resume()
                return
            record_filename = ended_record.output_filename
            self.audio_recorder.reset_record()
            print("Recording stopped.")
            try:
                self.state = AssistantState.TRANSCRIBING
                transcription = self.transcriber.transcribe_online(record_filename)
                os.remove(record_filename)
                print(f"Transcription: {transcription}")
                self.context.running_conversation.new_user_message(transcription)
                self._think()
            except Exception as e:
                logger.log(ErrorMessage(content=f"_stop_recording - skipping : {e}"))
            self.action_listener.resume()
        except Exception as e:
            logger.log(ErrorMessage(content=f"_stop_recording: {e}"))
            raise Exception(f"_stop_recording: {e}")

    def _think(self):
        try:
            self.state = AssistantState.THINKING
            response = self.llm_engine.gpt_call(self.context.running_conversation)
            tool_calls_response = response.tool_calls
            if tool_calls_response:
                tool_calls = [
                    ToolCall(
                        tool_call_id=tool_call.id,
                        function_name=tool_call.function.name,
                        arguments=json.loads(tool_call.function.arguments)
                    )
                    for tool_call in tool_calls_response
                ]
                self.context.running_conversation.new_assistant_message(response.content, tool_calls)
                self._call_tools(tool_calls)
                self._think()
            else:
                response_message = response.content
                sanitized_text = response_message.encode("latin-1", errors="ignore").decode('latin-1')
                self.context.running_conversation.new_assistant_message(sanitized_text)
                self._speak(sanitized_text)
        except Exception as e:
            logger.log(ErrorMessage(content=f"_think: {e}"))
            raise Exception(f"_think: {e}")

    def _call_tools(self, tool_calls: list[ToolCall]):
        try:
            for tool_call in tool_calls:
                self.context.running_conversation.new_tool_message(tool_call)
        except Exception as e:
            logger.log(ErrorMessage(content=f"_call_tools: {e}"))
            raise Exception(f"_call_tools: {e}")

    def _speak(self, response):
        try:
            self.state = AssistantState.SPEAKING
            print(response)
            self.speaker.speak(response)
            self.state = AssistantState.IDLE
        except Exception as e:
            logger.log(ErrorMessage(content=f"_speak: {e}"))
            raise Exception(f"_speak: {e}")

    async def start(self):
        try:
            self.state = AssistantState.IDLE
            print("Assistant started. Listening for keyboard events...")
            logger.log(AppMessage(content="Start listening for events"))
            await self.action_listener.start_listening()
        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : start: {e}"))
            raise Exception(f"{self.__class__.__name__} : start: {e}")

    def stop(self):
        try:
            self.action_listener.stop_listening()
            self.audio_recorder.terminate()
            self.state = AssistantState.OFF
        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : stop: {e}"))
            raise Exception(f"{self.__class__.__name__} : stop: {e}")
