import asyncio
import base64
import time
from typing import Callable, Optional

import sounddevice as sd

from llm_engine.models import AudioConfig
from logger import logger, AppMessage, ErrorMessage


class AudioRecorder:
    """Handles microphone input recording using sounddevice."""

    def __init__(
        self,
        config: AudioConfig,
        on_audio_data: Callable[[str], None],
    ):
        """
        Initialize the audio recorder.

        Args:
            config: Audio configuration settings.
            on_audio_data: Callback receiving base64-encoded audio chunks.
        """
        self._config = config
        self._on_audio_data = on_audio_data
        self._stream: Optional[sd.InputStream] = None
        self._stop_event: Optional[asyncio.Event] = None
        self._recording_start_time: Optional[float] = None
        self._timeout_reached = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._frames: list = []

    @property
    def timeout_reached(self) -> bool:
        """Whether recording stopped due to timeout."""
        return self._timeout_reached

    async def start(self, stop_event: asyncio.Event) -> None:
        """
        Start recording audio. Stops when stop_event is set or timeout.

        Args:
            stop_event: Event to signal recording should stop.
        """
        try:
            print("Starting recording...")
            self._stop_event = stop_event
            self._loop = asyncio.get_running_loop()
            self._frames = []
            self._recording_start_time = time.time()
            self._timeout_reached = False

            self._stream = sd.InputStream(
                samplerate=self._config.input_sample_rate,
                channels=self._config.input_channels,
                dtype=self._config.input_format,
                callback=self._audio_callback,
            )

            self._stream.start()
            logger.log(AppMessage(content=f"{self.__class__.__name__}: Start recording"))

            # Create monitoring task
            asyncio.create_task(self._monitor_timeout())

        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : start: {e}"))
            raise

    def stop(self) -> None:
        """Stop the recording stream."""
        try:
            if self._stream:
                self._stream.stop()
                self._stream.close()
                self._stream = None
        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : stop: {e}"))
            raise

    def _audio_callback(self, indata, frames, time_info, status) -> None:
        """Sounddevice callback - processes audio data."""
        if status:
            print(status, flush=True)

        try:
            if self._stop_event and not self._stop_event.is_set():
                raw_audio_data = indata.copy().astype(self._config.input_format).tobytes()
                base64_audio = base64.b64encode(raw_audio_data).decode("utf-8")

                # Send audio data via callback
                self._on_audio_data(base64_audio)

                self._frames.append(indata.copy())

                # Check for timeout
                if (
                    self._recording_start_time
                    and time.time() - self._recording_start_time
                    >= self._config.max_recording_duration
                ):
                    if self._loop:

                        async def set_stop():
                            self._timeout_reached = True
                            self._stop_event.set()

                        asyncio.run_coroutine_threadsafe(set_stop(), self._loop)

        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : _audio_callback: {e}"))
            print(f"Error in audio callback: {e}")

    async def _monitor_timeout(self) -> None:
        """Monitor the recording and stop when stop event is set or max duration reached."""
        while self._stop_event and not self._stop_event.is_set():
            # Check for timeout
            if (
                self._recording_start_time
                and time.time() - self._recording_start_time
                >= self._config.max_recording_duration
            ):
                print("Recording timeout reached...")
                self._timeout_reached = True
                self._stop_event.set()
                break
            await asyncio.sleep(0.1)

        print("Stop event received, stopping recording...")
        self.stop()
