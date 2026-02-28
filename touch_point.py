#!/usr/bin/env python3
"""
MagicBand / RFID-triggered audio + NeoPixel effects (Raspberry Pi)

Notes:
- Forces pygame/SDL to use ALSA and your USB device (card 2, device 0).
- Uses relative paths safely by cd'ing to this script's directory.
- Initializes pygame mixer once (with pre_init for stability).
- Logs to touch_point.log and prints scan IDs.
"""

import os

# --- MUST BE SET BEFORE IMPORTING pygame ---
os.environ["SDL_AUDIODRIVER"] = "alsa"
os.environ["AUDIODEV"] = "plughw:2,0"  # USB audio: card 2, device 0

# Ensure relative paths work no matter where you launch from
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import logging
import random
import time

import board
import neopixel
import pygame
from mfrc522 import SimpleMFRC522


# ----------------------------
# Logging
# ----------------------------
logging.basicConfig(
    filename="touch_point.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
)


# ----------------------------
# NeoPixel Setup
# ----------------------------
NUM_PIXELS = 48
PIXEL_PIN = board.D18  # GPIO18
pixels = neopixel.NeoPixel(PIXEL_PIN, NUM_PIXELS, brightness=0.4, auto_write=False)

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


# ----------------------------
# Audio Setup (pygame)
# ----------------------------
pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
pygame.mixer.init()

def load_sound(path: str, volume: float = 1.0) -> pygame.mixer.Sound:
    """Load a WAV and set volume (0.0 to 1.0)."""
    s = pygame.mixer.Sound(path)
    s.set_volume(volume)
    return s

# Tap sound
tap_sound = load_sound("sound_files/mb_accept.wav", volume=1.0)

# Library of songs/effects
ALL_SOUNDS = [
    {"name": "progress",     "song": load_sound("sound_files/progress.wav", volume=1.0),         "length": 7},
    {"name": "haunted",      "song": load_sound("sound_files/haunted.wav", volume=1.0),          "length": 5},
    {"name": "monorail",     "song": load_sound("sound_files/monorail.wav", volume=1.0),         "length": 7},
    {"name": "small_world",  "song": load_sound("sound_files/small_world.wav", volume=1.0),      "length": 5},
    {"name": "pirates",      "song": load_sound("sound_files/pirates.wav", volume=1.0),          "length": 4},
    {"name": "happily",      "song": load_sound("sound_files/happily.wav", volume=1.0),          "length": 7},
    {"name": "mickey",       "song": load_sound("sound_files/m_i_c_k_e_y.wav", volume=1.0),      "length": 4},
    {"name": "force",        "song": load_sound("sound_files/yoda_force.wav", volume=1.0),       "length": 9},
    {"name": "stop_us",      "song": load_sound("sound_files/stop_us_now.wav", volume=1.0),      "length": 7},
    {"name": "tiki",         "song": load_sound("sound_files/tiki_room_cut2.wav", volume=1.0),   "length": 13},
    {"name": "saddle",       "song": load_sound("sound_files/blood-on-the-saddle_cut.wav", volume=1.0), "length": 14},
]


# ----------------------------
# RFID Reader
# ----------------------------
reader = SimpleMFRC522()


# ----------------------------
# Helpers / Effects
# ----------------------------
def play_sound(snd: pygame.mixer.Sound) -> None:
    snd.play()

def clear_pixels() -> None:
    pixels.fill((0, 0, 0))
    pixels.show()

def wheel(pos: int) -> tuple[int, int, int]:
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return (255 - pos * 3, pos * 3, 0)
    if pos < 170:
        pos -= 85
        return (0, 255 - pos * 3, pos * 3)
    pos -= 170
    return (pos * 3, 0, 255 - pos * 3)

def comet(color: tuple[int, int, int], tail_length: int = 12, delay: float = 0.03) -> None:
    for i in range(NUM_PIXELS + tail_length):
        pixels.fill((0, 0, 0))
        for j in range(tail_length):
            idx = (i - j) % NUM_PIXELS
            brightness = (tail_length - j) / tail_length
            pixels[idx] = tuple(int(c * brightness) for c in color)
        pixels.show()
        time.sleep(delay)

def burst() -> None:
    for _ in range(3):
        idx = random.randint(0, NUM_PIXELS - 1)
        color = random.choice(FIREWORK_COLORS)
        pixels[idx] = color
        pixels.show()
        time.sleep(0.05)
        pixels[idx] = (0, 0, 0)
        pixels.show()

def rainbow_cycle(duration: float = 1.0) -> None:
    steps = 60
    for i in range(steps):
        for j in range(NUM_PIXELS):
            rc_index = (j * 256 // NUM_PIXELS + i * 5) % 256
            pixels[j] = wheel(rc_index)
        pixels.show()
        time.sleep(duration / steps)

def fade_to_color(color: tuple[int, int, int], duration: float = 3.0) -> None:
    steps = 30
    for i in range(steps):
        level = i / steps
        current_color = tuple(int(c * level) for c in color)
        pixels.fill(current_color)
        pixels.show()
        time.sleep(duration / steps)

def fade_burst(pixel_index: int, color: tuple[int, int, int], duration: float = 0.5, steps: int = 15) -> None:
    for i in range(steps):
        brightness = 1 - (i / steps)
        pixels[pixel_index] = tuple(int(c * brightness) for c in color)
        pixels.show()
        time.sleep(duration / steps)
    pixels[pixel_index] = (0, 0, 0)
    pixels.show()

def fireworks(num_bursts: int = 10, delay_between: float = 0.2) -> None:
    for _ in range(num_bursts):
        pixel = random.randint(0, NUM_PIXELS - 1)
        color = random.choice(FIREWORK_COLORS)
        pixels[pixel] = color
        pixels.show()
        fade_burst(pixel, color)
        time.sleep(delay_between)


# ----------------------------
# Main Loop
# ----------------------------
def main() -> None:
    print("Ready to scan MagicBand...")

    while True:
        choice = random.choice(ALL_SOUNDS)
        logging.info("Chosen sound %s", choice["name"])

        choice_name = choice["name"]
        success_sound = choice["song"]
        sound_length = choice["length"]

        # Idle glow
        pixels.fill((50, 50, 50))
        pixels.show()

        # Block until RFID scan
        card_id, _text = reader.read()
        print(f"Scanned MagicBand ID: {card_id}")
        logging.info("Scanned MagicBand ID: %s", card_id)

        # Tap confirmation
        play_sound(tap_sound)

        # Visual + main sound
        comet((0, 0, 255))  # blue comet
        time.sleep(1)

        play_sound(success_sound)

        if choice_name == "haunted":
            fade_to_color((157, 0, 255), duration=sound_length)  # purple
        elif choice_name in ("pirates", "saddle"):
            fade_to_color((255, 0, 0), duration=sound_length)    # red
        elif choice_name == "monorail":
            fade_to_color((255, 255, 0), duration=sound_length)  # yellow
        elif choice_name == "happily":
            fireworks()
        elif choice_name in ("mickey", "tiki"):
            fade_to_color((255, 0, 0), duration=2)
            fade_to_color((255, 255, 0), duration=2)
        elif choice_name == "stop_us":
            start = time.time()
            while time.time() - start < 9:
                comet(random.choice(FIREWORK_COLORS), tail_length=8, delay=0.03)
                burst()
                rainbow_cycle(duration=1)
        else:
            fade_to_color((0, 255, 0), duration=sound_length)    # green

        time.sleep(1)
        fade_to_color((50, 50, 50), duration=2)  # back to idle


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Stopped.")
        logging.info("Keyboard Interrupt")
    except Exception:
        logging.exception("Unhandled error")
        raise
    finally:
        try:
            clear_pixels()
        except Exception:
            pass
        try:
            pygame.mixer.quit()
        except Exception:
            pass
