"""Tests for touchpoint.hardware using fake hardware modules.

`hardware.py` imports board/neopixel/mfrc522/pygame lazily inside its
functions rather than at module scope, so we can plant lightweight fake
modules in sys.modules before calling those functions -- no real Pi,
LEDs, RFID reader, or sound card required.
"""
import sys
import types

import pytest

from touchpoint import config, hardware


class FakeNeoPixel:
    def __init__(self, pin, n, brightness, auto_write):
        self.pin = pin
        self.n = n
        self.brightness = brightness
        self.auto_write = auto_write


def test_init_pixels_uses_configured_pin_and_count(monkeypatch):
    fake_board = types.SimpleNamespace(D18="D18-PIN")
    fake_neopixel_module = types.SimpleNamespace(NeoPixel=FakeNeoPixel)
    monkeypatch.setitem(sys.modules, "board", fake_board)
    monkeypatch.setitem(sys.modules, "neopixel", fake_neopixel_module)
    monkeypatch.setattr(config, "PIXEL_PIN_NAME", "D18")
    monkeypatch.setattr(config, "NUM_PIXELS", 48)
    monkeypatch.setattr(config, "BRIGHTNESS", 0.4)

    pixels = hardware.init_pixels()

    assert pixels.pin == "D18-PIN"
    assert pixels.n == 48
    assert pixels.brightness == 0.4
    assert pixels.auto_write is False


def test_init_pixels_raises_clear_error_for_unknown_pin(monkeypatch):
    fake_board = types.SimpleNamespace()  # no D18 attribute
    monkeypatch.setitem(sys.modules, "board", fake_board)
    monkeypatch.setitem(sys.modules, "neopixel", types.SimpleNamespace(NeoPixel=FakeNeoPixel))
    monkeypatch.setattr(config, "PIXEL_PIN_NAME", "D18")

    with pytest.raises(AttributeError):
        hardware.init_pixels()


def test_init_reader_returns_simple_mfrc522(monkeypatch):
    sentinel = object()
    fake_module = types.SimpleNamespace(SimpleMFRC522=lambda: sentinel)
    monkeypatch.setitem(sys.modules, "mfrc522", fake_module)

    assert hardware.init_reader() is sentinel


def test_init_audio_sets_env_vars_and_calls_mixer(monkeypatch):
    calls = {}

    class FakeMixer:
        @staticmethod
        def pre_init(**kwargs):
            calls["pre_init"] = kwargs

        @staticmethod
        def init():
            calls["init"] = True

    fake_pygame = types.SimpleNamespace(mixer=FakeMixer)
    monkeypatch.setitem(sys.modules, "pygame", fake_pygame)
    monkeypatch.setattr(config, "AUDIO_DRIVER", "alsa")
    monkeypatch.setattr(config, "AUDIO_DEVICE", "plughw:1,0")

    result = hardware.init_audio()

    assert result is fake_pygame
    assert calls["init"] is True
    assert calls["pre_init"]["frequency"] == 44100
    import os

    assert os.environ["SDL_AUDIODRIVER"] == "alsa"
    assert os.environ["AUDIODEV"] == "plughw:1,0"


def test_load_all_sounds_covers_the_whole_library(monkeypatch, tmp_path):
    loaded_paths = []

    class FakeSound:
        def __init__(self, path):
            self.path = path
            self.volume = None
            loaded_paths.append(path)

        def set_volume(self, volume):
            self.volume = volume

    fake_pygame = types.SimpleNamespace(mixer=types.SimpleNamespace(Sound=FakeSound))
    monkeypatch.setattr(config, "SOUND_DIR", tmp_path)

    from touchpoint import sounds

    tap_sound, library = hardware.load_all_sounds(fake_pygame)

    assert isinstance(tap_sound, FakeSound)
    assert tap_sound.volume == 1.0
    assert set(library.keys()) == {clip.name for clip in sounds.SOUND_LIBRARY}
    for clip in sounds.SOUND_LIBRARY:
        assert library[clip.name]["length"] == clip.length
    # tap sound + one per library clip
    assert len(loaded_paths) == 1 + len(sounds.SOUND_LIBRARY)


def test_load_sound_defaults_to_configured_volume(monkeypatch, tmp_path):
    class FakeSound:
        def __init__(self, path):
            self.volume = None

        def set_volume(self, volume):
            self.volume = volume

    fake_pygame = types.SimpleNamespace(mixer=types.SimpleNamespace(Sound=FakeSound))
    monkeypatch.setattr(config, "VOLUME", 0.6)

    sound = hardware.load_sound(fake_pygame, tmp_path / "clip.wav")

    assert sound.volume == 0.6


def test_load_sound_explicit_volume_overrides_config(monkeypatch, tmp_path):
    class FakeSound:
        def __init__(self, path):
            self.volume = None

        def set_volume(self, volume):
            self.volume = volume

    fake_pygame = types.SimpleNamespace(mixer=types.SimpleNamespace(Sound=FakeSound))
    monkeypatch.setattr(config, "VOLUME", 0.6)

    sound = hardware.load_sound(fake_pygame, tmp_path / "clip.wav", volume=0.2)

    assert sound.volume == 0.2
