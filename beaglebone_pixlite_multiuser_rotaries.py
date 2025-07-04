
import smbus2
import time
import socket
import threading
import Adafruit_BBIO.GPIO as GPIO

# MPU6050 I2C Address
MPU6050_ADDR = 0x68
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B

# LED matrix size
MATRIX_WIDTH = 80
MATRIX_HEIGHT = 50

# Art-Net settings
ARTNET_IP = '192.168.1.50'  # Replace with your Pixlite controller IP
ARTNET_PORT = 6454
UNIVERSE_SIZE = 170
NUM_PIXELS = MATRIX_WIDTH * MATRIX_HEIGHT
NUM_UNIVERSES = (NUM_PIXELS + UNIVERSE_SIZE - 1) // UNIVERSE_SIZE

# Initialize I2C
bus = smbus2.SMBus(1)

# Define rotary encoders (A and B pins for X and Y of 4 users)
ENCODERS = {
    'red':   {'xA': 'P8_7',  'xB': 'P8_8',  'yA': 'P8_9',  'yB': 'P8_10'},
    'green': {'xA': 'P8_11', 'xB': 'P8_12', 'yA': 'P8_13', 'yB': 'P8_14'},
    'blue':  {'xA': 'P8_15', 'xB': 'P8_16', 'yA': 'P8_17', 'yB': 'P8_18'},
    'white': {'xA': 'P8_19', 'xB': 'P8_20', 'yA': 'P8_21', 'yB': 'P8_22'}
}

# Initial cursor positions
positions = {
    'red':   [10, 10],
    'green': [20, 10],
    'blue':  [30, 10],
    'white': [40, 10]
}

colors = {
    'red':   (255, 0, 0),
    'green': (0, 255, 0),
    'blue':  (0, 0, 255),
    'white': (255, 255, 255)
}

position_lock = threading.Lock()

def mpu6050_init():
    bus.write_byte_data(MPU6050_ADDR, PWR_MGMT_1, 0)

def read_acceleration():
    def read_word(reg):
        high = bus.read_byte_data(MPU6050_ADDR, reg)
        low = bus.read_byte_data(MPU6050_ADDR, reg + 1)
        val = (high << 8) + low
        return val if val < 32768 else val - 65536

    x = read_word(ACCEL_XOUT_H)
    y = read_word(ACCEL_XOUT_H + 2)
    z = read_word(ACCEL_XOUT_H + 4)
    return (x, y, z)

def detect_shake(last_accel, threshold=10000):
    x, y, z = read_acceleration()
    dx = abs(x - last_accel[0])
    dy = abs(y - last_accel[1])
    dz = abs(z - last_accel[2])
    return (dx + dy + dz) > threshold, (x, y, z)

def create_artnet_packet(universe, data):
    header = bytearray()
    header.extend(b'Art-Net ')
    header.extend((0x00, 0x50))
    header.extend((0x00, 0x0e))
    header.extend((0x00, 0x00))
    header.extend(universe.to_bytes(2, 'little'))
    header.extend(len(data).to_bytes(2, 'big'))
    header.extend(data)
    return header

def send_led_data(matrix):
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    flat_data = bytearray()
    for row in matrix:
        for pixel in row:
            flat_data.extend(pixel)
    for u in range(NUM_UNIVERSES):
        start = u * UNIVERSE_SIZE * 3
        end = start + UNIVERSE_SIZE * 3
        packet_data = flat_data[start:end]
        packet = create_artnet_packet(u, packet_data)
        udp.sendto(packet, (ARTNET_IP, ARTNET_PORT))

def rotary_callback_generator(user, axis):
    def callback(channel):
        a_pin = ENCODERS[user][axis + 'A']
        b_pin = ENCODERS[user][axis + 'B']
        a = GPIO.input(a_pin)
        b = GPIO.input(b_pin)
        delta = 1 if a == b else -1
        with position_lock:
            if axis == 'x':
                positions[user][0] = (positions[user][0] + delta) % MATRIX_WIDTH
            else:
                positions[user][1] = (positions[user][1] + delta) % MATRIX_HEIGHT
    return callback

def setup_all_encoders():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    for user, pins in ENCODERS.items():
        for axis in ['x', 'y']:
            a_pin = pins[axis + 'A']
            b_pin = pins[axis + 'B']
            GPIO.setup(a_pin, GPIO.IN)
            GPIO.setup(b_pin, GPIO.IN)
            cb = rotary_callback_generator(user, axis)
            GPIO.add_event_detect(a_pin, GPIO.BOTH, callback=cb)

def erase_matrix(matrix):
    for y in range(MATRIX_HEIGHT):
        for x in range(MATRIX_WIDTH):
            matrix[y][x] = (0, 0, 0)

def drawing_loop():
    mpu6050_init()
    setup_all_encoders()
    matrix = [[(0, 0, 0) for _ in range(MATRIX_WIDTH)] for _ in range(MATRIX_HEIGHT)]
    last_accel = read_acceleration()

    while True:
        shaken, last_accel = detect_shake(last_accel)
        if shaken:
            print("Shake detected! Erasing matrix...")
            erase_matrix(matrix)

        with position_lock:
            for user, (x, y) in positions.items():
                matrix[y][x] = colors[user]

        send_led_data(matrix)
        time.sleep(0.1)

if __name__ == "__main__":
    try:
        drawing_loop()
    except KeyboardInterrupt:
        GPIO.cleanup()
