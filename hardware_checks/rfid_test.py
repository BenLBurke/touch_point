#!/usr/bin/env python3
"""Standalone smoke test for the RC522 RFID reader.

Confirms the reader initializes over SPI and can read tags reliably,
independent of the rest of the touch point (no LEDs, no audio). Run
this first after wiring up a new reader:

    sudo ~/touch_point/venv/bin/python hardware_checks/rfid_test.py

Expected: an "initialized" message, then after tapping a tag, its
numeric ID printed back within a second or two. Tap a few different
tags, and the same tag a few times, to confirm reads are consistent
-- not just a single lucky read. Ctrl+C to stop.
"""
import sys

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522


def main() -> int:
    print("Initializing RC522 over SPI...")
    try:
        reader = SimpleMFRC522()
    except Exception as exc:
        print(f"FAILED to initialize reader: {exc}")
        print("Check: SPI enabled (raspi-config), wiring matches README.md, reader has 3.3V power (not 5V).")
        return 1

    print("Reader initialized. Place a tag near the reader (Ctrl+C to stop)...")

    scan_count = 0
    try:
        while True:
            try:
                card_id, text = reader.read()
            except Exception as exc:
                print(f"Read error: {exc}")
                continue
            scan_count += 1
            print(f"[{scan_count}] OK - ID: {card_id}  Text: {text.strip()!r}")
    except KeyboardInterrupt:
        print(f"\nStopped after {scan_count} successful scan(s).")
    finally:
        GPIO.cleanup()

    return 0 if scan_count > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
