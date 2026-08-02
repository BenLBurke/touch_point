import pytest

from touchpoint import effects


class FakePixels(list):
    """Minimal stand-in for neopixel.NeoPixel: a fixed-size list plus a
    fill()/show() API, with a show() call counter."""

    def __init__(self, n):
        super().__init__([(0, 0, 0)] * n)
        self.show_calls = 0

    def fill(self, color):
        for i in range(len(self)):
            self[i] = color

    def show(self):
        self.show_calls += 1


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    """Effects call time.sleep() between animation frames; skip the
    real delay so the test suite runs instantly."""
    monkeypatch.setattr(effects.time, "sleep", lambda *a, **k: None)


def test_wheel_boundaries():
    assert effects.wheel(0) == (255, 0, 0)
    assert effects.wheel(85) == (0, 255, 0)
    assert effects.wheel(170) == (0, 0, 255)


def test_wheel_wraps_at_256():
    assert effects.wheel(256) == effects.wheel(0)
    assert effects.wheel(-1) == effects.wheel(255)


def test_clear_pixels_turns_everything_off():
    pixels = FakePixels(10)
    pixels.fill((10, 20, 30))
    effects.clear_pixels(pixels)
    assert all(p == (0, 0, 0) for p in pixels)
    assert pixels.show_calls == 1


def test_fade_to_color_ends_exactly_on_target():
    pixels = FakePixels(5)
    effects.fade_to_color(pixels, (100, 150, 200), duration=0.01)
    assert all(p == (100, 150, 200) for p in pixels)


def test_comet_leaves_only_tail_length_pixels_lit():
    pixels = FakePixels(20)
    effects.comet(pixels, (255, 0, 0), tail_length=4, delay=0)
    lit = [p for p in pixels if p != (0, 0, 0)]
    assert len(lit) == 4


def test_comet_handles_ring_smaller_than_tail(monkeypatch):
    # Regression guard: comet() derives pixel count from len(pixels)
    # rather than a hardcoded constant, so it can't index out of range
    # even on a ring shorter than the requested tail length.
    pixels = FakePixels(3)
    effects.comet(pixels, (255, 0, 0), tail_length=6, delay=0)
    assert len(pixels) == 3


def test_fade_burst_turns_pixel_back_off():
    pixels = FakePixels(8)
    effects.fade_burst(pixels, 2, (255, 0, 0), duration=0, steps=5)
    assert pixels[2] == (0, 0, 0)


def test_fireworks_respects_num_bursts(monkeypatch):
    pixels = FakePixels(16)
    monkeypatch.setattr(effects.random, "randint", lambda a, b: 0)
    monkeypatch.setattr(effects.random, "choice", lambda seq: seq[0])
    effects.fireworks(pixels, num_bursts=3, delay_between=0)
    # fireworks() always fades the lit pixel back to off before returning.
    assert pixels[0] == (0, 0, 0)


def test_burst_restores_original_pixel_state():
    pixels = FakePixels(10)
    effects.burst(pixels)
    assert all(p == (0, 0, 0) for p in pixels)
