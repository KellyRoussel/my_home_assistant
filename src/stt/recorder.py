import sounddevice as sd
import numpy as np
import time
from logger import logger, ErrorMessage, AppMessage
from stt.record import Record
import subprocess

class Recorder:

    # Audio configuration
    FORMAT = np.int16
    CHANNELS = 1
    RATE = 44100
    CHUNK = 1024
    SILENCE_THRESHOLD = 500
    MAX_SILENCE_DURATION = 5


    def __init__(self):
        try:
            self.running_record = None
            self.is_recording = False
            self.silence_frames=0
        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : __init__: {e}"))
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")

    @property
    def sample_size(self):
        return np.dtype(self.FORMAT).itemsize

    
    def notify(self):
        player_command = ["ffplay", "-nodisp", "-autoexit", "./listening.mp3"]

        # Start the process and wait for it to finish
        subprocess.run(player_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)



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
            self.notify()
            self.running_record.stream.start()
            self.silence_frames=0
            print("Recording started...")
            logger.log(AppMessage(content=f"{self.__class__.__name__}: Start recording"))
        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : start_recording: {e}"))
            raise Exception(f"start_recording: {e}")

    def callback(self, indata, frames, time, status):
        if status:
            print(status, flush=True)
        
        rms = np.sqrt(np.mean(indata ** 2))
        if rms < self.SILENCE_THRESHOLD:
            self.silence_frames += 1
        else:
            self.silence_frames = 0
        
        self.running_record.frames.append(indata.copy())

        if self.silence_frames >= (self.RATE / self.CHUNK) * self.MAX_SILENCE_DURATION:
            if self.is_recording:
                print("Silence detected, stopping recording...")
                self.is_recording = False
        

    def stop_recording(self):
        try:
            self.notify()
            self.running_record.stream.stop()
            self.running_record.stream.close()
            audio_duration = self.running_record.get_duration(self.RATE)
            if audio_duration < 0.001: # seconds
                print("Recording too short, skipping...")
                logger.log(AppMessage(content="Recording too short, skipping..."))
                return None
            self.running_record.save(self.CHANNELS, self.sample_size, self.RATE)
            return self.running_record
        except Exception as e:
            print("ERREUR")
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : stop_recording: {e}"))
            raise Exception(f"{self.__class__.__name__} : stop_recording: {e}")

    def reset_record(self):
        try:
            self.running_record = None
        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : reset_record: {e}"))
            raise Exception(f"{self.__class__.__name__} : reset_record: {e}")

    def record(self, output_filename: str):
        try:
            self.start_recording(output_filename)
            while self.is_recording:
                time.sleep(1)  # Adjust the sleep time as needed
            return self.stop_recording()
        except KeyboardInterrupt:
            self.stop_recording()
        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : record: {e}"))
            raise Exception(f"{self.__class__.__name__} : record: {e}")

    def terminate(self):
        sd.stop()
