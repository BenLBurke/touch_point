#!/usr/bin/env python3
"""MagicBand / RFID-triggered audio + NeoPixel effects (Raspberry Pi).

Run with:
    sudo ~/touch_point/venv/bin/python touch_point.py

Behavior is tuned via environment variables (see touchpoint/config.py),
so the same code runs unmodified on a Pi 3/4/5 or a Pi Zero W / Zero 2 W
-- see README.md for per-model notes.
"""
import logging
import os
import random
import signal
import time

# Ensure relative paths (sound_files/, the log file) work no matter
# where the process is launched from (pm2, cron, an interactive shell...).
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from touchpoint import config, effects, hardware
from touchpoint.sounds import SOUND_LIBRARY, TAP_SOUND_FILENAME, effect_for

logging.basicConfig(
    filename=str(config.LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
)
logger = logging.getLogger(__name__)


class Shutdown(Exception):
    """Raised from the SIGTERM handler so the main loop can unwind and
    clean up hardware state. pm2 stop/restart sends SIGTERM."""


def _handle_sigterm(signum, frame):
    raise Shutdown()


def run_effect(pixels, plan: dict) -> None:
    if plan["type"] == "fade":
        effects.fade_to_color(pixels, plan["color"], duration=plan["duration"])
    elif plan["type"] == "double_fade":
        for color in plan["colors"]:
            effects.fade_to_color(pixels, color, duration=plan["duration"])
    elif plan["type"] == "fireworks":
        effects.fireworks(pixels)
    elif plan["type"] == "chaos":
        start = time.time()
        while time.time() - start < plan["duration"]:
            effects.comet(pixels, random.choice(effects.FIREWORK_COLORS), tail_length=8, delay=0.03)
            effects.burst(pixels)
            effects.rainbow_cycle(pixels, duration=1)
    elif plan["type"] == "hop":
        effects.hop(pixels, plan["color"], duration=plan["duration"])
    elif plan["type"] == "parade":
        effects.parade(pixels, plan["colors"], duration=plan["duration"])
    elif plan["type"] == "swirl":
        effects.swirl(pixels, *plan["colors"], duration=plan["duration"])
    else:
        raise ValueError(f"Unknown effect type: {plan['type']!r}")


def open_speaker():
    """Reopen the speaker, or return None (lights only) if it's missing."""
    try:
        return hardware.init_audio()
    except Exception:
        logger.exception("Speaker unavailable; playing lights only")
        return None


def play_sound(pygame_module, filename):
    """Load and start a clip. Returns the Sound (keep a reference while it
    plays), or None if there's no speaker or the clip fails to load."""
    if pygame_module is None:
        return None
    try:
        sound = hardware.load_sound(pygame_module, config.SOUND_DIR / filename)
        sound.play()
        return sound
    except Exception:
        logger.exception("Could not play %s", filename)
        return None


def main() -> None:
    pixels = hardware.init_pixels()
    reader = hardware.init_reader()
    # Opened once here only so the log shows the speaker status at boot;
    # it's reopened on every tap below.
    pygame_module = open_speaker()

    for clip in SOUND_LIBRARY:
        if not (config.SOUND_DIR / clip.filename).exists():
            logger.warning("Missing sound file: %s", clip.filename)

    print("Ready to scan MagicBand...")

    try:
        while True:
            clip = random.choice(SOUND_LIBRARY)
            logger.info("Chosen sound %s", clip.name)

            # Idle glow
            pixels.fill(config.IDLE_COLOR)
            pixels.show()

            # Block until RFID scan. A transient read error shouldn't take
            # down the whole process -- log it and keep waiting for a tag.
            try:
                card_id, _text = reader.read()
            except Exception:
                logger.exception("RFID read failed, retrying")
                time.sleep(1)
                continue

            print(f"Scanned MagicBand ID: {card_id}")
            logger.info("Scanned MagicBand ID: %s", card_id)

            try:
                # Free the last tap's sounds while their mixer is still
                # open, then reopen the speaker in case it reconnected.
                tap_sound = song = None
                pygame_module = open_speaker()
                tap_sound = play_sound(pygame_module, TAP_SOUND_FILENAME)

                effects.comet(pixels, config.TAP_COLOR)
                time.sleep(1)

                song = play_sound(pygame_module, clip.filename)
                run_effect(pixels, effect_for(clip.name, clip.length))

                time.sleep(1)
                effects.fade_to_color(pixels, config.IDLE_COLOR, duration=2)
            except (KeyboardInterrupt, Shutdown):
                raise
            except Exception:
                logger.exception("Effect playback failed for %s", clip.name)
    finally:
        try:
            effects.clear_pixels(pixels)
        except Exception:
            logger.exception("Failed to clear pixels during shutdown")
        try:
            if pygame_module is not None:
                pygame_module.mixer.quit()
        except Exception:
            logger.exception("Failed to quit audio mixer during shutdown")


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, _handle_sigterm)
    try:
        main()
    except (KeyboardInterrupt, Shutdown):
        print("Stopped.")
        logger.info("Stopped (signal)")
    except Exception:
        logger.exception("Unhandled error")
        raise
