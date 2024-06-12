import threading

from session import AssistantContext, AssistantState
from llm_engine.llm_engine import LLMEngine
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
            self.llm_engine = LLMEngine()
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
                print(f"Transcription: {transcription}")
                self.context.running_conversation.new_user_message(transcription)
                self._think()
        except Exception as e:
            raise Exception(f"_stop_recording: {e}")

    def _think(self):
        try:
            self.state = AssistantState.THINKING
            response = self.llm_engine.gpt_call(self.context.running_conversation)
            self.context.running_conversation.new_assistant_message(response)
            self._speak(response)
        except Exception as e:
            raise Exception(f"_start_thinking: {e}")

    def _speak(self, response):
        try:
            self.state = AssistantState.SPEAKING
            print(response)
            self.state = AssistantState.IDLE
        except Exception as e:
            raise Exception(f"_start_speaking: {e}")

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