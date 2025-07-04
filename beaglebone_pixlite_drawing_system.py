
import smbus2
import time
import socket
import threading
import random

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
UNIVERSE = 0

# Initialize I2C
bus = smbus2.SMBus(1)

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
    packet = create_artnet_packet(UNIVERSE, flat_data[:512])
    udp.sendto(packet, (ARTNET_IP, ARTNET_PORT))

def simulate_rotary_input():
    # Placeholder for reading rotary encoder knobs
    x = random.randint(0, MATRIX_WIDTH - 1)
    y = random.randint(0, MATRIX_HEIGHT - 1)
    return x, y

def erase_matrix(matrix):
    for y in range(MATRIX_HEIGHT):
        for x in range(MATRIX_WIDTH):
            matrix[y][x] = (0, 0, 0)

def drawing_loop():
    mpu6050_init()
    matrix = [[(0, 0, 0) for _ in range(MATRIX_WIDTH)] for _ in range(MATRIX_HEIGHT)]
    last_accel = read_acceleration()

    while True:
        shaken, last_accel = detect_shake(last_accel)
        if shaken:
            print("Shake detected! Erasing matrix...")
            erase_matrix(matrix)

        x, y = simulate_rotary_input()
        matrix[y][x] = (255, 255, 255)  # White pixel

        send_led_data(matrix)
        time.sleep(0.1)

if __name__ == "__main__":
    drawing_loop()
