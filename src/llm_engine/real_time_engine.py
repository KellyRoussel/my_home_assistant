import asyncio
import base64
import json
import queue
import subprocess
from pathlib import Path
from typing import Callable, Optional

from agents import FunctionTool
from agents.realtime import RealtimeAgent, RealtimeRunner

from tools.tool import Tool
from llm_engine.audio import AudioRecorder, AudioPlayer
from llm_engine.models import AudioConfig, ConversationResult
from session.conversation import Conversation
from logger import logger, AppMessage, ErrorMessage

_SCRIPT_DIR = Path(__file__).parent


def _to_function_tool(tool: Tool) -> FunctionTool:
    """Wrap a Tool instance as an SDK FunctionTool."""
    schema = tool.json_definition_flatten

    async def on_invoke_tool(ctx, args_str: str) -> str:
        args = json.loads(args_str)
        try:
            result = await asyncio.to_thread(tool.execute, **args)
            return str(result)
        except Exception as e:
            return f"Error: {e}"

    return FunctionTool(
        name=schema["name"],
        description=schema["description"],
        params_json_schema=schema["parameters"],
        on_invoke_tool=on_invoke_tool,
    )


class RealTimeEngine:
    """
    Facade coordinating real-time voice interaction via the openai-agents SDK.

    Public API:
        - __init__(tools: list[Tool])
        - start() -> Optional[ConversationResult]
    """

    def __init__(self, tools: list[Tool] = None):
        self._tools = list(tools) if tools else []
        self._audio_config = AudioConfig()

    async def start(
        self,
        on_user_transcript: Optional[Callable[[str], None]] = None,
        on_assistant_transcript: Optional[Callable[[str], None]] = None,
    ) -> Optional[ConversationResult]:
        """
        Start a real-time voice interaction session.

        Args:
            on_user_transcript: Optional callback invoked when the user transcript is available.
            on_assistant_transcript: Optional callback invoked when the assistant transcript is available.

        Returns a ConversationResult with user and assistant transcripts.
        """
        sdk_tools = [_to_function_tool(t) for t in self._tools]
        agent = RealtimeAgent(
            name="Jarvis",
            instructions=Conversation()._get_prompt(),
            tools=sdk_tools,
        )
        runner = RealtimeRunner(
            starting_agent=agent,
            config={
                "model_settings": {
                    "model_name": "gpt-realtime-mini",
                    "voice": "echo",
                    "modalities": ["audio"],
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "input_audio_transcription": {"model": "gpt-4o-mini-transcribe"},
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "silence_duration_ms": 1000,
                        "prefix_padding_ms": 500,
                    },
                }
            },
        )

        audio_queue: queue.Queue = queue.Queue()
        stop_recording = asyncio.Event()
        player = AudioPlayer(self._audio_config)
        recorder = AudioRecorder(
            config=self._audio_config,
            on_audio_data=audio_queue.put_nowait,
        )

        user_transcript: Optional[str] = None
        assistant_transcript: Optional[str] = None
        audio_task = None

        try:
            async with await runner.run() as session:
                print("Session started. You can speak now...")
                logger.log(AppMessage(content="Connected via openai-agents SDK"))
                await recorder.start(stop_recording)

                async def send_audio_loop():
                    while not stop_recording.is_set():
                        try:
                            b64 = audio_queue.get_nowait()
                            await session.send_audio(base64.b64decode(b64))
                        except queue.Empty:
                            await asyncio.sleep(0.01)

                audio_task = asyncio.create_task(send_audio_loop())
                await asyncio.to_thread(self._notify)

                async for event in session:
                    if event.type != "raw_model_event":
                        print(f"[Event] {event.type}")

                    if event.type == "agent_start":
                        logger.log(AppMessage(content=f"Agent started: {event.agent.name}"))
                        stop_recording.set()
                        
                    elif event.type == "agent_end":
                        logger.log(AppMessage(content=f"Agent ended: {event.agent.name}"))

                    elif event.type == "audio":
                        await player.stream_bytes(event.audio.data)

                    elif event.type == "audio_end":
                        stop_recording.set()
                        break

                    elif event.type == "audio_interrupted":
                        await player.cleanup()

                    elif event.type == "tool_start":
                        tool_name = getattr(event.tool, "name", str(event.tool))
                        logger.log(AppMessage(content=f"Tool call: {tool_name}"))

                    elif event.type == "tool_end":
                        tool_name = getattr(event.tool, "name", str(event.tool))
                        logger.log(AppMessage(content=f"Tool result: {tool_name} → {event.output}"))

                    elif event.type == "handoff":
                        from_name = getattr(event.from_agent, "name", str(event.from_agent))
                        to_name = getattr(event.to_agent, "name", str(event.to_agent))
                        logger.log(AppMessage(content=f"Handoff: {from_name} → {to_name}"))

                    elif event.type == "raw_model_event":
                        inner = event.data
                        inner_type = getattr(inner, "type", None)
                        if inner_type != "raw_server_event":
                            print(f"  [raw] {inner_type}")
                        if inner_type == "conversation.item.input_audio_transcription.completed":
                            user_transcript = getattr(inner, "transcript", None)
                            if user_transcript and on_user_transcript:
                                on_user_transcript(user_transcript)
                        elif inner_type == "response.audio_transcript.done":
                            assistant_transcript = getattr(inner, "transcript", None)
                            if assistant_transcript and on_assistant_transcript:
                                on_assistant_transcript(assistant_transcript)

                    elif event.type == "error":
                        logger.log(ErrorMessage(content=f"SDK realtime error: {event.error}"))
                        print(f"Error event: {event.error}")

                if audio_task:
                    audio_task.cancel()

        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : start: {e}"))
            print(f"Error in RealTimeEngine.start: {e}")
        finally:
            stop_recording.set()
            if audio_task and not audio_task.done():
                audio_task.cancel()
            await player.wait_for_completion()
            await player.cleanup()

        return ConversationResult(
            user_transcript=user_transcript,
            assistant_transcript=assistant_transcript,
        )

    def _notify(self, retries: int = 1) -> None:
        """Play notification sound."""
        try:
            subprocess.run(
                ["ffplay", "-nodisp", "-autoexit", str(_SCRIPT_DIR.parent / "listening.mp3")],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=1.5,
            )
        except subprocess.TimeoutExpired:
            if retries > 0:
                self._notify(retries=retries - 1)
