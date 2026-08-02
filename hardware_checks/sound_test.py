from machine import Pin, PWM
import time

# Initialize PWM on the GPIO pin (GP15 in this example)
speaker_pin = PWM(Pin(15))

def play_tone(frequency, duration):
    speaker_pin.freq(frequency)  # Set the frequency of the tone
    speaker_pin.duty_u16(32768)  # 50% duty cycle (max volume)
    time.sleep(duration)         # Play the tone for a specified duration
    speaker_pin.duty_u16(0)      # Turn off the sound

# Play a 1kHz tone for 0.5 seconds
play_tone(1000, 0.5)

# Play another tone
play_tone(1500, 0.3)
