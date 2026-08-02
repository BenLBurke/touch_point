"""Sound + LED-effect catalogue.

This module is pure data and logic: it knows which wav file and which
animation go with each tag scan, but never touches real audio or LED
hardware, so it can be unit tested on any machine.
"""
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
