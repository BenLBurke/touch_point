import board
import busio
import digitalio
import neopixel
import time
import pygame
from adafruit_pn532.spi import PN532_SPI

# --------- Setup RFID over SPI ---------
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
cs_pin = digitalio.DigitalInOut(board.D5)
pn532 = PN532_SPI(spi, cs_pin, debug=False)
pn532.SAM_configuration()

# --------- Setup NeoPixels ---------
NUM_PIXELS = 30
PIXEL_PIN = board.D18
pixels = neopixel.NeoPixel(PIXEL_PIN, NUM_PIXELS, auto_write=False)

# --------- Setup Sound ---------
pygame.mixer.init()
scan_sound = pygame.mixer.Sound("sounds_files/mb_accept.wav")
green_sound = pygame.mixer.Sound("sounds_files/progress.wav")

# --------- Animations ---------
def white_comet():
    for i in range(NUM_PIXELS):
        pixels[i] = (200, 200, 200)
        if i > 0:
            pixels[i-1] = (50, 50, 50)
        if i > 1:
            pixels[i-2] = (10, 10, 10)
        pixels.show()
        time.sleep(0.05)
    pixels.fill((0, 0, 0))
    pixels.show()

def blue_comet():
    for i in range(NUM_PIXELS):
        pixels[i] = (0, 0, 255)
        if i > 0:
            pixels[i-1] = (0, 0, 80)
        if i > 1:
            pixels[i-2] = (0, 0, 20)
        pixels.show()
        time.sleep(0.05)
    pixels.fill((0, 0, 0))
    pixels.show()

def green_fade():
    for i in range(0, 256, 5):
        pixels.fill((0, i, 0))
        pixels.show()
        time.sleep(0.01)
    for i in range(255, -1, -5):
        pixels.fill((0, i, 0))
        pixels.show()
        time.sleep(0.01)
    pixels.fill((0, 0, 0))
    pixels.show()

# --------- RFID + Light + Sound Logic ---------
def wait_for_tag_and_respond():
    print("Waiting for NFC tag...")
    while True:
        white_comet()

        uid = pn532.read_passive_target(timeout=0.1)
        if uid is not None:
            print("Tag detected:", [hex(i) for i in uid])

            # Play scan sound and animation
            scan_sound.play()
            blue_comet()

            # Delay and play green confirmation
            time.sleep(2)
            green_sound.play()
            green_fade()

# --------- Run Loop ---------
if __name__ == "__main__":
    try:
        wait_for_tag_and_respond()
    except KeyboardInterrupt:
        pixels.fill((0, 0, 0))
        pixels.show()
        print("Program stopped.")
