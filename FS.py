import ImageToDMX as imdmx
import numpy as np
import time
from knob import RotaryEncoderArray as REA
import os

# Define multiple encoder pairs (X,Y)
encoder_pins = [
    ("P8_7", "P8_8"),    # X1 encoder
    ("P8_9", "P8_10"),   # Y1 encoder
    ("P8_11", "P8_12"),  # X2 encoder
    ("P8_13", "P8_14"),  # Y2 encoder
    # Additional encoders can be added here
]

# Min/max limits for each encoder
min_values = [0, 0, 0, 0]  # X1_MIN, Y1_MIN, X2_MIN, Y2_MIN
max_values = [15, 15, 15, 15]  # X1_MAX, Y1_MAX, X2_MAX, Y2_MAX

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

screens = []
for i in range(len(receivers)):
    if i < len(receivers):
        screens.append(imdmx.SACNPixelSender(receivers[i]))
    else:
        # For displays without physical receivers, add None as placeholder
        screens.append(None)

# Define unique colors for each pair
# Colors are in RGB format
pair_colors = [
    [0, 255, 0],    # Green for pair 1
    [255, 0, 0],    # Red for pair 2
    [0, 0, 255],    # Blue for pair 3
    [255, 255, 0],  # Yellow for pair 4
    [255, 0, 255],  # Magenta for pair 5
    [0, 255, 255],  # Cyan for pair 6
]

# Store last positions to detect changes

# Store last positions
last_positions = encoders.get_positions().copy()
frame_counter = 0  # Counter to track frames
time_current=time.time()
time_thresh=600
time_switch=0
while True:
    # Get the current positions - update happens in background thread
    positions = encoders.get_positions()
    if last_positions!=positions:
        time_current=time.time()
        time_switch=0
    # Fade the entire image
    dat = dat * 0.99995
    
    # Get pairs of positions (X,Y coordinates)
    num_pairs = len(positions) // 2
    
    # Update each pair's position with its unique color
    for i in range(num_pairs):
        x = positions[i*2]     # X position
        y = positions[i*2+1]   # Y position
        
        # Use modulo to cycle through colors if there are more pairs than colors
        color_index = i % len(pair_colors)
        
        # Set the pixel at the current position to full brightness with unique color
        dat[x, y, :] = pair_colors[color_index]
    
    # Sleep for 1/120 second (120 FPS)
    time.sleep(1/120)
    
    # Only send updates every 3rd frame
    frame_counter += 1
    if frame_counter >= 3:
        # Send the updated image
        screens[0].send(dat.copy().astype(np.uint8))
        frame_counter = 0  # Reset counter
    
    # Update last positions
    last_positions = positions.copy()

    if time.time()-time_current>time_thresh:
        if time_switch==0:
            # Save dat to a timestamped .npz file
            save_dir = "unfiltered_saves"
            os.makedirs(save_dir, exist_ok=True)
            
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = os.path.join(save_dir, f"display_capture_{timestamp}.npz")
            np.savez_compressed(filename, display_data=dat)
            print(f"Display data saved to {filename}")
            time_switch=1


        dat = dat * 0.995