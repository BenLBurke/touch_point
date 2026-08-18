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
from logging.handlers import RotatingFileHandler

# Ensure relative paths (sound_files/, the log file) work no matter
# where the process is launched from (pm2, cron, an interactive shell...).
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from touchpoint import config, effects, hardware
from touchpoint.sounds import choose_sound, effect_for

# RotatingFileHandler, not basicConfig(filename=...), so the log can't
# grow unbounded on a device meant to run for months unattended.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    handlers=[
        RotatingFileHandler(
            str(config.LOG_FILE),
            maxBytes=config.LOG_MAX_BYTES,
            backupCount=config.LOG_BACKUP_COUNT,
        )
    ],
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
    else:
        raise ValueError(f"Unknown effect type: {plan['type']!r}")


def main() -> None:
    pixels = hardware.init_pixels()
    reader = hardware.init_reader()
    pygame_module = hardware.init_audio()
    tap_sound, sound_library, special_sound_library = hardware.load_all_sounds(pygame_module)

    if config.SPECIAL_CARD_ID and not special_sound_library:
        logger.warning(
            "TOUCHPOINT_SPECIAL_CARD_ID is set but SPECIAL_SOUND_LIBRARY in "
            "touchpoint/sounds.py is empty -- that card will behave like any other."
        )

    print("Ready to scan MagicBand...")

    try:
        while True:
            # Idle glow -- alternating pixels, not a full fill, to cut
            # idle power draw roughly in half (see effects.alternating_fill).
            effects.alternating_fill(pixels, config.IDLE_COLOR)

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

            # Which song plays depends on which card this is -- the one
            # configured special card draws from its own collection.
            name, sound, is_special = choose_sound(card_id, sound_library, special_sound_library)
            logger.info("Chosen sound %s%s", name, " (special)" if is_special else "")

            try:
                tap_sound.play()

                effects.comet(pixels, config.TAP_COLOR)
                time.sleep(1)

                sound["song"].play()
                if is_special:
                    effects.water_ripple(pixels, duration=sound["length"])
                    time.sleep(1)
                    # Cross-fade from the ripple's own dim ending color
                    # instead of fade_to_color's snap-to-black start, so
                    # the whole special-card sequence stays soft to the end.
                    effects.fade_pixels_to(pixels, config.IDLE_COLOR, duration=2)
                else:
                    run_effect(pixels, effect_for(name, sound["length"]))
                    time.sleep(1)
                    effects.fade_to_color(pixels, config.IDLE_COLOR, duration=2)
            except (KeyboardInterrupt, Shutdown):
                raise
            except Exception:
                logger.exception("Effect playback failed for %s", name)
    finally:
        try:
            effects.clear_pixels(pixels)
        except Exception:
            logger.exception("Failed to clear pixels during shutdown")
        try:
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
