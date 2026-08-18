"""LED ring animations.

Every function takes a `pixels`-like object -- anything that supports
``len()``, item assignment, ``fill()`` and ``show()`` (a real
``neopixel.NeoPixel``, or a plain list-based fake in tests) -- so the
animation logic can be exercised without any LED hardware attached.
"""
import math
import random
import time

Color = tuple

FIREWORK_COLORS = [
    (255, 0, 0),      # red
    (255, 140, 0),    # orange
    (255, 255, 0),    # yellow
    (255, 255, 255),  # white
    (0, 0, 255),      # blue
    (128, 0, 128),    # purple
    (75, 0, 130),     # indigo
    (255, 20, 147),   # pink
]


def clear_pixels(pixels) -> None:
    pixels.fill((0, 0, 0))
    pixels.show()


def alternating_fill(pixels, color: Color) -> None:
    """Light every other pixel, leaving the rest off.

    Static (no animation loop), so it's safe to use anywhere a plain
    fill() was used before -- no risk to RFID read latency. Draws
    roughly half the current of lighting the whole ring at the same
    color, since WS2812 power scales with how many pixels are lit.
    """
    n = len(pixels)
    for i in range(n):
        pixels[i] = color if i % 2 == 0 else (0, 0, 0)
    pixels.show()


def wheel(pos: int) -> Color:
    """Generate rainbow colors across 0-255 positions."""
    pos = pos % 256
    if pos < 85:
        return (255 - pos * 3, pos * 3, 0)
    if pos < 170:
        pos -= 85
        return (0, 255 - pos * 3, pos * 3)
    pos -= 170
    return (pos * 3, 0, 255 - pos * 3)


def comet(pixels, color: Color, tail_length: int = 12, delay: float = 0.03) -> None:
    n = len(pixels)
    for i in range(n + tail_length):
        pixels.fill((0, 0, 0))
        for j in range(tail_length):
            idx = (i - j) % n
            brightness = (tail_length - j) / tail_length
            pixels[idx] = tuple(int(c * brightness) for c in color)
        pixels.show()
        time.sleep(delay)


def burst(pixels) -> None:
    n = len(pixels)
    for _ in range(3):
        idx = random.randint(0, n - 1)
        color = random.choice(FIREWORK_COLORS)
        pixels[idx] = color
        pixels.show()
        time.sleep(0.05)
        pixels[idx] = (0, 0, 0)
        pixels.show()


def rainbow_cycle(pixels, duration: float = 1.0) -> None:
    n = len(pixels)
    steps = 60
    for i in range(steps):
        for j in range(n):
            rc_index = (j * 256 // n + i * 5) % 256
            pixels[j] = wheel(rc_index)
        pixels.show()
        time.sleep(duration / steps)


def fade_to_color(pixels, color: Color, duration: float = 3.0) -> None:
    steps = 30
    for i in range(steps):
        level = i / steps
        pixels.fill(tuple(int(c * level) for c in color))
        pixels.show()
        time.sleep(duration / steps)
    # Guarantee we land exactly on the target color instead of stopping
    # one step short of it.
    pixels.fill(color)
    pixels.show()


def fade_burst(pixels, pixel_index: int, color: Color, duration: float = 0.5, steps: int = 15) -> None:
    for i in range(steps):
        brightness = 1 - (i / steps)
        pixels[pixel_index] = tuple(int(c * brightness) for c in color)
        pixels.show()
        time.sleep(duration / steps)
    pixels[pixel_index] = (0, 0, 0)
    pixels.show()


def water_ripple(
    pixels,
    low_color: Color = (6, 40, 66),
    high_color: Color = (120, 210, 220),
    duration: float = 20.0,
    speed: float = 0.6,
    fps: float = 30.0,
) -> None:
    """Smooth, continuously flowing ripple, like light reflecting off water.

    Owns its own timing and loops until `duration` elapses -- unlike the
    fixed-step effects above, this fits songs of any length (the special
    collection's songs run anywhere from ~10s to ~60s) at a consistent
    animation speed, rather than stretching/compressing a fixed step count.

    Two overlaid sine waves of different frequency and phase, rather than
    one, so the ring doesn't just pulse in unison -- it reads as a mild,
    organic ripple. `low_color` never actually goes fully dark by default,
    keeping the whole thing soft rather than flashing to black.
    """
    n = len(pixels)
    frame_delay = 1.0 / fps
    start = time.time()
    while time.time() - start < duration:
        t = time.time() - start
        for i in range(n):
            angle = (i / n) * 2 * math.pi
            wave = math.sin(angle + t * speed) * 0.7 + math.sin(angle * 2 - t * speed * 1.3) * 0.3
            level = max(0.0, min(1.0, (wave + 1) / 2))
            pixels[i] = tuple(
                int(low_color[c] + (high_color[c] - low_color[c]) * level)
                for c in range(3)
            )
        pixels.show()
        time.sleep(frame_delay)


def fireworks(pixels, num_bursts: int = 10, delay_between: float = 0.2) -> None:
    n = len(pixels)
    for _ in range(num_bursts):
        pixel = random.randint(0, n - 1)
        color = random.choice(FIREWORK_COLORS)
        pixels[pixel] = color
        pixels.show()
        fade_burst(pixels, pixel, color)
        time.sleep(delay_between)
