import os
import re
import io
import time
import subprocess
import pyaudio
from deepgram import DeepgramClient, SpeakOptions

class Speaker:

    def __init__(self):
        try:
            self.deepgram_client = DeepgramClient()
            self.player_command = ["ffplay", "-autoexit", "-", "-nodisp"]

        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")


    def _segment_text_by_sentence(self, text):
        try:
            return re.findall(r"[^.!?]+[.!?]", text)
        except Exception as e:
            raise Exception(f"_segment_text_by_sentence: {e}")

    # todo: https://developers.deepgram.com/docs/text-chunking-for-tts-optimization


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

            start_time = time.time()  # Record the time before sending the request
            first_byte_time = None  # Initialize a variable to store the time when the first byte is received

            for chunk in response_stream:
                if chunk:
                    if first_byte_time is None:  # Check if this is the first chunk received
                        first_byte_time = time.time()  # Record the time when the first byte is received
                        ttfb = int((first_byte_time - start_time) * 1000)  # Calculate the time to first byte
                        print(f"TTS Time to First Byte (TTFB): {ttfb}ms\n")
                    self.player_process.stdin.write(chunk)
                    self.player_process.stdin.flush()

            if self.player_process.stdin:
                self.player_process.stdin.close()
            self.player_process.wait()

        except Exception as e:
            raise Exception(f"speak: {e}")

