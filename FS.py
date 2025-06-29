import ImageToDMX as imdmx
import numpy as np
import time
from knob import RotaryEncoderArray as REA

encoder_pins = [
    ("P8_7", "P8_8"),    # X1 encoder
    ("P8_9", "P8_10"),   # Y1 encoder
    # Additional encoders can be added here
]

# Min/max limits for each encoder
min_values = [0, 0]  # X1_MIN, Y1_MIN
max_values = [15, 15]  # X1_MAX, Y1_MAX

# Create encoder array
encoders = REA(encoder_pins, min_values, max_values)

receivers = [
            # Primary display receivers (frame 0)
            [
                {
                    'ip': '192.168.68.111',
                    'pixel_count': 500,
                    'addressing_array': imdmx.make_indicesHS(r"Unit1.txt")
                }
            ]]
dat = np.zeros([16,16,3]).astype(np.uint8)
dat[:,7,2]=255
screens = []
for i in range(len(receivers)):
    if i < len(receivers):
        screens.append(imdmx.SACNPixelSender(receivers[i]))
    else:
        # For displays without physical receivers, add None as placeholder
        screens.append(None)

# Store last positions to detect changes
last_positions = None

while True:
    # Get the current positions - update happens in background thread
    positions = encoders.get_positions()
    
    # If positions changed, update the pixel
    if last_positions is None or not np.array_equal(positions, last_positions):
        # Set the pixel at the current encoder position to green [0,255,0]
        dat[positions[0], positions[1], :] = [0, 255, 0]
        last_positions = positions.copy()
    
    # Fade the entire image
    dat = dat * 0.999
    time.sleep(1/20)

    # Send the updated image
    screens[0].send(dat.copy().astype(np.uint8))