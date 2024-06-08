import wave

class Record:


    def __init__(self, output_filename):
        try:
            self.output_filename = output_filename
            self.frames = []
            self.stream = None
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")


    def save(self, channels, sample_width, framerate):
        try:
            with wave.open(self.output_filename, 'wb') as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(sample_width)
                wf.setframerate(framerate)
                wf.writeframes(b''.join(self.frames))
            print(f"Audio saved to {self.output_filename}")
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : save: {e}")

