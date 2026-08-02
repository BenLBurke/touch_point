import board
import neopixel
import time

pixels = neopixel.NeoPixel(board.D18, 8, brightness=0.3, auto_write=True)

while True:
    pixels.fill((255, 0, 0))  # Red
    time.sleep(1)
    pixels.fill((0, 255, 0))  # Green
    time.sleep(1)
    pixels.fill((0, 0, 255))  # Blue
    time.sleep(1)
