"""Real hardware bring-up: NeoPixel ring, RFID reader, and audio.

Every hardware library is imported lazily, inside these functions, not
at module import time. That means ``touchpoint.hardware`` -- and the
pure ``touchpoint.effects`` / ``touchpoint.sounds`` modules it sits on
top of -- can be imported and unit tested on a regular dev machine with
no Blinka/SPI/audio hardware attached: tests simply put fake modules in
``sys.modules`` before calling these functions.
"""
import logging
import os

from . import config, sounds

logger = logging.getLogger(__name__)


def init_pixels():
    import board
    import neopixel

    pin = getattr(board, config.PIXEL_PIN_NAME)
    pixels = neopixel.NeoPixel(
        pin, config.NUM_PIXELS, brightness=config.BRIGHTNESS, auto_write=False
    )
    logger.info("NeoPixel ring ready: %d pixels on %s", config.NUM_PIXELS, config.PIXEL_PIN_NAME)
    return pixels


def init_reader():
    from mfrc522 import SimpleMFRC522

    reader = SimpleMFRC522()
    logger.info("RFID reader ready")
    return reader


def init_audio():
    # Must be set before pygame/SDL touches the audio subsystem.
    os.environ["SDL_AUDIODRIVER"] = config.AUDIO_DRIVER
    os.environ["AUDIODEV"] = config.AUDIO_DEVICE

    import pygame

    pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
    pygame.mixer.init()
    logger.info("Audio ready: driver=%s device=%s", config.AUDIO_DRIVER, config.AUDIO_DEVICE)
    return pygame


def load_sound(pygame_module, path, volume: float = None):
    """Load a WAV and set its volume (0.0 to 1.0). Defaults to config.VOLUME."""
    if volume is None:
        volume = config.VOLUME
    sound = pygame_module.mixer.Sound(str(path))
    sound.set_volume(volume)
    return sound


def _load_library(pygame_module, clips):
    return {
        clip.name: {
            "song": load_sound(pygame_module, config.SOUND_DIR / clip.filename),
            "length": clip.length,
        }
        for clip in clips
    }


def load_all_sounds(pygame_module):
    """Load the tap sound, the main library, and the special-card library.

    Returns (tap_sound, {name: {"song": Sound, "length": int}}, {same shape, special collection}).
    """
    tap_sound = load_sound(pygame_module, config.SOUND_DIR / sounds.TAP_SOUND_FILENAME)
    library = _load_library(pygame_module, sounds.SOUND_LIBRARY)
    special_library = _load_library(pygame_module, sounds.SPECIAL_SOUND_LIBRARY)
    return tap_sound, library, special_library
