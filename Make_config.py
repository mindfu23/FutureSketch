def create_serpentine_config(output_file, start_pixel, width, height, row_start=0):
    """
    Creates a serpentine layout configuration file compatible with make_indicesHS.
    
    Parameters:
    output_file (str): Path to the output file
    start_pixel (int): Starting pixel number (for the first pixel in the pattern)
    width (int): Width of the pixel zone
    height (int): Height of the pixel zone
    row_start (int): Starting row number (default is 0)
    
    The function will append to the file if it exists, or create a new one if it doesn't.
    Each row in the output file follows the format: [row_number, start_column, length]
    where length is positive if left-to-right, negative if right-to-left.
    """
    import os
    
    # Create configuration data
    config_data = []
    current_pixel = start_pixel
    
    # Generate serpentine pattern
    for row in range(height):
        actual_row = row_start + row
        
        if row % 2 == 0:  # Even rows - left to right
            config_data.append([actual_row, start_pixel, width])
            current_pixel += width  # Move to the end of this row
        else:  # Odd rows - right to left
            config_data.append([actual_row, start_pixel, -width])
            current_pixel += width  # Move to the end of this row
    
    # Save configuration to file
    # Check if file exists to determine mode (append or create new)
    file_mode = 'a' if os.path.exists(output_file) else 'w'
    
    with open(output_file, file_mode) as f:
        # Add a newline if appending to an existing file that doesn't end with a newline
        if file_mode == 'a' and os.path.getsize(output_file) > 0:
            with open(output_file, 'rb+') as check_file:
                check_file.seek(-1, os.SEEK_END)
                if check_file.read(1) != b'\n':
                    f.write('\n')
        
        # Write configuration data
        for row_config in config_data:
            f.write(f"{int(row_config[0])},{int(row_config[1])},{int(row_config[2])}\n")
            
    return config_data

create_serpentine_config("layout.txt", start_pixel=0, width=31, height=19,row_start=0)
create_serpentine_config("layout.txt", start_pixel=31, width=31, height=19,row_start=0)
create_serpentine_config("layout.txt", start_pixel=0, width=31, height=19,row_start=19)
create_serpentine_config("layout.txt", start_pixel=31, width=31, height=19,row_start=19)