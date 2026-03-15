from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = Path(__file__).parent
_ACTIONS_LISTENER_DIR = SRC_DIR / "actions_listener"


class Config:
    LOGS_FILE = PROJECT_ROOT / "logs.json"
    TOKEN_FILE = PROJECT_ROOT / "secret_token.json"
    NOTIFICATION_SOUND = SRC_DIR / "listening.mp3"
    WORKDIR = PROJECT_ROOT / "workdir"
    MEAL_PLAN_STATE_FILE = PROJECT_ROOT / "workdir" / "meal_plan_state.json"
    WAKE_WORD_SAMPLES_DIR = PROJECT_ROOT / "data" / "wake_word_samples"
    WAKE_WORD_SAMPLES_TRUE_DIR = WAKE_WORD_SAMPLES_DIR / "true"
    WAKE_WORD_SAMPLES_FALSE_DIR = WAKE_WORD_SAMPLES_DIR / "false"
    WAKE_WORD_MODEL = _ACTIONS_LISTENER_DIR / "hey_jarvis_v0.1.tflite"
    VERIFIER_MODEL = _ACTIONS_LISTENER_DIR / "hey_jarvis_retrained.pkl"
    MIN_POSITIVE_SAMPLES = 3
    MIN_NEGATIVE_SAMPLES = 3
