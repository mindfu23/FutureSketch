#this is completely untested as yet

import Adafruit_BBIO.GPIO as GPIO
import time

# Pin definitions
CLK_X = "P8_7"
DT_X = "P8_8"
CLK_Y = "P8_9"
DT_Y = "P8_10"

# Set up GPIO
GPIO.setup(CLK_X, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DT_X, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(CLK_Y, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DT_Y, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Position tracking
x_position = 0
y_position = 0
clk_x_last_state = GPIO.input(CLK_X)
clk_y_last_state = GPIO.input(CLK_Y)

# Define limits
X_MIN = 0
X_MAX = 49
Y_MIN = 0
Y_MAX = 79

try:
    print("Rotary encoder test. Turn the knobs.")
    while True:
        # X-axis encoder
        clk_x_state = GPIO.input(CLK_X)
        dt_x_state = GPIO.input(DT_X)

        # Detect rising edge on CLK_X
        if clk_x_state != clk_x_last_state and clk_x_state == 1:
            if dt_x_state != clk_x_state:
                x_position = min(X_MAX, x_position + 1)   # Clockwise
            else:
                x_position = max(X_MIN, x_position - 1)   # Counter-clockwise
            
            print(f"Pixel moved to x = {x_position}")

        clk_x_last_state = clk_x_state

        # Y-axis encoder
        clk_y_state = GPIO.input(CLK_Y)
        dt_y_state = GPIO.input(DT_Y)

        # Detect rising edge on CLK_Y
        if clk_y_state != clk_y_last_state and clk_y_state == 1:
            if dt_y_state != clk_y_state:
                y_position = min(Y_MAX, y_position + 1)   # Clockwise
            else:
                y_position = max(Y_MIN, y_position - 1)   # Counter-clockwise
            
            print(f"Pixel moved to y = {y_position}")

        clk_y_last_state = clk_y_state
        
        # Print combined position when either encoder changes
        if (clk_x_state != clk_x_last_state and clk_x_state == 1) or (clk_y_state != clk_y_last_state and clk_y_state == 1):
            print(f"Pixel position: ({x_position}, {y_position})")
            
        time.sleep(0.001)

except KeyboardInterrupt:
    print("Exiting cleanly")
    GPIO.cleanup()