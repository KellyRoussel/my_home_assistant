import numpy as np
from dataclasses import dataclass


@dataclass
class AudioConfig:
    """Configuration for audio recording and playback."""

    # Recording settings
    input_sample_rate: int = 24000
    input_channels: int = 1
    input_chunk_size: int = 1024
    input_format: type = np.int16
    max_recording_duration: int = 60

    # Playback settings
    output_sample_rate: int = 24000
    output_format: str = "s16le"
    bytes_per_sample: int = 2
