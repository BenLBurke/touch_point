from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO

reader = SimpleMFRC522()

while True:
  print("Place your tag near the reader...")

  try:
      id = reader.read_id()
      print("ID: %s" % id)
  finally:
      print("Cleaning up GPIO")
      GPIO.cleanup()
