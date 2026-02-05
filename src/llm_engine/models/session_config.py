from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools.tool import Tool


@dataclass
class SessionConfig:
    """Configuration for OpenAI Realtime API session."""

    model: str = "gpt-realtime-2025-08-28"
    output_modalities: list[str] = field(default_factory=lambda: ["audio"])
    input_format_type: str = "audio/pcm"
    input_rate: int = 24000
    transcription_model: str = "whisper-1"
    turn_detection_type: str = "server_vad"
    vad_threshold: float = 0.5
    prefix_padding_ms: int = 500
    silence_duration_ms: int = 1000
    create_response: bool = True
    voice: str = "echo"
    speed: float = 1.25
    tools: list["Tool"] = field(default_factory=list)

    def to_api_dict(self) -> dict:
        """Convert to OpenAI API session format."""
        return {
            "type": "realtime",
            "output_modalities": self.output_modalities,
            "audio": {
                "input": {
                    "format": {"type": self.input_format_type, "rate": self.input_rate},
                    "transcription": {"model": self.transcription_model},
                    "turn_detection": {
                        "type": self.turn_detection_type,
                        "threshold": self.vad_threshold,
                        "prefix_padding_ms": self.prefix_padding_ms,
                        "silence_duration_ms": self.silence_duration_ms,
                        "create_response": self.create_response,
                    },
                },
                "output": {"voice": self.voice, "speed": self.speed},
            },
            "tools": [tool.json_definition_flatten for tool in self.tools],
            "tool_choice": "auto",
        }
