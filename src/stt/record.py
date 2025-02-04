import base64
import wave

import numpy as np
from logger import logger, ErrorMessage, AppMessage

class Record:


    def __init__(self, output_filename, format):
        try:
            self.output_filename = output_filename
            self.frames = []
            self.format = format
            self.stream = None
        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : __init__: {e}"))
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")


    def save(self, channels, sample_width, framerate):
        try:
            with wave.open(self.output_filename, 'wb') as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(sample_width)
                wf.setframerate(framerate)
                wf.writeframes(b''.join(self.frames))
            print(f"Audio saved to {self.output_filename}")
            logger.log(AppMessage(content=f"Audio saved to {self.output_filename}"))
        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : save: {e}"))
            raise Exception(f"{self.__class__.__name__} : save: {e}")
        
    def get_base64_raw_bytes(self):
        try:
            # Convert recorded frames to raw bytes
            raw_audio_data = np.concatenate(self.frames, axis=0).astype(self.format).tobytes()

            # Encode to Base64
            base64_audio = base64.b64encode(raw_audio_data).decode('utf-8')
            return base64_audio
        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : get_base64_raw_bytes: {e}"))
            raise Exception(f"{self.__class__.__name__} : get_base64_raw")

    def get_duration(self, framerate):
        try:
            return len(self.frames) / framerate
        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : duration: {e}"))
            raise Exception(f"{self.__class__.__name__} : duration: {e}")
