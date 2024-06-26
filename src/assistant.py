import json
import os
import threading

from session.assistant_context import AssistantContext, AssistantState
from llm_engine.llm_engine import LLMEngine
from session.tool_call import ToolCall
from tools.tools_library import tools
from tts.speaker import Speaker
from stt.recorder import Recorder
from stt.transcriber import Transcriber
from actions_listener.keyboard_actions_listener import KeyboardActionListener
import time

class Assistant:
    """The role of the assistant class is to coordinate the capacities of the home assistant.
    For now:
    - detect when the space bar is pressed
    - record audio
    """

    def __init__(self):
        try:
            self.audio_recorder = Recorder()
            self.transcriber = Transcriber()
            self.keyboard_listener = KeyboardActionListener()
            self.llm_engine = LLMEngine(tools=tools.values())
            self.speaker = Speaker()
            self.keyboard_listener.set_press_callback(self._start_recording)
            self.keyboard_listener.set_release_callback(self._stop_recording)
            self.context = AssistantContext()
            self.state = AssistantState.OFF
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")

    def _start_recording(self):
        try:
            if self.state != AssistantState.IDLE:
                return
            self.state = AssistantState.RECORDING
            print("Space pressed: starting recording.")
            # let's give a name to the output file with a timestamp to avoid overwriting
            output_filename = f"recording_{int(time.time())}.wav"
            self.recording_thread = threading.Thread(target=self.audio_recorder.record, args=(output_filename,))
            self.recording_thread.start()
        except Exception as e:
            raise Exception(f"_start_recording: {e}")

    def _stop_recording(self):
        try:
            start_time = time.time()
            if self.state != AssistantState.RECORDING:
                return
            print("Space released: stopping recording.")
            ended_record = self.audio_recorder.stop_recording()
            record_filename = ended_record.output_filename
            print(f"Recording saved to {record_filename}")
            self.audio_recorder.reset_record()
            if self.recording_thread:
                self.recording_thread.join()  # Ensure the recording thread has finished
                self.recording_thread = None
                print("Recording stopped.")
                self.state = AssistantState.TRANSCRIBING
                transcription = self.transcriber.transcribe_online(record_filename)
                # delete the recording file
               # os.remove(record_filename)
                print(f"Transcription: {transcription}")
                self.context.running_conversation.new_user_message(transcription)
                self._think()
            end_time = time.time()
            print(f"Time elapsed: {(end_time - start_time)*1000} ms")
        except Exception as e:
            raise Exception(f"_stop_recording: {e}")

    def _think(self):
        try:
            self.state = AssistantState.THINKING
            response = self.llm_engine.gpt_call(self.context.running_conversation)
            tool_calls_response = response.tool_calls
            # Check if the model wanted to call a function
            if tool_calls_response:
                tool_calls = [ToolCall(tool_call.id, tool_call.function.name, json.loads(tool_call.function.arguments)) for tool_call in tool_calls_response]
                self.context.running_conversation.new_assistant_message(response.content, tool_calls)
                self._call_tools(tool_calls)
                self._think()
            else:
                response_message = response.content
                self.context.running_conversation.new_assistant_message(response_message)
                self._speak(response_message)
        except Exception as e:
            raise Exception(f"_think: {e}")

    def _call_tools(self, tool_calls: list[ToolCall]):
        try:
            # Send the info for each function call and function response to the model
            for tool_call in tool_calls:
                self.context.running_conversation.new_tool_message(
                    tool_call
                )
        except Exception as e:
            raise Exception(f"_call_tools: {e}")

    def _speak(self, response):
        try:
            self.state = AssistantState.SPEAKING
            print(response)
            self.speaker.speak(response)
            print("Assistant done speaking.")
            self.state = AssistantState.IDLE
        except Exception as e:
            raise Exception(f"_speak: {e}")

    def start(self):
        try:
            self.state = AssistantState.IDLE
            print("Assistant started. Listening for keyboard events...")
            self.keyboard_listener.start_listening()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : start: {e}")

    def stop(self):
        try:
            self.audio_recorder.terminate()
            self.state = AssistantState.OFF
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : stop: {e}")