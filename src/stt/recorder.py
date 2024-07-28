import sounddevice as sd
import numpy as np
import time

from stt.record import Record


class Recorder:

    # Audio configuration
    FORMAT = np.int16
    CHANNELS = 2
    RATE = 44100
    CHUNK = 1024

    def __init__(self):
        try:
            self.running_record = None
            self.is_recording = False
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")

    @property
    def sample_size(self):
        return np.dtype(self.FORMAT).itemsize

    def start_recording(self, output_filename: str):
        try:
            self.is_recording = True
            self.running_record = Record(output_filename)
            self.running_record.stream = sd.InputStream(
                samplerate=self.RATE,
                channels=self.CHANNELS,
                dtype=self.FORMAT,
                callback=self.callback
            )
            self.running_record.stream.start()
            print("Recording started...")
        except Exception as e:
            raise Exception(f"start_recording: {e}")

    def callback(self, indata, frames, time, status):
        if status:
            print(status, flush=True)
        self.running_record.frames.append(indata.copy())

    def stop_recording(self):
        try:
            self.is_recording = False
            self.running_record.stream.stop()
            self.running_record.stream.close()
            self.running_record.save(self.CHANNELS, self.sample_size, self.RATE)
            return self.running_record
        except Exception as e:
            raise Exception(f"stop_recording: {e}")

    def reset_record(self):
        try:
            self.running_record = None
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : reset_record: {e}")

    def record(self, output_filename: str):
        try:
            self.start_recording(output_filename)
            while self.is_recording:
                time.sleep(1)  # Adjust the sleep time as needed
        except KeyboardInterrupt:
            self.stop_recording()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : record: {e}")

    def terminate(self):
        sd.stop()
        sd.terminate()
