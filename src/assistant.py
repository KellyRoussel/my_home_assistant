import threading

from stt.recorder import Recorder
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
            self.keyboard_listener = KeyboardActionListener()
            self.keyboard_listener.set_press_callback(self._start_recording)
            self.keyboard_listener.set_release_callback(self._stop_recording)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")

    def _start_recording(self):
        try:
            print("Space pressed: starting recording.")
            # let's give a name to the output file with a timestamp to avoid overwriting
            output_filename = f"recording_{int(time.time())}.wav"
            self.recording_thread = threading.Thread(target=self.audio_recorder.record, args=(output_filename,))
            self.recording_thread.start()
        except Exception as e:
            raise Exception(f"_start_recording: {e}")

    def _stop_recording(self):
        try:
            print("Space released: stopping recording.")
            self.audio_recorder.stop_recording()
            if self.recording_thread:
                self.recording_thread.join()  # Ensure the recording thread has finished
                self.recording_thread = None
        except Exception as e:
            raise Exception(f"_stop_recording: {e}")

    def start(self):
        try:
            print("Assistant started. Listening for keyboard events...")
            self.keyboard_listener.start_listening()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : start: {e}")

