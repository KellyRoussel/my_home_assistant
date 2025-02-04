import numpy as np
import pyaudio
from logger import logger, AppMessage, ErrorMessage
from openwakeword.model import Model
import asyncio
class WakeWordListener:
    MAX_BUFFER_SIZE = 1000
    def __init__(self):
        self._detect_callback = None
        self._wake_word_is_detected = False
        self.listening = True
        self._paused = False
        self.audio = pyaudio.PyAudio()
        # Load the wake word model
        self.oww_model = Model(wakeword_models=["./actions_listener/hey_jarvis_v0.1.tflite"], inference_framework="tflite")
        self.mic_stream = None
    
    

    async def start_listening(self):
        self.listening = True
        self.mic_stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True,
                                          frames_per_buffer=1280)
        while self.listening:
            if not self._paused:
                try:
                    # Capture audio
                    audio_data = np.frombuffer(self.mic_stream.read(1280), dtype=np.int16)

                    # Predict using the model
                    prediction = self.oww_model.predict(audio_data)
    
                    # Check if any model detected the wakeword
                    for mdl in self.oww_model.prediction_buffer.keys():
                        scores = list(self.oww_model.prediction_buffer[mdl])
                        #print(round(scores[-1],2))
                        if scores[-1] > 0.9:  # Threshold for detection
                            if not self._wake_word_is_detected:
                                self._wake_word_is_detected = True
                                logger.log(AppMessage(content=f"Wakeword detected with score: {round(scores[-1],2)}"))
                                print(f"===> Wakeword detected with score: {round(scores[-1],2)}")
                                await self._detect_callback()
                        else:
                            self._wake_word_is_detected = False
                    if len(self.oww_model.prediction_buffer) > self.MAX_BUFFER_SIZE:
                        self.oww_model.prediction_buffer.clear()  # Or implement a rolling buffer mechanism

                except Exception as e:
                    logger.log(ErrorMessage(content=f"{self.__class__.__name__} : start_listening: {e}"))
                    raise Exception(f"{self.__class__.__name__} : start_listening: {e}")
            await asyncio.sleep(0.01)  # Prevent tight loop

    def stop_listening(self):
        self.listening = False
        self.mic_stream.stop_stream()

    def pause(self):
        self._paused = True
        self.mic_stream.stop_stream()
        self.mic_stream.close() 
    
    def resume(self):
        self._wake_word_is_detected = False
        #self.oww_model.reset()
        self.oww_model = Model(wakeword_models=["./actions_listener/hey_jarvis_v0.1.tflite"], inference_framework="tflite")
        self.mic_stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1280)
        self._paused = False

    def set_detection_callback(self, callback):
        self._detect_callback = callback

