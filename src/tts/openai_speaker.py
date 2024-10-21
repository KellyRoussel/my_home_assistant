import subprocess
from openai import OpenAI
from logger import logger, ErrorMessage
class OpenaiSpeaker:

    def __init__(self):
        try:
            self.client = OpenAI()
            self.player_command = ["ffplay", "-autoexit", "-", "-nodisp"]

        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : __init__: {e}"))
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")


    def speak(self, text: str):
        try:

            # Call the stream method on the speak property
            response = self.client.audio.speech.create(
                model="tts-1",
                voice="echo",
                input=text,
                speed=1.25
            )
            response_stream = response.iter_bytes(chunk_size=4096)


            self.player_process = subprocess.Popen(
                self.player_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            for chunk in response_stream:
                if chunk:
                    self.player_process.stdin.write(chunk)
                    self.player_process.stdin.flush()

            if self.player_process.stdin:
                self.player_process.stdin.close()
            self.player_process.wait()

        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : speak: {e}"))
            raise Exception(f"{self.__class__.__name__} : speak: {e}")


