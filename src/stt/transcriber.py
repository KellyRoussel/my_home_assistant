from openai import OpenAI
import whisper
from logger import logger, ErrorMessage
class Transcriber:

    def __init__(self):
        try:
            self.client = OpenAI()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")

    def transcribe_online(self, audio_filename: str):
        try:
            audio_file = open(audio_filename, "rb")
            transcription = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            return transcription.text

        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} :transcribe_online: {e}"))
            raise Exception(f"{self.__class__.__name__} :transcribe_online: {e}")

    def transcribe_local(self, audio_filename: str):
        try:
            model = whisper.load_model("small")
            result = model.transcribe(audio_filename, fp16=False)

            return result["text"]

        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} :transcribe_local: {e}"))
            raise Exception(f"{self.__class__.__name__} :transcribe_local: {e}")