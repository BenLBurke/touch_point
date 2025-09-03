import board
import neopixel
import pygame
from mfrc522 import SimpleMFRC522

import logging
import time
import random

logging.basicConfig(
    filename='touch_point.log',       # Log file path
    level=logging.INFO,         # Minimum level to log
    format='%(asctime)s %(levelname)s:%(message)s'
)

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
    (75, 0, 130),   # indigo
    (255, 20, 147),   # pink
]

pygame.mixer.init()

def load_sound(path, volume=1.0):
    """Load a sound and set its volume (0.0 to 1.0)."""
    sound = pygame.mixer.Sound(path)
    sound.set_volume(volume)
    return sound

# Sound Setup
pygame.mixer.init()
tap_sound = pygame.mixer.Sound("sound_files/mb_accept.wav")
all_sounds = [{'name':   'progress', 'song':     load_sound("sound_files/progress.wav"), 'length': 7}
              , {'name': 'haunted',  'song':     load_sound("sound_files/haunted.wav"), 'length': 5}
              , {'name': 'monorail', 'song':     load_sound("sound_files/monorail.wav"), 'length': 7}
              , {'name': 'small_world', 'song':  load_sound("sound_files/small_world.wav"), 'length':5}
              , {'name': 'pirates', 'song':      load_sound("sound_files/pirates.wav"), 'length': 4}
              , {'name': 'happily', 'song':      load_sound("sound_files/happily.wav"), 'length': 7}
              , {'name': 'mickey', 'song':       load_sound("sound_files/m_i_c_k_e_y.wav"), 'length': 4}
              , {'name': 'force', 'song':        load_sound("sound_files/yoda_force.wav"), 'length': 9}
              , {'name': 'stop_us', 'song':      load_sound("sound_files/stop_us_now.wav"), 'length': 7}
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

def burst():
    for _ in range(3):
        idx = random.randint(0, NUM_PIXELS - 1)
        color = random.choice(firework_colors)
        pixels[idx] = color
        pixels.show()
        time.sleep(0.05)
        pixels[idx] = (0,0,0)
        pixels.show()

def rainbow_cycle(duration=9):
    steps = 60
    for i in range(steps):
        for j in range(NUM_PIXELS):
            rc_index = (j * 256 // NUM_PIXELS + i * 5) % 256
            pixels[j] = wheel(rc_index)
        pixels.show()
        time.sleep(duration / steps)

def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return (255 - pos * 3, pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (0, 255 - pos * 3, pos * 3)
    else:
        pos -= 170
        return (pos * 3, 0, 255 - pos * 3)


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
        logging.info(f"Chosen sound {choice['name']}")
      
        choice_name = choice['name']
        success_sound = choice['song']
        sound_length = choice['length']
      
        pixels.fill((50, 50, 50))  # Soft white idle glow
        pixels.show()

        id, text = reader.read()
        print(f"Scanned MagicBand ID: {id}")
        logging.info(f"Scanned MagicBand ID: {id}")

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
        elif choice_name == 'stop_us':
            start = time.time()
            while time.time() - start < 9:
                comet(random.choice(firework_colors), tail_length=8, delay=0.03)
                burst()
                rainbow_cycle(duration=1)  # quick rainbow flashes
            
        else:
            fade_to_color((0, 255, 0), duration=sound_length)  # Fade to green
        time.sleep(1)
        fade_to_color((50, 50, 50), duration=2)  # Fade back to soft white

except Exception as e:
    logging.error(f"There was an error: {e}")
    pass
  
except KeyboardInterrupt:
    print("Stopped.")
    logging.info(f"Keyboard Interrupt")
  
finally:
    clear_pixels()
    pygame.mixer.quit()
