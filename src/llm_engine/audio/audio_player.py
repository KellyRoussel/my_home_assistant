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
        self._process: Optional[asyncio.subprocess.Process] = None
        self._queue: Optional[asyncio.Queue] = None
        self._writer_task: Optional[asyncio.Task] = None
        self._is_first_chunk = True
        self._stream_start_time: Optional[float] = None
        self._total_audio_duration: float = 0

    @property
    def is_playing(self) -> bool:
        """Whether audio is currently playing."""
        return self._process is not None and self._process.returncode is None

    @property
    def remaining_duration(self) -> float:
        """Estimated remaining playback duration in seconds."""
        if not self._stream_start_time:
            return 0
        time_elapsed = time.time() - self._stream_start_time
        return max(0, self._total_audio_duration - time_elapsed)

    async def stream_bytes(self, raw_bytes: bytes) -> None:
        """Enqueue raw PCM bytes for playback (non-blocking)."""
        chunk_samples = len(raw_bytes) // self._config.bytes_per_sample
        chunk_duration = chunk_samples / self._config.output_sample_rate
        self._total_audio_duration += chunk_duration
        print(f"[AudioPlayer] stream_bytes: {len(raw_bytes)} bytes ({chunk_duration:.3f}s), total={self._total_audio_duration:.3f}s")

        if self._is_first_chunk:
            await self.cleanup()
            await self._start_player()
            print(f"[AudioPlayer] ffplay started (pid={self._process.pid})")
            self._stream_start_time = time.time()
            self._is_first_chunk = False

        self._queue.put_nowait(raw_bytes)

    async def _writer_loop(self) -> None:
        """Background task: drain audio queue into ffplay stdin."""
        try:
            while True:
                chunk = await self._queue.get()
                if chunk is None:
                    break  # sentinel: no more data
                if self._process and self._process.stdin and self._process.returncode is None:
                    self._process.stdin.write(chunk)
                    try:
                        await asyncio.wait_for(self._process.stdin.drain(), timeout=5.0)
                    except asyncio.TimeoutError:
                        pid = self._process.pid
                        print(f"[AudioPlayer] FREEZE DETECTED: drain() blocked >5s (pid={pid}) - ffplay stuck")
                        logger.log(ErrorMessage(content=f"AudioPlayer writer: drain() timeout (pid={pid}), ffplay stuck"))
                        return
                else:
                    print("[AudioPlayer] writer: process unavailable, stopping")
                    return
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[AudioPlayer] writer error: {type(e).__name__}: {e}")
            logger.log(ErrorMessage(content=f"AudioPlayer writer: {type(e).__name__}: {e}"))
        finally:
            # Close stdin so ffplay receives EOF and finishes playing
            if self._process and self._process.stdin:
                try:
                    self._process.stdin.close()
                    await self._process.stdin.wait_closed()
                except Exception:
                    pass

    async def stream_chunk(self, audio_base64: str) -> None:
        """Stream a base64-encoded audio chunk to the player."""
        await self.stream_bytes(base64.b64decode(audio_base64))

    async def _start_player(self) -> None:
        """Start ffplay as an asyncio subprocess."""
        self._process = await asyncio.create_subprocess_exec(
            "ffplay",
            "-f", self._config.output_format,
            "-ar", str(self._config.output_sample_rate),
            "-ac", "1",
            "-i", "pipe:0",
            "-nodisp",
            "-autoexit",
            "-volume", "100",
            "-sync", "ext",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        self._queue = asyncio.Queue()
        self._writer_task = asyncio.create_task(self._writer_loop())

    async def wait_for_completion(self) -> None:
        """Wait for all queued audio to finish playing."""
        if not self._process or self._process.returncode is not None:
            return

        # Signal writer to close stdin after draining the queue
        if self._queue:
            self._queue.put_nowait(None)

        remaining = self.remaining_duration + 1
        print(
            f"Elapsed: {time.time() - self._stream_start_time:.2f}s, "
            f"Total: {self._total_audio_duration:.2f}s, "
            f"Remaining: {remaining:.2f}s"
        )

        # Wait for writer to finish closing stdin (shield so we don't cancel it on timeout)
        if self._writer_task and not self._writer_task.done():
            try:
                await asyncio.wait_for(asyncio.shield(self._writer_task), timeout=remaining + 2)
            except asyncio.TimeoutError:
                print("[AudioPlayer] wait_for_completion: writer task timed out")

        # Wait for ffplay to finish playing all buffered audio
        if self._process and self._process.returncode is None:
            try:
                await asyncio.wait_for(self._process.wait(), timeout=remaining + 2)
                print("[AudioPlayer] ffplay finished playing")
            except asyncio.TimeoutError:
                print("[AudioPlayer] wait_for_completion: timed out waiting for ffplay")

    async def cleanup(self) -> None:
        """Stop playback immediately and clean up."""
        if self._writer_task:
            self._writer_task.cancel()
            try:
                await asyncio.wait_for(self._writer_task, timeout=1.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass
            self._writer_task = None

        if self._process:
            pid = self._process.pid
            try:
                if self._process.stdin:
                    try:
                        self._process.stdin.close()
                        await asyncio.wait_for(self._process.stdin.wait_closed(), timeout=1.0)
                    except (asyncio.TimeoutError, Exception):
                        pass
                try:
                    await asyncio.wait_for(self._process.wait(), timeout=2.0)
                    print(f"[AudioPlayer] ffplay exited cleanly (pid={pid})")
                except asyncio.TimeoutError:
                    print(f"[AudioPlayer] cleanup: ffplay (pid={pid}) didn't exit in 2s, killing")
                    self._process.kill()
                    await self._process.wait()
            except Exception as e:
                print(f"[AudioPlayer] cleanup error (pid={pid}): {type(e).__name__}: {e}")
            finally:
                self._process = None

        self._queue = None
        self._is_first_chunk = True
        self._stream_start_time = None
        self._total_audio_duration = 0
