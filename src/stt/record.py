import wave
from logger import logger, ErrorMessage, AppMessage

class Record:


    def __init__(self, output_filename):
        try:
            self.output_filename = output_filename
            self.frames = []
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

    def get_duration(self, framerate):
        try:
            return len(self.frames) / framerate
        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : duration: {e}"))
            raise Exception(f"{self.__class__.__name__} : duration: {e}")
