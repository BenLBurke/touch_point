import time
import board
import neopixel
from mfrc522 import SimpleMFRC522

# === Configuration ===
NUM_PIXELS = 48
PIN = board.D18
BRIGHTNESS = 0.4
TAIL_LENGTH = 6
IDLE_COLOR = (255, 255, 255)  # White
TAP_COLOR = (0, 0, 255)       # Blue
FINAL_COLOR = (0, 255, 0)     # Green

pixels = neopixel.NeoPixel(PIN, NUM_PIXELS, brightness=BRIGHTNESS, auto_write=False)
reader = SimpleMFRC522()

def dim_color(color, factor):
    return tuple(int(c * factor) for c in color)

def spin_tail(color, tail_len, speed=0.05, duration=None):
    """Spin tail animation for a given duration (or infinite if None)."""
    position = 0
    start_time = time.time()
    while True:
        pixels.fill((0, 0, 0))
        for i in range(tail_len):
            idx = (position - i) % NUM_PIXELS
            fade = (tail_len - i) / tail_len
            pixels[idx] = dim_color(color, fade)
        pixels.show()
        time.sleep(speed)
        position = (position + 1) % NUM_PIXELS

        if duration and time.time() - start_time > duration:
            break

def solid_fill(color, duration):
    pixels.fill(color)
    pixels.show()
    time.sleep(duration)

def run():
    print("Place your MagicBand near the reader...")
    try:
        while True:
            # Start idle animation
            spin_tail(IDLE_COLOR, TAIL_LENGTH, speed=0.05, duration=0.1)  # Loop in slices

            # Check for RFID card (non-blocking way)
            id, text = reader.read_no_block()
            if id:
                print(f"Tag detected: {id} – {text}")
                # Blue comet animation
                spin_tail(TAP_COLOR, TAIL_LENGTH, speed=0.03, duration=3)
                # Green solid fill
                solid_fill(FINAL_COLOR, 3)
                # Then return to idle (loop continues)

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        pixels.fill((0, 0, 0))
        pixels.show()
run()
