from dataclasses import dataclass
from typing import Optional


@dataclass
class ConversationResult:
    """Result of a real-time voice interaction session."""

    user_transcript: Optional[str] = None
    assistant_transcript: Optional[str] = None
