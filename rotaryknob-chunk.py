#this is completely untested as yet

import Adafruit_BBIO.GPIO as GPIO
import time

# Pin definitions
CLK = "P9_12"
DT = "P9_15"

# Set up GPIO
GPIO.setup(CLK, GPIO.IN)
GPIO.setup(DT, GPIO.IN)

# Position tracking
x_position = 0
clk_last_state = GPIO.input(CLK)

try:
    print("Rotary encoder test. Turn the knob.")
    while True:
        clk_state = GPIO.input(CLK)
        dt_state = GPIO.input(DT)

        # Detect rising edge on CLK
        if clk_state != clk_last_state and clk_state == 1:
            if dt_state != clk_state:
                x_position += 1   # Clockwise
            else:
                x_position -= 1   # Counter-clockwise
            
            print(f"Pixel moved to x = {x_position}")

        clk_last_state = clk_state
        time.sleep(0.001)

except KeyboardInterrupt:
    print("Exiting cleanly")
    GPIO.cleanup()
