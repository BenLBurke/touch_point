import time
import board
import neopixel

NUM_PIXELS = 16        # Update this to match your ring
TAIL_LENGTH = 6        # How long the trail should be
COLOR = (255, 100, 0)  # Orange color (you can change this)
SPEED = 0.05           # Lower = faster

pixels = neopixel.NeoPixel(board.D18, NUM_PIXELS, brightness=0.4, auto_write=False)

def dim_color(color, factor):
    return tuple(int(c * factor) for c in color)

def spin_tail():
    position = 0
    while True:
        pixels.fill((0, 0, 0))  # Clear strip each time

        for i in range(TAIL_LENGTH):
            idx = (position - i) % NUM_PIXELS
            fade = (TAIL_LENGTH - i) / TAIL_LENGTH
            pixels[idx] = dim_color(COLOR, fade)

        pixels.show()
        time.sleep(SPEED)
        position = (position + 1) % NUM_PIXELS

try:
    spin_tail()
except KeyboardInterrupt:
    pixels.fill((0, 0, 0))
    pixels.show()
except Exceptional as e:
    print(e)
