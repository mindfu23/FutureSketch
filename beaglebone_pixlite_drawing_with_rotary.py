
import smbus2
import time
import socket
import threading
import RPi.GPIO as GPIO  # For BeagleBone, use Adafruit_BBIO.GPIO
from collections import deque

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
UNIVERSE_SIZE = 170  # RGB values per universe (170*3 = 510 bytes)
NUM_PIXELS = MATRIX_WIDTH * MATRIX_HEIGHT
NUM_UNIVERSES = (NUM_PIXELS + UNIVERSE_SIZE - 1) // UNIVERSE_SIZE

# Initialize I2C
bus = smbus2.SMBus(1)

# Rotary encoder GPIO pins (change to match your wiring)
ENCODER_A = 'P8_12'  # For BeagleBone
ENCODER_B = 'P8_14'

# Position state
cursor_x = 0
cursor_y = 0
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
    header.extend(b'Art-Net ')                   # ID
    header.extend((0x00, 0x50))                     # OpCode ArtDmx
    header.extend((0x00, 0x0e))                     # Protocol version
    header.extend((0x00, 0x00))                     # Sequence, Physical
    header.extend(universe.to_bytes(2, 'little'))   # Universe
    header.extend(len(data).to_bytes(2, 'big'))     # Length
    header.extend(data)                             # DMX data
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

def rotary_callback(channel):
    global cursor_x
    a = GPIO.input(ENCODER_A)
    b = GPIO.input(ENCODER_B)
    direction = 1 if a == b else -1
    with position_lock:
        cursor_x = (cursor_x + direction) % MATRIX_WIDTH

def setup_rotary_encoder():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(ENCODER_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(ENCODER_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(ENCODER_A, GPIO.BOTH, callback=rotary_callback)

def erase_matrix(matrix):
    for y in range(MATRIX_HEIGHT):
        for x in range(MATRIX_WIDTH):
            matrix[y][x] = (0, 0, 0)

def drawing_loop():
    mpu6050_init()
    setup_rotary_encoder()
    matrix = [[(0, 0, 0) for _ in range(MATRIX_WIDTH)] for _ in range(MATRIX_HEIGHT)]
    last_accel = read_acceleration()
    y_pos = MATRIX_HEIGHT // 2

    while True:
        shaken, last_accel = detect_shake(last_accel)
        if shaken:
            print("Shake detected! Erasing matrix...")
            erase_matrix(matrix)

        with position_lock:
            matrix[y_pos][cursor_x] = (255, 255, 255)  # Draw white pixel

        send_led_data(matrix)
        time.sleep(0.1)

if __name__ == "__main__":
    try:
        drawing_loop()
    except KeyboardInterrupt:
        GPIO.cleanup()
