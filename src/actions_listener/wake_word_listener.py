import numpy as np
import pyaudio
from pathlib import Path
from logger import logger, AppMessage, ErrorMessage
from openwakeword.model import Model
import asyncio
from collections import deque
import wave
import datetime
from config import Config

_SCRIPT_DIR = Path(__file__).parent
class WakeWordListener:
    MAX_BUFFER_SIZE = 1000
    PRE_DETECTION_SECONDS = 3
    SAMPLE_RATE = 16000
    CHUNK_SIZE = 1280
    #SILENCE_THRESHOLD = 500
    def __init__(self):
        self._detect_callback = None
        self._wake_word_is_detected = False
        self.listening = True
        self._paused = False
        self.audio = pyaudio.PyAudio()
        _buf_chunks = int(self.PRE_DETECTION_SECONDS * self.SAMPLE_RATE / self.CHUNK_SIZE)
        self._audio_buffer = deque(maxlen=_buf_chunks)
        # Load the wake word model
        self.oww_model = Model(wakeword_models=[str(_SCRIPT_DIR / "hey_jarvis_v0.1.tflite")],
                               enable_speex_noise_suppression=True,
                               vad_threshold=0.8,
                               inference_framework="tflite",
                               custom_verifier_models={"hey_jarvis_v0.1": str(_SCRIPT_DIR / "hey_jarvis_retrained.pkl")},
                                custom_verifier_threshold=0.9)
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
                    self._audio_buffer.append(audio_data)

                    rms = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
                    #print(f"--- RMS: {rms}")
                    #if rms < self.SILENCE_THRESHOLD:
                     #   continue  # Ignore ce buffer, trop silencieux

                    # Predict using the model
                    prediction = self.oww_model.predict(audio_data)
    
                    # Check if any model detected the wakeword
                    for mdl in self.oww_model.prediction_buffer.keys():
                        scores = list(self.oww_model.prediction_buffer[mdl])
                        sliding_avg = round(np.mean(scores[-3:]), 2)
                        if scores[-1] > 0.5:
                            print(round(scores[-1],2), f"avg3: {sliding_avg}")
                            logger.log(AppMessage(content=f"~~~~\nNo detection, but score: {round(scores[-1],2)} \nsliding_avg: {round(sliding_avg, 2)} \nRMS: {round(rms,2)}\n~~~~"))
                        #if scores[-1] > 0.8:  # Threshold for detection
                        if scores[-1] > 0.8 and sliding_avg > 0.6: # Trying something else
                            if not self._wake_word_is_detected:
                                self._wake_word_is_detected = True
                                logger.log(AppMessage(content=f"Wakeword detected with sliding_avg: {round(sliding_avg, 2)} \nscore: {round(scores[-1],2)} \nRMS: {round(rms,2)}"))
                               # print(f"===> Wakeword detected with sliding_avg: {round(sliding_avg, 2)} \nscore: {round(scores[-1],2)} \nRMS: {round(rms,2)}")
                                self._save_trigger_audio()
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
        self.oww_model = Model(
            wakeword_models=[str(_SCRIPT_DIR / "hey_jarvis_v0.1.tflite")],
            enable_speex_noise_suppression=True,
            vad_threshold=0.8,
            inference_framework="tflite",
            custom_verifier_models={"hey_jarvis_v0.1": str(_SCRIPT_DIR / "hey_jarvis_retrained.pkl")},
            custom_verifier_threshold=0.9
            )
        self.mic_stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1280)
        self._paused = False

    def _save_trigger_audio(self):
        try:
            Config.WAKE_WORD_SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")[:-3]
            filepath = Config.WAKE_WORD_SAMPLES_DIR / f"{timestamp}.wav"
            audio_bytes = np.concatenate(list(self._audio_buffer)).tobytes()
            with wave.open(str(filepath), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # int16 = 2 bytes
                wf.setframerate(self.SAMPLE_RATE)
                wf.writeframes(audio_bytes)
        except Exception as e:
            logger.log(ErrorMessage(content=f"WakeWordListener: failed to save trigger audio: {e}"))

    def set_detection_callback(self, callback):
        self._detect_callback = callback

