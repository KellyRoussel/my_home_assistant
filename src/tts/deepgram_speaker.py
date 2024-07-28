import subprocess
from deepgram import DeepgramClient, SpeakOptions

class DeepgramSpeaker:

    def __init__(self):
        try:
            self.deepgram_client = DeepgramClient()
            self.player_command = ["ffplay", "-autoexit", "-", "-nodisp"]

        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")


    def speak(self, text: str):
        try:
            options = SpeakOptions(
                model="aura-asteria-en",
            )

            # Call the stream method on the speak property
            response = self.deepgram_client.speak.v("1").stream({"text": text}, options)
            #  This takes the resulting audio and holds it in memory via io.BytesIO.
            response_stream = response.stream

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
            raise Exception(f"speak: {e}")


