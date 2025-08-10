import ImageToDMX as imdmx
import numpy as np
import time
from knob import RotaryEncoderArray as REA
import os
import random

# Define multiple encoder pairs (X,Y)
encoder_pins = [
    ("P8_7", "P8_8"),    # X1 encoder
    ("P8_9", "P8_10"),   # Y1 encoder
    ("P8_11", "P8_12"),  # X2 encoder
    ("P8_13", "P8_14"),  # Y2 encoder
     ("P8_15", "P8_16"),  # X2 encoder
    ("P8_17", "P8_18"),  # Y2 encoder   
     ("P9_11", "P9_12"),  # X2 encoder
    ("P9_13", "P9_14"),  # Y2 encoder   
    # Additional encoders can be added here
]
button_pins = ["P9_15", "P9_16","P9_17", "P9_18","P9_21", "P9_22","P9_23", "P9_24"]
# Min/max limits for each encoder
min_values = [0, 0, 0, 0,0,0,0,0]  # X1_MIN, Y1_MIN, X2_MIN, Y2_MIN
max_values = [37,61, 37, 61, 37, 61, 37, 61]  # X1_MAX, Y1_MAX, X2_MAX, Y2_MAX

# Create encoder array
encoders = REA(encoder_pins, min_values, max_values,button_pins)

receivers = [
            # Primary display receivers (frame 0)
            [
                {
                    'ip': '192.168.68.111',
                    'pixel_count': 2356,
                    'addressing_array': imdmx.make_indicesHS(r"layout.txt")
                }
            ]]

dat = np.zeros([38,62,3]).astype(np.uint8)

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
last_buttons=encoders.get_buttons()
frame_counter = 0  # Counter to track frames
time_last_update=time.time()
time_thresh=30
load_image_time=100
decay_rate=0.995
time_switch=1
last_load_time = 0
while True:
    buttons=encoders.get_buttons()
    if not np.array_equal(buttons, last_buttons):
        last_buttons=buttons
       # print(buttons)
    # Get the current positions - update happens in background thread
    positions = encoders.get_positions()
    
    if not np.array_equal(last_positions, positions):
        if (time_switch>0) and (time_thresh>100):
            time_thresh=time_thresh*0.9
        time_last_update=time.time()
        time_switch=0

        #print(positions)
    # Fade the entire image
    #dat = dat * 0.9995
    #print(encoders.get_button_presses())
    # Get pairs of positions (X,Y coordinates)
    num_pairs = len(positions) // 2
    
    # Update each pair's position with its unique color
    for i in range(num_pairs):
        x = positions[i*2]     # X position
        y = positions[i*2+1]   # Y position
        
        # Use modulo to cycle through colors if there are more pairs than colors
        #color_index = i % len(pair_colors)
        color_index = buttons[i*2+1]
        # Set the pixel at the current position to full brightness with unique color
        size = buttons[i*2]
        
        # Calculate radius based on size value (0-4)
        radius = int(0.5+size * 0.75)  # Size 0 = radius 0, Size 4 = radius 2
        
        # Create coordinates for all pixels within radius
        y_indices, x_indices = np.ogrid[-radius:radius+1, -radius:radius+1]
        # Calculate distance from center for each pixel
        distances = np.sqrt(x_indices**2 + y_indices**2)
        
        # Calculate intensity falloff (1.0 at center, decreasing outward)
        intensity = np.clip(1.0 - distances/max(0.5+size * 0.75, 1), 0, 1)**2
        
        # Calculate bounds for the spot
        # Calculate bounds for the spot
        # Calculate bounds for the spot
        y_min = max(0, y - radius)
        y_max = min(dat.shape[1] - 1, y + radius)
        x_min = max(0, x - radius)
        x_max = min(dat.shape[0] - 1, x + radius)
        
        # Make sure we have valid ranges before proceeding
        if y_min <= y_max and x_min <= x_max:
            # Calculate indices within array bounds
            array_y_indices = np.arange(y_min, y_max + 1)
            array_x_indices = np.arange(x_min, x_max + 1)
            
            # Ensure we have non-empty arrays
            if len(array_y_indices) > 0 and len(array_x_indices) > 0:
                # Adjust distances/intensities to match array bounds
                y_offset = y_min - (y - radius)
                x_offset = x_min - (x - radius)
                sub_intensity = intensity[y_offset:y_offset + len(array_y_indices), 
                                        x_offset:x_offset + len(array_x_indices)]
                
                # Get the intensity matrix properly shaped for broadcasting
                intensity_matrix = sub_intensity.T
                
                # Apply the spot with intensity falloff for each color channel
                for color_channel in range(3):
                    color_value = pair_colors[color_index][color_channel]
                    
                    # Direct indexing to avoid dimension issues
                    current_values = dat[x_min:x_max+1, y_min:y_max+1, color_channel]
                    new_values = (intensity_matrix * color_value).astype(np.uint8)
                    
                    # Update with maximum values
                    dat[x_min:x_max+1, y_min:y_max+1, color_channel] = np.maximum(
                        current_values, new_values
                    )

    
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
    time_dif=time.time()-time_last_update
    if time_dif>time_thresh:
        if time_switch==0:
            # Save dat to a timestamped .npz file
            save_dir = "unfiltered_saves"
            os.makedirs(save_dir, exist_ok=True)
            
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = os.path.join(save_dir, f"display_capture_{timestamp}.npz")
            np.savez_compressed(filename, display_data=dat)
            print(f"Display data saved to {filename}")
            time_switch=1

        current_time = time.time()
        if current_time - last_load_time > load_image_time:
            filtered_dir = "filtered_saves"
            if os.path.exists(filtered_dir):
                npz_files = [f for f in os.listdir(filtered_dir) if f.endswith('.npz')]
                if npz_files:
                    # Choose a random file
                    random_file = random.choice(npz_files)
                    file_path = os.path.join(filtered_dir, random_file)
                    
                    try:
                        # Load the display data
                        loaded_data = np.load(file_path)
                        if 'display_data' in loaded_data:
                            dat = loaded_data['display_data']
                            print(f"Loaded display data from {file_path}")
                        else:
                            print(f"No display_data array found in {file_path}")
                    except Exception as e:
                        print(f"Error loading file {file_path}: {e}")
                    
                    # Update the last load time
                    last_load_time = current_time

        if (time_dif-time_thresh-time_switch*9>0) and (time_thresh<1000):
            time_switch+=1
            time_thresh+=1

        

        dat = dat * decay_rate