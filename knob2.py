import Adafruit_BBIO.GPIO as GPIO
import time
import numpy as np
import threading

class RotaryEncoderArray:
    def __init__(self, encoder_pins, min_values=None, max_values=None, button_pins=None):
        """
        Initialize rotary encoder array.
        
        Args:
            encoder_pins: List of tuples, each containing (CLK_PIN, DT_PIN) for each encoder
            min_values: List of minimum values for each encoder (defaults to all zeros)
            max_values: List of maximum values for each encoder (defaults to all 100)
            button_pins: List of pins for push buttons
        """
        self.encoder_count = len(encoder_pins)
        self.clk_pins = [pins[0] for pins in encoder_pins]
        self.dt_pins = [pins[1] for pins in encoder_pins]
        self.bt_pins = button_pins if button_pins is not None else []
        
        # Set default limits if not provided
        self.min_values = min_values if min_values is not None else [0] * self.encoder_count
        self.max_values = max_values if max_values is not None else [100] * self.encoder_count
        
        # Initialize positions and last states
        self.positions = np.zeros(self.encoder_count, dtype=int)
        self.button_state = np.zeros(len(self.bt_pins), dtype=int)
        self.clk_last_states = []
        self.lock = threading.Lock()
        
        # Set up GPIO pins and attach interrupts
        for i, (clk_pin, dt_pin) in enumerate(encoder_pins):
            GPIO.setup(clk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(dt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self.clk_last_states.append(GPIO.input(clk_pin))
            
            # Add rising edge detection on CLK pin (BOTH for better reliability)
            GPIO.add_event_detect(clk_pin, GPIO.BOTH, 
                                  callback=lambda channel, idx=i: self._encoder_callback(channel, idx),
                                  bouncetime=1)  # 1ms debounce
        
        # Set up button pins and attach interrupts
        for i, bt_pin in enumerate(self.bt_pins):
            GPIO.setup(bt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            # Add rising edge detection on button pin
            GPIO.add_event_detect(bt_pin, GPIO.RISING, 
                                  callback=lambda channel, idx=i: self._button_callback(channel, idx),
                                  bouncetime=50)  # 50ms debounce for buttons
    
    def _encoder_callback(self, channel, encoder_idx):
        """Callback function for encoder interrupt"""
        with self.lock:
            clk_state = GPIO.input(self.clk_pins[encoder_idx])
            dt_state = GPIO.input(self.dt_pins[encoder_idx])
            
            # Only process on rising edge of CLK
            if clk_state == 1 and clk_state != self.clk_last_states[encoder_idx]:
                if dt_state != clk_state:
                    # Clockwise
                    self.positions[encoder_idx] = min(self.max_values[encoder_idx], 
                                                     self.positions[encoder_idx] + 1)
                else:
                    # Counter-clockwise
                    self.positions[encoder_idx] = max(self.min_values[encoder_idx], 
                                                     self.positions[encoder_idx] - 1)
            
            self.clk_last_states[encoder_idx] = clk_state
    
    def _button_callback(self, channel, button_idx):
        """Callback function for button interrupt"""
        with self.lock:
            self.button_state[button_idx] = np.mod(self.button_state[button_idx] + 1, 5)
    
    def get_positions(self):
        """
        Returns the current positions as a numpy array.
        """
        with self.lock:
            return self.positions.copy()

    def get_buttons(self):
        """
        Returns the current button states as a numpy array.
        """
        with self.lock:
            return self.button_state.copy()
    
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
        # Remove event detection for all pins
        for pin in self.clk_pins:
            GPIO.remove_event_detect(pin)
        
        for pin in self.bt_pins:
            GPIO.remove_event_detect(pin)
            
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
        
        # Button pins
        button_pins = ["P8_11", "P8_12"]  # Add your actual button pins
        
        # Min/max limits for each encoder
        min_values = [0, 0]  # X1_MIN, Y1_MIN
        max_values = [49, 79]  # X1_MAX, Y1_MAX
        
        # Create encoder array
        encoders = RotaryEncoderArray(encoder_pins, min_values, max_values, button_pins)
        
        print("Rotary encoder test. Turn the knobs.")
        while True:
            positions = encoders.get_positions()
            positions_pairs = encoders.get_positions_as_pairs()
            button_states = encoders.get_buttons()
            
            print(f"Raw positions: {positions}")
            print(f"As X-Y pairs: {positions_pairs}")
            print(f"Button states: {button_states}")
                
            time.sleep(0.1)  # Just to update the display
            
    except KeyboardInterrupt:
        print("Exiting cleanly")
        encoders.cleanup()