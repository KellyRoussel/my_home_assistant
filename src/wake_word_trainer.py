import openwakeword
from config import Config


def train_verifier(positive_clips: list[str], negative_clips: list[str]) -> None:
    openwakeword.train_custom_verifier(
        positive_reference_clips=positive_clips,
        negative_reference_clips=negative_clips,
        output_path=str(Config.VERIFIER_MODEL),
        model_name=str(Config.WAKE_WORD_MODEL),
    )
