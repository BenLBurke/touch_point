#!/usr/bin/env python3
"""Standalone smoke test for the WS2812B/NeoPixel ring.

Cycles the whole ring through red/green/blue so you can confirm DIN,
5V, and GND are wired correctly before running the full touch point.
Uses the same pixel count / data pin as the real app (touchpoint/config.py),
so set TOUCHPOINT_NUM_PIXELS first if your ring isn't the default 48:

    TOUCHPOINT_NUM_PIXELS=24 sudo -E ~/touch_point/venv/bin/python hardware_checks/led_test.py

Ctrl+C to stop.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import board
import neopixel

from touchpoint import config

pin = getattr(board, config.PIXEL_PIN_NAME)
pixels = neopixel.NeoPixel(pin, config.NUM_PIXELS, brightness=0.3, auto_write=True)

print(f"Cycling {config.NUM_PIXELS} pixels on {config.PIXEL_PIN_NAME} (Ctrl+C to stop)...")

try:
    while True:
        pixels.fill((255, 0, 0))  # Red
        time.sleep(1)
        pixels.fill((0, 255, 0))  # Green
        time.sleep(1)
        pixels.fill((0, 0, 255))  # Blue
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopped.")
finally:
    pixels.fill((0, 0, 0))
    pixels.show()
