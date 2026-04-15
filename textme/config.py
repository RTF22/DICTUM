import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# .env aus dem Projektverzeichnis laden
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")


@dataclass
class Config:
    # Whisper
    whisper_model: str = "small"
    whisper_language: str = "de"

    # Audio
    sample_rate: int = 16000
    channels: int = 1
    silence_threshold: float = 0.01  # RMS unter diesem Wert = Stille
    min_duration: float = 0.5        # Mindestaufnahmelänge in Sekunden

    # Hotkeys
    hotkey_record: str = "ctrl+shift+space"
    hotkey_mode_a: str = "ctrl+shift+1"
    hotkey_mode_b: str = "ctrl+shift+2"
    hotkey_mode_c: str = "ctrl+shift+3"

    # Modus: "clean", "business", "rage"
    default_mode: str = "clean"

    # Anthropic
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    anthropic_model: str = "claude-sonnet-4-20250514"

    # UI
    overlay_display_seconds: float = 1.5
