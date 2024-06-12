import pyaudio
import time
from stt.record import Record


class Recorder:

    # Audio configuration
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 44100
    CHUNK = 1024

    def __init__(self):
        try:
            # Initialize PyAudio
            self._audio = pyaudio.PyAudio()
            self.running_record = None
            self.is_recording = False
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")

    @property
    def sample_size(self):
        return self._audio.get_sample_size(self.FORMAT)

    def start_recording(self, output_filename: str):
        try:
            self.is_recording = True
            self.running_record = Record(output_filename)
            self.running_record.stream = self._audio.open(format=self.FORMAT,
                                          channels=self.CHANNELS,
                                          rate=self.RATE,
                                          input=True,
                                          frames_per_buffer=self.CHUNK)
            print("Recording started...")
        except Exception as e:
            raise Exception(f"start_recording: {e}")

    def stop_recording(self):
        try:
            self.is_recording = False
            self.running_record.stream.stop_stream()
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
            start_time = time.time()
            last_minute = 0

            try:
                while self.is_recording:
                    data = self.running_record.stream.read(self.CHUNK)
                    self.running_record.frames.append(data)
                    elapsed_time = time.time() - start_time
                    minutes_elapsed = int(elapsed_time // 60)
                    if minutes_elapsed > last_minute:
                        last_minute = minutes_elapsed
                        print(f" {minutes_elapsed} minute(s)")
            except KeyboardInterrupt:
                self.stop_recording()


        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : record: {e}")

    def terminate(self):
        self._audio.terminate()
