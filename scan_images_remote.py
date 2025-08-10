import os
import numpy as np
import cv2
import io
import paramiko
import tempfile

def scan_unfiltered_images():
    """
    Connect to remote host via SSH, scan unfiltered_saves directory for .npz files, 
    display each image locally, and allow user to save (S) or reject (D) them on the remote system.
    """
    # Remote connection details
    remote_host = "192.168.68.50"
    remote_user = "debian"
    remote_password = "temppwd"
    remote_base_path = "~/FS/FutureSketch"
    
    # Remote directory paths
    unfiltered_dir = f"{remote_base_path}/unfiltered_saves"
    filtered_dir = f"{remote_base_path}/filtered_saves"
    rejected_dir = f"{remote_base_path}/rejected_saves"
    
    print(f"Connecting to {remote_user}@{remote_host}...")
    
    # Establish SSH connection
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=remote_host, username=remote_user, password=remote_password)
        sftp = ssh_client.open_sftp()
        
        # Create directories if they don't exist
        for directory in [filtered_dir, rejected_dir]:
            try:
                ssh_client.exec_command(f"mkdir -p {directory}")
            except Exception as e:
                print(f"Error creating directory {directory}: {e}")
                return
        
        # List files in unfiltered directory
        try:
            # Expand the path (to handle ~)
            stdin, stdout, stderr = ssh_client.exec_command(f"echo {unfiltered_dir}")
            expanded_unfiltered_dir = stdout.read().decode().strip()
            
            # List .npz files
            stdin, stdout, stderr = ssh_client.exec_command(f"ls {expanded_unfiltered_dir}/*.npz 2>/dev/null")
            file_list = stdout.read().decode().strip().split('\n')
            
            # Filter out empty entries
            npz_files = [os.path.basename(f) for f in file_list if f.strip()]
            
        except Exception as e:
            print(f"Error listing files: {e}")
            ssh_client.close()
            return
        
        if not npz_files or (len(npz_files) == 1 and not npz_files[0]):
            print(f"No .npz files found in {unfiltered_dir}.")
            ssh_client.close()
            return
        
        print(f"Found {len(npz_files)} files. Starting scan...")
        print("Press 'S' to save to filtered directory, 'D' to reject, 'Q' to quit")
        
        # Process each file
        for i, file_name in enumerate(npz_files):
            remote_file_path = f"{expanded_unfiltered_dir}/{file_name}"
            temp_path = None
            
            try:
                # Create a temporary file to store the downloaded .npz
                temp_file = tempfile.NamedTemporaryFile(suffix='.npz', delete=False)
                temp_path = temp_file.name
                temp_file.close()  # Close file handle immediately
                
                # Download the file
                sftp.get(remote_file_path, temp_path)
                
                # Load the data - use a with statement to ensure proper closing
                img_data = None
                with np.load(temp_path, allow_pickle=True) as data:
                    if 'display_data' not in data:
                        print(f"Warning: {file_name} does not contain 'display_data'. Skipping.")
                        # Clean up before continuing
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        continue
                    
                    # Copy the data to a new variable before closing the file
                    img_data = data['display_data'].copy()
                
                # Clean up the temporary file
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception as e:
                        print(f"Warning: Could not delete temporary file {temp_path}: {e}")
                
                # Scale up the image for better visualization
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
                        # Move to filtered directory on remote
                        stdin, stdout, stderr = ssh_client.exec_command(
                            f"mv {remote_file_path} {filtered_dir}/{file_name}"
                        )
                        error = stderr.read().decode()
                        if error:
                            print(f"Error moving file: {error}")
                        else:
                            print(f"Moved to {filtered_dir}/{file_name}")
                        break
                        
                    elif key == ord('d') or key == ord('D'):
                        # Move to rejected directory on remote
                        stdin, stdout, stderr = ssh_client.exec_command(
                            f"mv {remote_file_path} {rejected_dir}/{file_name}"
                        )
                        error = stderr.read().decode()
                        if error:
                            print(f"Error moving file: {error}")
                        else:
                            print(f"Rejected: Moved to {rejected_dir}/{file_name}")
                        break
                        
                    elif key == ord('q') or key == ord('Q'):
                        # Quit the program
                        print("Quitting...")
                        cv2.destroyAllWindows()
                        ssh_client.close()
                        return
                        
                    else:
                        print("Invalid key. Press 'S' to save, 'D' to reject, 'Q' to quit")
                
                # Close the window
                cv2.destroyWindow(window_name)
                
            except Exception as e:
                print(f"Error processing {file_name}: {e}")
                # Make sure to clean up temp file if it exists
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
        
        print("Finished scanning all files.")
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"Connection error: {e}")
    
    finally:
        if 'ssh_client' in locals() and ssh_client:
            ssh_client.close()
            print("SSH connection closed.")

if __name__ == "__main__":
    scan_unfiltered_images()