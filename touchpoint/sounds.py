"""Sound + LED-effect catalogue.

This module is pure data and logic: it knows which wav file and which
animation go with each tag scan, but never touches real audio or LED
hardware, so it can be unit tested on any machine.
"""
import random
from dataclasses import dataclass

PURPLE = (157, 0, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)

TAP_SOUND_FILENAME = "mb_accept.wav"


@dataclass(frozen=True)
class SoundClip:
    name: str
    filename: str
    length: int  # seconds; used as the default fade duration


SOUND_LIBRARY = (
    SoundClip("progress", "progress.wav", 7),
    SoundClip("haunted", "haunted.wav", 5),
    SoundClip("monorail", "monorail.wav", 7),
    SoundClip("small_world", "small_world.wav", 5),
    SoundClip("pirates", "pirates.wav", 4),
    SoundClip("happily", "happily.wav", 7),
    SoundClip("mickey", "m_i_c_k_e_y.wav", 4),
    SoundClip("force", "yoda_force.wav", 9),
    SoundClip("stop_us", "stop_us_now.wav", 7),
    SoundClip("tiki", "tiki_room_cut2.wav", 13),
    SoundClip("saddle", "blood-on-the-saddle_cut.wav", 14),
)

# Sounds that just fade the ring to a fixed color for the sound's length.
_FADE_COLORS = {
    "haunted": PURPLE,
    "pirates": RED,
    "saddle": RED,
    "monorail": YELLOW,
}

# Sounds that fade through two fixed colors instead of one.
_DOUBLE_FADE_NAMES = {"mickey", "tiki"}

DEFAULT_EFFECT_COLOR = GREEN


def effect_for(name: str, length: int) -> dict:
    """Return a plan describing which animation to play for a sound.

    Plan shapes:
      {"type": "fade", "color": (r, g, b), "duration": seconds}
      {"type": "double_fade", "colors": [(r, g, b), (r, g, b)], "duration": seconds}
      {"type": "fireworks"}
      {"type": "chaos", "duration": seconds}
    """
    if name in _FADE_COLORS:
        return {"type": "fade", "color": _FADE_COLORS[name], "duration": length}
    if name == "happily":
        return {"type": "fireworks"}
    if name in _DOUBLE_FADE_NAMES:
        return {"type": "double_fade", "colors": [RED, YELLOW], "duration": 2}
    if name == "stop_us":
        return {"type": "chaos", "duration": 9}
    return {"type": "fade", "color": DEFAULT_EFFECT_COLOR, "duration": length}


def find_clip(name: str):
    for clip in SOUND_LIBRARY:
        if clip.name == name:
            return clip
    return None


# Songs played only for one specific card (see TOUCHPOINT_SPECIAL_CARD_ID
# in touchpoint/config.py), each getting the "water" light show
# (touchpoint.effects.water_ripple) instead of the normal name-based
# mapping above. Add your own entries here, same shape as SOUND_LIBRARY:
#
#   SoundClip("ariel", "part_of_your_world.wav", 45),
#
SPECIAL_SOUND_LIBRARY = (
    SoundClip("william1", "william1_music.wav", 30),
    SoundClip("william2", "william2_music.wav", 25),
    SoundClip("william3", "william3_music.wav", 29),
    SoundClip("ben", "ben_music.wav", 67),
    SoundClip("kyrstin", "kyrstin_music.wav", 45),
    SoundClip("chalene", "chalene_music.wav", 45),
    SoundClip("matthew", "matthew_music.wav", 20),
)


def choose_sound(card_id, sound_library: dict, special_sound_library: dict):
    """Pick a (name, sound_entry, is_special) tuple for a scanned card.

    sound_library / special_sound_library are {name: {"song": ..., "length": ...}}
    dicts, e.g. what touchpoint.hardware.load_all_sounds() returns. Falls
    back to the normal library if the card doesn't match the configured
    special card, or if the special collection is empty (nothing added
    yet) even when the card does match -- so an incomplete setup degrades
    to normal behavior instead of crashing. `is_special` tells the caller
    whether to play the water effect instead of the usual name-based one.
    """
    from . import config

    is_special_card = bool(config.SPECIAL_CARD_ID) and str(card_id) == config.SPECIAL_CARD_ID
    if is_special_card and special_sound_library:
        name, sound = random.choice(list(special_sound_library.items()))
        return name, sound, True
    name, sound = random.choice(list(sound_library.items()))
    return name, sound, False
