import asyncio
import queue
import subprocess
import time
from pathlib import Path
from typing import Callable, Optional

from tools.tool import Tool
from llm_engine.audio import AudioRecorder, AudioPlayer
from llm_engine.realtime_session import RealtimeSession
from llm_engine.event_handler import EventHandler
from llm_engine.models import AudioConfig, ConversationResult, SessionConfig
from logger import logger, AppMessage, ErrorMessage

_SCRIPT_DIR = Path(__file__).parent


class RealTimeEngine:
    """
    Facade coordinating real-time voice interaction.

    Public API:
        - __init__(tools: list[Tool])
        - start() -> Optional[str]
    """

    def __init__(self, tools: list[Tool] = None):
        try:
            self._audio_config = AudioConfig()
            self._session_config = SessionConfig(tools=list(tools) if tools else [])

            # Components initialized per session
            self._audio_queue: Optional[queue.Queue] = None
            self._stop_event: Optional[asyncio.Event] = None
            self._recorder: Optional[AudioRecorder] = None
            self._player: Optional[AudioPlayer] = None
            self._session: Optional[RealtimeSession] = None
            self._event_handler: Optional[EventHandler] = None
            self._is_processing = False

        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : __init__: {e}"))
            raise

    def _reset(self) -> None:
        """Reset state between sessions."""
        self._audio_queue = None
        self._stop_event = None
        self._recorder = None
        self._player = None
        self._session = None
        self._event_handler = None
        self._is_processing = False

    async def start(
        self,
        on_user_transcript: Optional[Callable[[str], None]] = None,
        on_assistant_transcript: Optional[Callable[[str], None]] = None,
    ) -> Optional[ConversationResult]:
        """
        Start a real-time voice interaction session.

        Args:
            on_user_transcript: Optional callback invoked immediately when the user transcript is available.
            on_assistant_transcript: Optional callback invoked immediately when the assistant transcript is available.

        Returns a ConversationResult with user and assistant transcripts.
        """
        result = None
        audio_task = None
        self._reset()

        # Initialize components
        self._audio_queue = queue.Queue()
        self._stop_event = asyncio.Event()
        self._player = AudioPlayer(self._audio_config)
        self._recorder = AudioRecorder(
            config=self._audio_config,
            on_audio_data=self._audio_queue.put_nowait,
        )
        self._session = RealtimeSession(self._session_config)
        self._event_handler = EventHandler(
            on_audio_delta=self._player.stream_chunk,
            on_audio_committed=lambda: self._stop_event.set(),
            on_user_transcript=on_user_transcript,
            on_assistant_transcript=on_assistant_transcript,
        )

        try:
            async with self._session.connect() as connection:
                logger.log(AppMessage(content="About to start recording..."))
                self._notify()
                await self._recorder.start(self._stop_event)
                logger.log(
                    AppMessage(content="Recording started, now starting event and audio processing...")
                )

                self._is_processing = True

                event_task = asyncio.create_task(self._event_handler.process_events(connection))
                audio_task = asyncio.create_task(self._process_audio_queue())

                assistant_transcript = await event_task
                result = ConversationResult(
                    user_transcript=self._event_handler.user_transcript,
                    assistant_transcript=assistant_transcript,
                )

        except Exception as e:
            print(f"Error in main loop: {e}")
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : start: {e}"))
        finally:
            print("Finally")
            self._stop_event.set()
            self._is_processing = False

            if audio_task:
                print("Cancelling audio processing task...")
                await audio_task

            print("Audio processing task done")
            await self._handle_response_done()
            print("Cleaning up player...")
            self._reset()
            print("Reset done")

        return result

    async def _handle_response_done(self) -> None:
        """Wait for audio playback to complete and cleanup."""
        if self._player:
            await self._player.wait_for_completion()
            await self._player.cleanup()

    async def _process_audio_queue(self) -> None:
        """Bridge between recorder queue and session."""
        print("Processing audio queue...")
        chunks_sent = 0
        try:
            while self._is_processing and not self._stop_event.is_set():
                try:
                    base64_audio = self._audio_queue.get_nowait()
                    await self._session.send_audio(base64_audio)
                    chunks_sent += 1
                except queue.Empty:
                    await asyncio.sleep(0.01)
                    continue
                except Exception as e:
                    print(f"Error processing audio chunk: {e}")
                    await asyncio.sleep(0.01)

            print(f"[Audio queue] Exited loop - sent {chunks_sent} chunks, timeout_reached={self._recorder.timeout_reached if self._recorder else 'N/A'}")

            # Handle timeout
            if self._recorder and self._recorder.timeout_reached:
                print("Sending commit event due to timeout...")
                try:
                    await self._session.commit_audio()
                    print("Commit event sent successfully")
                except Exception as e:
                    print(f"Error sending commit event: {e}")

        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : _process_audio_queue: {e}"))
            print(f"Error in _process_audio_queue: {e}")

    def _notify(self, retries: int = 1) -> None:
        """Play notification sound."""
        try:
            print("Playing notification sound...")
            player_command = [
                "ffplay",
                "-nodisp",
                "-autoexit",
                str(_SCRIPT_DIR.parent / "listening.mp3"),
            ]
            start_time = time.perf_counter()
            subprocess.run(
                player_command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=1.5,
            )
            end_time = time.perf_counter()
            duration = end_time - start_time
            logger.log(AppMessage(content=f"ffplay duration {duration:.2f} seconds."))
            print(f"ffplay duration {duration:.2f} seconds.")
        except subprocess.TimeoutExpired:
            logger.log(
                ErrorMessage(
                    content=f"{self.__class__.__name__} : notify : ffplay timed out - remaining {retries} attempts"
                )
            )
            if retries > 0:
                return self._notify(retries=retries - 1)
