#!/usr/bin/env python3
"""Standalone smoke test for the audio chain: USB sound card -> amp -> speaker.

Confirms pygame can open the configured ALSA device and actually play a
real sound file from this project, independent of the RFID/LED pieces.
Reuses touchpoint/hardware.py's init_audio()/load_sound(), the same
code the real app uses, so a pass here means touch_point.py's audio
will work too.

Find your USB sound card's ALSA card/device index first:

    aplay -l

Then run, setting the device if it isn't the default plughw:2,0:

    TOUCHPOINT_AUDIO_DEVICE=plughw:1,0 sudo -E ~/touch_point/venv/bin/python hardware_checks/sound_test.py
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from touchpoint import config, hardware


def main() -> int:
    print(f"Opening audio: driver={config.AUDIO_DRIVER} device={config.AUDIO_DEVICE}")
    try:
        pygame = hardware.init_audio()
    except Exception as exc:
        print(f"FAILED to open audio device: {exc}")
        print("Run `aplay -l` to find your USB sound card's real card/device index,")
        print("then re-run with TOUCHPOINT_AUDIO_DEVICE=plughw:<card>,<device> set.")
        return 1

    sound_path = config.SOUND_DIR / "mb_accept.wav"
    print(f"Playing {sound_path} ...")
    try:
        sound = hardware.load_sound(pygame, sound_path)
    except Exception as exc:
        print(f"FAILED to load {sound_path}: {exc}")
        return 1

    channel = sound.play()
    while channel is not None and channel.get_busy():
        time.sleep(0.1)

    print("Done. If you heard the chime clearly through the speaker, the audio chain is good.")
    pygame.mixer.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
