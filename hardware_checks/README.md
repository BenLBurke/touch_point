# Hardware checks

Small, standalone scripts for bringing up and sanity-checking one piece
of physical hardware at a time. They require real hardware attached to
a Raspberry Pi (or, for `pico_pn532/`, a MicroPython board) and are run
manually -- they are **not** part of the automated `pytest` suite in
`tests/`.

- `led_test.py` -- cycles the NeoPixel ring through red/green/blue.
- `comet.py` -- spins a comet-tail animation on the ring.
- `rfid_test.py` -- reads and prints RFID tag IDs in a loop.
- `sound_test.py` -- plays a WAV to confirm the audio output is wired up.
- `tag_pixels_test.py` -- combined RFID + LED demo (non-blocking read).
- `pico_pn532/` -- an earlier prototype using a PN532 NFC module driven
  from MicroPython on a separate microcontroller (e.g. a Pi Pico), not
  the RC522 + Raspberry Pi setup `touch_point.py` uses today. Kept for
  reference.

Run any of them the same way you'd run `touch_point.py`, e.g.:

```bash
sudo ~/touch_point/venv/bin/python hardware_checks/led_test.py
```
