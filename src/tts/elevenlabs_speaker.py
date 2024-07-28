from elevenlabs import stream
from elevenlabs.client import ElevenLabs


class ElevenLabsSpeaker:

    def __init__(self):
        try:
            self.client = ElevenLabs()
            self.player_command = ["ffplay", "-autoexit", "-", "-nodisp"]

        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")

    def text_stream(self, text: str):
        # split on ".", "!", "?"
        sentences = text.split(".")
        for sentence in sentences:
            yield sentence

    def speak(self, text: str):
        try:

            audio = self.client.generate(
                text=self.text_stream(text),
                voice="Will",
                model="eleven_multilingual_v2",
                stream = True
            )

            stream(audio)

        except Exception as e:
            raise Exception(f"speak: {e}")