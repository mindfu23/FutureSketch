import Adafruit_BBIO.GPIO as GPIO
import time
import numpy as np
import threading

class RotaryEncoderArray:
    def __init__(self, encoder_pins, min_values=None, max_values=None):
        """
        Initialize rotary encoder array.
        
        Args:
            encoder_pins: List of tuples, each containing (CLK_PIN, DT_PIN) for each encoder
            min_values: List of minimum values for each encoder (defaults to all zeros)
            max_values: List of maximum values for each encoder (defaults to all 100)
        """
        self.encoder_count = len(encoder_pins)
        self.clk_pins = [pins[0] for pins in encoder_pins]
        self.dt_pins = [pins[1] for pins in encoder_pins]
        
        # Set default limits if not provided
        self.min_values = min_values if min_values is not None else [0] * self.encoder_count
        self.max_values = max_values if max_values is not None else [100] * self.encoder_count
        
        # Initialize positions and last states
        self.positions = np.zeros(self.encoder_count, dtype=int)
        self.clk_last_states = []
        
        # Thread control
        self.running = False
        self.update_thread = None
        self.lock = threading.Lock()
        
        # Set up GPIO pins
        for clk_pin, dt_pin in encoder_pins:
            GPIO.setup(clk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(dt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self.clk_last_states.append(GPIO.input(clk_pin))
        
        # Start the update thread
        self.start_update_thread()
    
    def update(self):
        """
        Update positions based on encoder states.
        Returns True if any position changed, False otherwise.
        """
        changed = False
        
        with self.lock:
            for i in range(self.encoder_count):
                clk_state = GPIO.input(self.clk_pins[i])
                dt_state = GPIO.input(self.dt_pins[i])
                
                # Detect rising edge on CLK pin
                if clk_state != self.clk_last_states[i] and clk_state == 1:
                    old_position = self.positions[i]
                    
                    if dt_state != clk_state:
                        # Clockwise
                        self.positions[i] = min(self.max_values[i], self.positions[i] + 1)
                    else:
                        # Counter-clockwise
                        self.positions[i] = max(self.min_values[i], self.positions[i] - 1)
                    
                    if old_position != self.positions[i]:
                        changed = True
                
                self.clk_last_states[i] = clk_state
        
        return changed
    
    def _update_loop(self):
        """Thread function that continuously polls the encoders"""
        while self.running:
            self.update()
            # Small sleep to prevent CPU hogging
            time.sleep(0.0001)  # 0.1ms sleep, very short to catch all changes
    
    def start_update_thread(self):
        """Start the background thread for encoder updates"""
        if not self.running:
            self.running = True
            self.update_thread = threading.Thread(target=self._update_loop)
            self.update_thread.daemon = True  # Thread will exit when main program exits
            self.update_thread.start()
    
    def stop_update_thread(self):
        """Stop the background update thread"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=1.0)
    
    def get_positions(self):
        """
        Returns the current positions as a numpy array.
        """
        with self.lock:
            return self.positions.copy()
    
    def get_positions_as_pairs(self):
        """
        Returns the positions as x,y pairs in a 2xN numpy array.
        Assumes positions are ordered as [x1, y1, x2, y2, ...]
        """
        with self.lock:
            if self.encoder_count % 2 != 0:
                raise ValueError("Cannot form pairs: odd number of encoders")
                
            x_positions = self.positions[0::2]  # Every even index (0, 2, 4...)
            y_positions = self.positions[1::2]  # Every odd index (1, 3, 5...)
            
            return np.array([x_positions, y_positions])
    
    def cleanup(self):
        """
        Clean up GPIO resources.
        """
        self.stop_update_thread()
        GPIO.cleanup()


# Example usage:
if __name__ == "__main__":
    try:
        # Define pins for two X-Y encoder pairs
        encoder_pins = [
            ("P8_7", "P8_8"),    # X1 encoder
            ("P8_9", "P8_10"),   # Y1 encoder
            # Additional encoders can be added here
        ]
        
        # Min/max limits for each encoder
        min_values = [0, 0]  # X1_MIN, Y1_MIN
        max_values = [49, 79]  # X1_MAX, Y1_MAX
        
        # Create encoder array
        encoders = RotaryEncoderArray(encoder_pins, min_values, max_values)
        
        print("Rotary encoder test. Turn the knobs.")
        while True:
            positions = encoders.get_positions()
            positions_pairs = encoders.get_positions_as_pairs()
            
            print(f"Raw positions: {positions}")
            print(f"As X-Y pairs: {positions_pairs}")
                
            time.sleep(0.1)  # Just to avoid flooding the console
            
    except KeyboardInterrupt:
        print("Exiting cleanly")
        encoders.cleanup()