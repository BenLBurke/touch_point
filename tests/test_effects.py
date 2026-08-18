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


class RecordingPixels(FakePixels):
    """FakePixels that also keeps a snapshot of every frame shown, so a
    test can inspect the *first* frame drawn instead of only the state
    left behind once the whole effect call returns."""

    def __init__(self, n):
        super().__init__(n)
        self.snapshots = []

    def show(self):
        super().show()
        self.snapshots.append(list(self))


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


def test_alternating_fill_lights_only_even_indices():
    pixels = FakePixels(10)
    effects.alternating_fill(pixels, (50, 50, 50))
    for i, p in enumerate(pixels):
        if i % 2 == 0:
            assert p == (50, 50, 50)
        else:
            assert p == (0, 0, 0)
    assert pixels.show_calls == 1


def test_alternating_fill_draws_roughly_half_the_current_of_a_full_fill():
    pixels = FakePixels(48)
    effects.alternating_fill(pixels, (50, 50, 50))
    lit = sum(1 for p in pixels if p != (0, 0, 0))
    assert lit == 24


def test_alternating_fill_overwrites_previous_state():
    pixels = FakePixels(6)
    pixels.fill((10, 10, 10))
    effects.alternating_fill(pixels, (255, 0, 0))
    assert pixels[0] == (255, 0, 0)
    assert pixels[1] == (0, 0, 0)


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


def _fake_clock(step=0.05):
    """A time.time() replacement that advances by `step` on every call,
    regardless of sleep (the no_sleep fixture neutralizes real sleeping,
    so water_ripple's own timing has to come from time.time() alone)."""
    state = {"n": 0}

    def fake_time():
        state["n"] += 1
        return state["n"] * step

    return fake_time


def test_water_ripple_runs_and_calls_show(monkeypatch):
    pixels = FakePixels(12)
    monkeypatch.setattr(effects.time, "time", _fake_clock())

    effects.water_ripple(pixels, duration=0.3, fps=20)

    assert pixels.show_calls >= 1


def test_water_ripple_colors_stay_within_low_and_high_bounds(monkeypatch):
    pixels = FakePixels(12)
    monkeypatch.setattr(effects.time, "time", _fake_clock())
    low = (6, 40, 66)
    high = (120, 210, 220)

    effects.water_ripple(pixels, low_color=low, high_color=high, duration=0.3, fps=20)

    for pixel in pixels:
        for channel in range(3):
            lo, hi = sorted((low[channel], high[channel]))
            assert lo <= pixel[channel] <= hi


def test_water_ripple_default_never_goes_fully_dark(monkeypatch):
    # Encodes the "soft" requirement: the low end of the ripple is a dim
    # blue, not black, so it never looks like the ring switched off.
    pixels = FakePixels(12)
    monkeypatch.setattr(effects.time, "time", _fake_clock())

    effects.water_ripple(pixels, duration=0.3, fps=20)

    assert all(pixel != (0, 0, 0) for pixel in pixels)


def test_water_ripple_is_smooth_between_neighboring_pixels(monkeypatch):
    # "Smooth and soft" means no hard edges between adjacent pixels --
    # unlike e.g. comet()'s sharp tail cutoff, neighboring pixels here
    # should always be close in brightness.
    pixels = FakePixels(24)
    monkeypatch.setattr(effects.time, "time", _fake_clock())

    effects.water_ripple(pixels, duration=0.3, fps=20)

    for i in range(len(pixels)):
        a = pixels[i]
        b = pixels[(i + 1) % len(pixels)]
        assert all(abs(a[c] - b[c]) < 60 for c in range(3))


def test_water_ripple_fades_in_from_low_color(monkeypatch):
    # Right after the tap chime the ripple shouldn't snap straight to full
    # swing -- the very first frame drawn should sit close to low_color.
    pixels = RecordingPixels(12)
    monkeypatch.setattr(effects.time, "time", _fake_clock(step=0.01))
    low = (6, 40, 66)

    effects.water_ripple(pixels, low_color=low, duration=2.0, fps=20, fade_in=1.0, fade_out=0.0)

    first_frame = pixels.snapshots[0]
    for pixel in first_frame:
        for channel in range(3):
            assert abs(pixel[channel] - low[channel]) < 40


def test_water_ripple_fades_out_before_ending(monkeypatch):
    # The last frame before duration elapses should have settled back
    # near low_color rather than cutting off mid-swell.
    pixels = FakePixels(12)
    monkeypatch.setattr(effects.time, "time", _fake_clock(step=0.01))
    low = (6, 40, 66)

    effects.water_ripple(pixels, low_color=low, duration=2.0, fps=20, fade_in=0.0, fade_out=1.0)

    for pixel in pixels:
        for channel in range(3):
            assert abs(pixel[channel] - low[channel]) < 40


def test_water_ripple_clamps_fade_windows_on_short_clips(monkeypatch):
    # A fade_in + fade_out longer than the clip itself shouldn't crash or
    # leave the ring stuck; it should just run and finish normally.
    pixels = FakePixels(12)
    monkeypatch.setattr(effects.time, "time", _fake_clock(step=0.01))

    effects.water_ripple(pixels, duration=0.3, fps=20, fade_in=5.0, fade_out=5.0)

    assert pixels.show_calls >= 1


def test_fade_pixels_to_does_not_snap_through_black():
    pixels = FakePixels(6)
    pixels.fill((100, 40, 20))

    effects.fade_pixels_to(pixels, (10, 10, 200), duration=0, steps=4)

    # Even the very first written frame should already be blended, never
    # a hard drop to (0, 0, 0) the way fade_to_color's first step would be.
    assert all(p != (0, 0, 0) for p in pixels)


def test_fade_pixels_to_lands_exactly_on_target():
    pixels = FakePixels(6)
    pixels.fill((100, 40, 20))

    effects.fade_pixels_to(pixels, (10, 10, 200), duration=0, steps=5)

    assert all(p == (10, 10, 200) for p in pixels)


def test_fade_pixels_to_handles_pixels_that_already_started_dark():
    pixels = FakePixels(4)  # starts all (0, 0, 0)

    effects.fade_pixels_to(pixels, (50, 50, 50), duration=0, steps=3)

    assert all(p == (50, 50, 50) for p in pixels)


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
