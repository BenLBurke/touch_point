import importlib

from touchpoint import config

ENV_VARS = (
    "TOUCHPOINT_NUM_PIXELS",
    "TOUCHPOINT_PIXEL_PIN",
    "TOUCHPOINT_BRIGHTNESS",
    "TOUCHPOINT_VOLUME",
    "TOUCHPOINT_AUDIO_DRIVER",
    "TOUCHPOINT_AUDIO_DEVICE",
    "TOUCHPOINT_LOG_MAX_BYTES",
    "TOUCHPOINT_LOG_BACKUP_COUNT",
)


def _reload_with_clean_env(monkeypatch):
    for var in ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    return importlib.reload(config)


def test_defaults_when_env_unset(monkeypatch):
    reloaded = _reload_with_clean_env(monkeypatch)
    try:
        assert reloaded.NUM_PIXELS == 48
        assert reloaded.PIXEL_PIN_NAME == "D18"
        assert reloaded.BRIGHTNESS == 0.4
        assert reloaded.VOLUME == 1.0
        assert reloaded.AUDIO_DRIVER == "alsa"
        assert reloaded.AUDIO_DEVICE == "plughw:2,0"
        assert reloaded.LOG_MAX_BYTES == 1_000_000
        assert reloaded.LOG_BACKUP_COUNT == 3
    finally:
        importlib.reload(config)


def test_env_overrides_are_applied(monkeypatch):
    _reload_with_clean_env(monkeypatch)
    monkeypatch.setenv("TOUCHPOINT_NUM_PIXELS", "12")
    monkeypatch.setenv("TOUCHPOINT_AUDIO_DEVICE", "plughw:1,0")
    reloaded = importlib.reload(config)
    try:
        assert reloaded.NUM_PIXELS == 12
        assert reloaded.AUDIO_DEVICE == "plughw:1,0"
    finally:
        monkeypatch.delenv("TOUCHPOINT_NUM_PIXELS", raising=False)
        monkeypatch.delenv("TOUCHPOINT_AUDIO_DEVICE", raising=False)
        importlib.reload(config)


def test_volume_is_clamped_to_valid_range(monkeypatch):
    _reload_with_clean_env(monkeypatch)
    monkeypatch.setenv("TOUCHPOINT_VOLUME", "1.5")
    reloaded = importlib.reload(config)
    try:
        assert reloaded.VOLUME == 1.0
    finally:
        monkeypatch.delenv("TOUCHPOINT_VOLUME", raising=False)
        importlib.reload(config)

    monkeypatch.setenv("TOUCHPOINT_VOLUME", "-0.5")
    reloaded = importlib.reload(config)
    try:
        assert reloaded.VOLUME == 0.0
    finally:
        monkeypatch.delenv("TOUCHPOINT_VOLUME", raising=False)
        importlib.reload(config)


def test_invalid_numeric_env_falls_back_to_default(monkeypatch):
    _reload_with_clean_env(monkeypatch)
    monkeypatch.setenv("TOUCHPOINT_NUM_PIXELS", "not-a-number")
    reloaded = importlib.reload(config)
    try:
        assert reloaded.NUM_PIXELS == 48
    finally:
        monkeypatch.delenv("TOUCHPOINT_NUM_PIXELS", raising=False)
        importlib.reload(config)
