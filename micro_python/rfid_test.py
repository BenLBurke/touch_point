from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO

reader = SimpleMFRC522()

print("Place your tag near the reader...")

try:
    id, text = reader.read()
    print("ID: %s\nText: %s" % (id, text))
finally:
    print("Cleaning up GPIO")
    GPIO.cleanup()
