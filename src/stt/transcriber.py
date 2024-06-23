import time

from openai import OpenAI
import whisper
class Transcriber:

    def __init__(self):
        try:
            self.client = OpenAI()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")

    def transcribe_online(self, audio_filename: str):
        try:
            start_time = time.time()
            audio_file = open(audio_filename, "rb")
            transcription = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            print(f"Transcription took {(time.time() - start_time)*1000} ms")
            return transcription.text

        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :transcribe_online: {e}")

    def transcribe_local(self, audio_filename: str):
        try:
            model = whisper.load_model("small")
            result = model.transcribe(audio_filename, fp16=False)

            return result["text"]

        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :transcribe_local: {e}")
