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

firework_colors = [
    (255, 0, 0),      # red
    (255, 140, 0),    # orange
    (255, 255, 0),    # yellow
    (255, 255, 255),  # white
    (0, 0, 255),      # blue
    (128, 0, 128),    # purple
    (255, 20, 147),   # pink
]

# Sound Setup
pygame.mixer.init()
tap_sound = pygame.mixer.Sound("sound_files/mb_accept.wav")
all_sounds = [{'name':   'progress', 'song':     pygame.mixer.Sound("sound_files/progress.wav"), 'length': 7}
              , {'name': 'haunted',  'song':     pygame.mixer.Sound("sound_files/haunted.wav"), 'length': 5}
              , {'name': 'monorail', 'song':     pygame.mixer.Sound("sound_files/monorail.wav"), 'length': 7}
              , {'name': 'small_world', 'song':  pygame.mixer.Sound("sound_files/small_world.wav"), 'length':5}
              , {'name': 'pirates', 'song':      pygame.mixer.Sound("sound_files/pirates.wav"), 'length': 4}
              , {'name': 'happily', 'song':      pygame.mixer.Sound("sound_files/happily.wav"), 'length': 7}
              , {'name': 'mickey', 'song':      pygame.mixer.Sound("sound_files/m_i_c_k_e_y.wav"), 'length': 4}
              , {'name': 'force', 'song':      pygame.mixer.Sound("sound_files/force.wav"), 'length': 9}
             ]



# RFID Reader
reader = SimpleMFRC522()

# --- FUNCTIONS ---

def play_sound(sound):
    pygame.mixer.Sound.play(sound)

def clear_pixels():
    pixels.fill((0, 0, 0))
    pixels.show()

def comet(color, tail_length=12, delay=0.03):
    for i in range(NUM_PIXELS + tail_length):
        clear_pixels()  # Clear before drawing the comet to avoid flicker
        for j in range(tail_length):
            idx = (i - j) % NUM_PIXELS  # Wrap around the ring
            brightness = (tail_length - j) / tail_length  # Linear fade
            faded_color = tuple(int(c * brightness) for c in color)
            pixels[idx] = faded_color
        pixels.show()
        time.sleep(delay)


def fade_to_color(color, duration=3):
    steps = 30
    for i in range(steps):
        level = i / steps
        current_color = tuple(int(c * level) for c in color)
        pixels.fill(current_color)
        pixels.show()
        time.sleep(duration / steps)

def fade_burst(pixel_index, color, duration=0.5, steps=15):
    for i in range(steps):
        brightness = 1 - (i / steps)
        faded_color = tuple(int(c * brightness) for c in color)
        pixels[pixel_index] = faded_color
        pixels.show()
        time.sleep(duration / steps)
    pixels[pixel_index] = (0, 0, 0)
    pixels.show()

def fireworks(num_bursts=10, delay_between=0.2):
    for _ in range(num_bursts):
        pixel = random.randint(0, NUM_PIXELS - 1)
        color = random.choice(firework_colors)
        pixels[pixel] = color
        pixels.show()
        fade_burst(pixel, color)
        time.sleep(delay_between)

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
        elif choice_name == 'happily':
            fireworks()
        elif choice_name == 'mickey':
            fade_to_color((255, 0, 0), duration=2) #red
            fade_to_color((255, 255, 0), duration=2) #yellow
        else:
            fade_to_color((0, 255, 0), duration=sound_length)  # Fade to green
        time.sleep(1)
        fade_to_color((50, 50, 50), duration=2)  # Fade back to soft white

except KeyboardInterrupt:
    print("Stopped.")
finally:
    clear_pixels()
    pygame.mixer.quit()
