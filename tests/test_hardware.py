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


class FakeMixer:
    def __init__(self, already_open=False):
        self.calls = []
        self.open = already_open

    def get_init(self):
        return self.open

    def quit(self):
        self.calls.append("quit")
        self.open = False

    def pre_init(self, **kwargs):
        self.calls.append(("pre_init", kwargs))

    def init(self):
        self.calls.append("init")
        self.open = True


def test_init_audio_sets_env_vars_and_calls_mixer(monkeypatch):
    mixer = FakeMixer()
    fake_pygame = types.SimpleNamespace(mixer=mixer)
    monkeypatch.setitem(sys.modules, "pygame", fake_pygame)
    monkeypatch.setattr(config, "AUDIO_DRIVER", "alsa")
    monkeypatch.setattr(config, "AUDIO_DEVICE", "plughw:1,0")

    result = hardware.init_audio()

    assert result is fake_pygame
    assert "quit" not in mixer.calls
    assert mixer.calls[-1] == "init"
    assert mixer.calls[0][1]["frequency"] == 44100
    import os

    assert os.environ["SDL_AUDIODRIVER"] == "alsa"
    assert os.environ["AUDIODEV"] == "plughw:1,0"


def test_init_audio_closes_an_already_open_mixer_first(monkeypatch):
    # Reopening is how a speaker that dropped off USB and came back gets
    # picked up again, so the stale mixer must be closed before init.
    mixer = FakeMixer(already_open=True)
    monkeypatch.setitem(sys.modules, "pygame", types.SimpleNamespace(mixer=mixer))

    hardware.init_audio()

    assert mixer.calls[0] == "quit"
    assert mixer.calls[-1] == "init"


def test_load_sound_sets_volume(tmp_path):
    class FakeSound:
        def __init__(self, path):
            self.path = path
            self.volume = None

        def set_volume(self, volume):
            self.volume = volume

    fake_pygame = types.SimpleNamespace(mixer=types.SimpleNamespace(Sound=FakeSound))

    sound = hardware.load_sound(fake_pygame, tmp_path / "x.wav", volume=0.5)

    assert sound.path == str(tmp_path / "x.wav")
    assert sound.volume == 0.5
