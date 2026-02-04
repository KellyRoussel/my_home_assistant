from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = Path(__file__).parent


class Config:
    LOGS_FILE = PROJECT_ROOT / "logs.json"
    TOKEN_FILE = PROJECT_ROOT / "secret_token.json"
    NOTIFICATION_SOUND = SRC_DIR / "listening.mp3"
    WORKDIR = PROJECT_ROOT / "workdir"
