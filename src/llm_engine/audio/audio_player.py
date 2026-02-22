import asyncio
import base64
import subprocess
import time
from typing import Optional

from llm_engine.models import AudioConfig
from logger import logger, ErrorMessage


class AudioPlayer:
    """Handles audio playback using ffplay subprocess."""

    def __init__(self, config: AudioConfig):
        self._config = config
        self._process: Optional[subprocess.Popen] = None
        self._is_first_chunk = True
        self._stream_start_time: Optional[float] = None
        self._total_audio_duration: float = 0

    @property
    def is_playing(self) -> bool:
        """Whether audio is currently playing."""
        return self._process is not None and self._process.poll() is None

    @property
    def remaining_duration(self) -> float:
        """Estimated remaining playback duration in seconds."""
        if not self._stream_start_time:
            return 0
        time_elapsed = time.time() - self._stream_start_time
        return max(0, self._total_audio_duration - time_elapsed)

    async def stream_bytes(self, raw_bytes: bytes) -> None:
        """Stream raw PCM bytes to the player (no base64 decoding needed)."""
        try:
            chunk_samples = len(raw_bytes) // self._config.bytes_per_sample
            chunk_duration = chunk_samples / self._config.output_sample_rate
            self._total_audio_duration += chunk_duration
            print(f"[AudioPlayer] stream_bytes: {len(raw_bytes)} bytes ({chunk_duration:.3f}s), total={self._total_audio_duration:.3f}s")

            if self._is_first_chunk:
                await self.cleanup()
                self._start_player()
                print(f"[AudioPlayer] ffplay started (pid={self._process.pid})")
                self._stream_start_time = time.time()
                self._is_first_chunk = False

            if self._process and self._process.stdin and self._process.poll() is None:
                loop = asyncio.get_event_loop()
                process = self._process
                try:
                    await asyncio.wait_for(
                        loop.run_in_executor(
                            None,
                            lambda: (process.stdin.write(raw_bytes), process.stdin.flush()),
                        ),
                        timeout=5.0,
                    )
                except asyncio.TimeoutError:
                    pid = self._process.pid if self._process else "None"
                    print(
                        f"[AudioPlayer] FREEZE DETECTED: stdin.write blocked >5s "
                        f"(pid={pid}, pipe buffer likely full — ffplay may be stuck)"
                    )
                    logger.log(ErrorMessage(content=f"AudioPlayer stdin write timeout (pid={pid}): ffplay deadlocked, killing process"))
                    await self.cleanup()
            else:
                poll = self._process.poll() if self._process else "None"
                print(f"[AudioPlayer] process dead or unavailable (poll={poll})")
                await self.cleanup()

        except BrokenPipeError:
            pid = self._process.pid if self._process else "None"
            print(f"[AudioPlayer] BrokenPipeError (pid={pid}) — ffplay stdin closed unexpectedly")
            await self.cleanup()
        except Exception as e:
            print(f"[AudioPlayer] Error streaming audio bytes: {type(e).__name__}: {e}")
            logger.log(ErrorMessage(content=f"AudioPlayer stream_bytes: {type(e).__name__}: {e}"))
            await self.cleanup()

    async def stream_chunk(self, audio_base64: str) -> None:
        """Stream a base64-encoded audio chunk to the player."""
        try:
            decoded_data = base64.b64decode(audio_base64)

            # Calculate duration of this chunk
            chunk_samples = len(decoded_data) // self._config.bytes_per_sample
            chunk_duration = chunk_samples / self._config.output_sample_rate
            self._total_audio_duration += chunk_duration

            if self._is_first_chunk:
                await self.cleanup()
                self._start_player()
                self._stream_start_time = time.time()
                self._is_first_chunk = False

            if self._process and self._process.stdin:
                if self._process.poll() is None:
                    self._process.stdin.write(decoded_data)
                    self._process.stdin.flush()
                else:
                    print("Player process has terminated unexpectedly")
                    await self.cleanup()

        except BrokenPipeError:
            print("Broken pipe - player process may have terminated")
            await self.cleanup()
        except Exception as e:
            print(f"Error streaming audio: {e}")
            await self.cleanup()

    def _start_player(self) -> None:
        """Start ffplay process."""
        self._process = subprocess.Popen(
            [
                "ffplay",
                "-f",
                self._config.output_format,
                "-ar",
                str(self._config.output_sample_rate),
                "-ac",
                "1",
                "-i",
                "pipe:0",
                "-nodisp",
                "-autoexit",
                "-volume",
                "100",
                "-sync",
                "ext",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            bufsize=0,
        )

    async def wait_for_completion(self) -> None:
        """Wait for current audio to finish playing."""
        if self._process and self._process.poll() is None:
            remaining = self.remaining_duration + 1  # Add buffer
            print(
                f"Elapsed: {time.time() - self._stream_start_time:.2f}s, "
                f"Total: {self._total_audio_duration:.2f}s, "
                f"Remaining: {remaining:.2f}s"
            )
            if remaining > 0:
                await asyncio.sleep(remaining)

    async def cleanup(self) -> None:
        """Clean up player process."""
        if self._process:
            pid = self._process.pid
            try:
                if self._process.stdin:
                    try:
                        self._process.stdin.close()
                    except OSError:
                        pass
                # Use run_in_executor so blocking wait() doesn't stall the event loop
                loop = asyncio.get_event_loop()
                try:
                    await asyncio.wait_for(
                        loop.run_in_executor(None, self._process.wait),
                        timeout=2.0,
                    )
                    print(f"[AudioPlayer] ffplay exited cleanly (pid={pid})")
                except asyncio.TimeoutError:
                    print(f"[AudioPlayer] cleanup: ffplay (pid={pid}) didn't exit in 2s, killing")
                    self._process.kill()
            except Exception as e:
                print(f"[AudioPlayer] cleanup error (pid={pid}): {type(e).__name__}: {e}")
            finally:
                self._process = None
                self._is_first_chunk = True
                self._stream_start_time = None
                self._total_audio_duration = 0
