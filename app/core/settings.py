from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os


class AppSettings(BaseModel):
    app_name: str = "Isilog Local Ticket Assistant"
    environment: str = Field(default="dev")
    db_path: Path = Path("./data/app.db")
    log_path: Path = Path("./data/app.log")
    whisper_model_size: str = "small"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "gemma3:4b"
    browser_channel: str = "msedge"
    helpdesk_url: str = "https://helpdesk.brgm.fr/IsilogWebSystem/Pages/HelpDesk/HELP005.aspx?Type=PROPERTY&Action=C&IwsId=1"
    timeout_seconds: int = 30
    debug: bool = False
    mitel_recordings_dir: Path = Path("C:/Users/hotline6/AppData/Roaming/Mitel/MitelDialer")
    live_recordings_dir: Path = Path("./data/live_recordings")
    live_sample_rate: int = 16000
    live_channels: int = 1


def load_settings(env_file: str = ".env") -> AppSettings:
    load_dotenv(env_file)
    settings = AppSettings(
        environment=os.getenv("APP_ENV", "dev"),
        db_path=Path(os.getenv("DB_PATH", "./data/app.db")),
        log_path=Path(os.getenv("LOG_PATH", "./data/app.log")),
        whisper_model_size=os.getenv("WHISPER_MODEL_SIZE", "small"),
        whisper_device=os.getenv("WHISPER_DEVICE", "cpu"),
        whisper_compute_type=os.getenv("WHISPER_COMPUTE_TYPE", "int8"),
        ollama_url=os.getenv("OLLAMA_URL", "http://127.0.0.1:11434"),
        ollama_model=os.getenv("OLLAMA_MODEL", "gemma3:4b"),
        browser_channel=os.getenv("BROWSER_CHANNEL", "msedge"),
        helpdesk_url=os.getenv("HELPDESK_URL", "https://helpdesk.brgm.fr/IsilogWebSystem/Pages/HelpDesk/HELP005.aspx?Type=PROPERTY&Action=C&IwsId=1"),
        timeout_seconds=int(os.getenv("TIMEOUT_SECONDS", "30")),
        debug=os.getenv("DEBUG", "false").lower() == "true",
        mitel_recordings_dir=Path(os.getenv("MITEL_RECORDINGS_DIR", "C:/Users/hotline6/AppData/Roaming/Mitel/MitelDialer")),
        live_recordings_dir=Path(os.getenv("LIVE_RECORDINGS_DIR", "./data/live_recordings")),
        live_sample_rate=int(os.getenv("LIVE_SAMPLE_RATE", "16000")),
        live_channels=int(os.getenv("LIVE_CHANNELS", "1")),
    )
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    settings.log_path.parent.mkdir(parents=True, exist_ok=True)
    settings.live_recordings_dir.mkdir(parents=True, exist_ok=True)
    return settings
