import json
from typing import Any, Awaitable, Callable, Optional

from models.tools import ToolCall
from logger import logger, ErrorMessage


class EventHandler:
    """Processes events from OpenAI Realtime API connection."""

    def __init__(
        self,
        on_audio_delta: Callable[[str], Awaitable[None]],
        on_audio_committed: Callable[[], None],
    ):
        """
        Initialize the event handler.

        Args:
            on_audio_delta: Async callback for audio chunks (base64 string).
            on_audio_committed: Callback when audio buffer is committed.
        """
        self._on_audio_delta = on_audio_delta
        self._on_audio_committed = on_audio_committed
        self._response_done_received = False
        self._user_transcript_received = False

    async def process_events(self, connection) -> Optional[str]:
        """
        Process events from the connection until response is complete.

        Returns the final transcript response.
        """
        response = None
        try:
            print("Processing events...")
            async for event in connection:
                print(f"[Event] {event.type}")

                if event.type == "error":
                    print(f"Error event: {event.error}")

                elif event.type == "input_audio_buffer.committed":
                    print("Audio buffer committed, stopping recording...")
                    self._on_audio_committed()

                elif event.type == "conversation.item.input_audio_transcription.completed":
                    print(f"User Transcript: {event.transcript}")
                    self._user_transcript_received = True
                    if self._response_done_received:
                        return response

                elif event.type == "response.audio_transcript.done":
                    response = event.transcript
                    print(f"Assistant Transcript: {response}")

                elif event.type == "response.output_audio.delta":
                    await self._on_audio_delta(event.delta)

                elif event.type == "response.done":
                    print("Response done")
                    print(f"Output type: {event.response.output[0].type}")

                    if event.response.output[0].type == "function_call":
                        await self._handle_function_call(event, connection)

                    elif event.response.output[0].type == "message":
                        self._response_done_received = True
                        if self._user_transcript_received:
                            return response

            print("[Event loop] Exited async for loop - connection closed or no more events")

        except Exception as e:
            print(f"Error in event processing: {e}")
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : process_events: {e}"))
            raise

        print(f"[Event loop] Returning response: {response}")
        return response

    async def _handle_function_call(self, event, connection) -> None:
        """Execute function call and send result back."""
        print(
            f"Arguments: {event.response.output[0].arguments} "
            f"- type: {type(event.response.output[0].arguments)}"
        )
        decoded_arguments = json.loads(event.response.output[0].arguments)

        tool_call = ToolCall(
            tool_call_id=event.response.output[0].call_id,
            function_name=event.response.output[0].name,
            arguments=decoded_arguments,
        )

        tool_result = tool_call.result
        print(f"Tool result: {tool_result}")

        await connection.conversation.item.create(
            item={
                "call_id": tool_call.tool_call_id,
                "type": "function_call_output",
                "output": tool_result,
            }
        )
        await connection.response.create()
