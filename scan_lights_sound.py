import time
import random

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
pygame.mixer.init()
tap_sound = pygame.mixer.Sound("sound_files/mb_accept.wav")
all_sounds = [{'name':   'progress', 'song':     pygame.mixer.Sound("sound_files/progress.wav"), 'length': 7}
              , {'name': 'haunted',  'song':     pygame.mixer.Sound("sound_files/haunted.wav")}, 'length': 5}
              , {'name': 'monorail', 'song':     pygame.mixer.Sound("sound_files/monorail.wav"), 'lenth': 7}
              , {'name': 'small_world', 'song':  pygame.mixer.Sound("sound_files/small_world.wav"), 'length':5}
              , {'name': 'pirates', 'song':      pygame.mixer.Sound("sound_files/pirates.wav"), 'length': 4}
             ]



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

print("Ready to scan MagicBand...")

try:
    while True:
        #choose a song
        choice = random.choice(all_sounds)
        choice_name = choice['name']
        success_sound = choice['song']
        sound_length = choice['length']
      
        pixels.fill((50, 50, 50))  # Soft white idle glow
        pixels.show()

        id, text = reader.read()
        print(f"Scanned MagicBand ID: {id}")

        play_sound(tap_sound)

        comet((0, 0, 255))  # Blue comet
        time.sleep(1)
        play_sound(success_sound)
        if choice_name == 'haunted':
            fade_to_color((157, 0, 255), duration=sound_length) # Fade to purple
        elif choice_name == 'pirates':
            fade_to_color((255, 0, 0), duration=sound_length) #red
        elif choice_name == 'monorail':
            fade_to_color((255, 255, 0), duration=sound_length) #yellow
        else:
            fade_to_color((0, 255, 0), duration=sound_length)  # Fade to green
        time.sleep(1)
        fade_to_color((50, 50, 50), duration=2)  # Fade back to soft white

except KeyboardInterrupt:
    print("Stopped.")
finally:
    clear_pixels()
    pygame.mixer.quit()
