import time
import board
import neopixel
import pygame
from mfrc522 import SimpleMFRC522

# --- SETUP ---

# NeoPixel Setup
NUM_PIXELS = 48
PIXEL_PIN = board.D18
pixels = neopixel.NeoPixel(PIXEL_PIN, NUM_PIXELS, brightness=0.4, auto_write=False)

# Sound Setup
# pygame.mixer.init()
# tap_sound = pygame.mixer.Sound("sounds_files/mb_accept.wav")
# success_sound = pygame.mixer.Sound("sounds_files/progress.wav")

# RFID Reader
reader = SimpleMFRC522()

# --- FUNCTIONS ---

def play_sound(sound):
    pygame.mixer.Sound.play(sound)

def clear_pixels():
    pixels.fill((0, 0, 0))
    pixels.show()

def comet(color, tail_length=6, delay=0.03):
    for i in range(NUM_PIXELS + tail_length):
        for j in range(tail_length):
            idx = i - j
            if 0 <= idx < NUM_PIXELS:
                brightness = 1 - (j / tail_length)
                faded_color = tuple(int(c * brightness) for c in color)
                pixels[idx] = faded_color
        pixels.show()
        time.sleep(delay)
        clear_pixels()

def fade_to_color(color, duration=3):
    steps = 30
    for i in range(steps):
        level = i / steps
        current_color = tuple(int(c * level) for c in color)
        pixels.fill(current_color)
        pixels.show()
        time.sleep(duration / steps)

# --- MAIN LOOP ---

print("Ready to scan RFID...")

try:
    while True:
        pixels.fill((50, 50, 50))  # Soft white idle glow
        pixels.show()

        id, text = reader.read()
        print(f"Scanned ID: {id}")

        # play_sound(tap_sound)

        comet((0, 0, 255))  # Blue comet
        # play_sound(success_sound)

        fade_to_color((0, 255, 0), duration=3)  # Fade to green
        time.sleep(1)
        fade_to_color((50, 50, 50), duration=2)  # Fade back to soft white

except KeyboardInterrupt:
    print("Stopped.")
finally:
    clear_pixels()
    pygame.mixer.quit()
