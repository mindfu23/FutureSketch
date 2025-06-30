import os
import numpy as np
import cv2
import shutil

def scan_unfiltered_images():
    """
    Scan unfiltered_saves directory for .npz files, display each image, and
    allow user to save (S) or reject (D) them.
    """
    # Directory paths
    unfiltered_dir = "unfiltered_saves"
    filtered_dir = "filtered_saves"
    rejected_dir = "rejected_saves"
    
    # Create directories if they don't exist
    os.makedirs(filtered_dir, exist_ok=True)
    os.makedirs(rejected_dir, exist_ok=True)
    
    # Check if unfiltered directory exists
    if not os.path.exists(unfiltered_dir):
        print(f"Error: {unfiltered_dir} directory not found.")
        return
    
    # Get all .npz files in the unfiltered directory
    npz_files = [f for f in os.listdir(unfiltered_dir) if f.endswith('.npz')]
    
    if not npz_files:
        print(f"No .npz files found in {unfiltered_dir}.")
        return
    
    print(f"Found {len(npz_files)} files. Starting scan...")
    print("Press 'S' to save to filtered directory, 'D' to reject, 'Q' to quit")
    
    # Process each file
    for i, file_name in enumerate(npz_files):
        file_path = os.path.join(unfiltered_dir, file_name)
        
        try:
            # Load the data
            data = np.load(file_path)
            
            if 'display_data' not in data:
                print(f"Warning: {file_name} does not contain 'display_data'. Skipping.")
                continue
            
            # Get the image data
            img_data = data['display_data']
            
            # Scale up the image for better visualization (16x16 is tiny on screen)
            scale_factor = 20
            img_resized = cv2.resize(img_data, 
                                    (img_data.shape[1] * scale_factor, 
                                     img_data.shape[0] * scale_factor),
                                    interpolation=cv2.INTER_NEAREST)
            
            # Display file information
            print(f"\nFile {i+1}/{len(npz_files)}: {file_name}")
            
            # Display the image
            window_name = f"Image Viewer - {file_name}"
            cv2.imshow(window_name, img_resized)
            
            # Wait for keyboard input
            while True:
                key = cv2.waitKey(0) & 0xFF
                
                if key == ord('s') or key == ord('S'):
                    # Save to filtered directory
                    dest_path = os.path.join(filtered_dir, file_name)
                    shutil.move(file_path, dest_path)
                    print(f"Moved to {dest_path}")
                    break
                    
                elif key == ord('d') or key == ord('D'):
                    # Move to rejected directory instead of deleting
                    dest_path = os.path.join(rejected_dir, file_name)
                    shutil.move(file_path, dest_path)
                    print(f"Rejected: Moved to {dest_path}")
                    break
                    
                elif key == ord('q') or key == ord('Q'):
                    # Quit the program
                    print("Quitting...")
                    cv2.destroyAllWindows()
                    return
                    
                else:
                    print("Invalid key. Press 'S' to save, 'D' to reject, 'Q' to quit")
            
            # Close the window
            cv2.destroyWindow(window_name)
            
        except Exception as e:
            print(f"Error processing {file_name}: {e}")
    
    print("Finished scanning all files.")
    cv2.destroyAllWindows()

if __name__ == "__main__":
    scan_unfiltered_images()