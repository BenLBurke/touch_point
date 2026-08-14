"""Runtime configuration for the touch point installation.

Every value can be overridden with an environment variable so the same
codebase runs unmodified across different Pi models -- e.g. a Pi Zero
whose USB sound card shows up at a different ALSA device index than the
one used for development.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return default


NUM_PIXELS = _env_int("TOUCHPOINT_NUM_PIXELS", 48)
PIXEL_PIN_NAME = os.environ.get("TOUCHPOINT_PIXEL_PIN", "D18")
BRIGHTNESS = _env_float("TOUCHPOINT_BRIGHTNESS", 0.4)
VOLUME = max(0.0, min(1.0, _env_float("TOUCHPOINT_VOLUME", 1.0)))

AUDIO_DRIVER = os.environ.get("TOUCHPOINT_AUDIO_DRIVER", "alsa")
AUDIO_DEVICE = os.environ.get("TOUCHPOINT_AUDIO_DEVICE", "plughw:2,0")

SOUND_DIR = Path(os.environ.get("TOUCHPOINT_SOUND_DIR", str(BASE_DIR / "sound_files")))
LOG_FILE = Path(os.environ.get("TOUCHPOINT_LOG_FILE", str(BASE_DIR / "touch_point.log")))
LOG_MAX_BYTES = _env_int("TOUCHPOINT_LOG_MAX_BYTES", 1_000_000)  # ~1MB per file
LOG_BACKUP_COUNT = _env_int("TOUCHPOINT_LOG_BACKUP_COUNT", 3)  # + 3 rotated copies

IDLE_COLOR = (50, 50, 50)
TAP_COLOR = (0, 0, 255)
