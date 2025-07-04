
import smbus2
import time
import socket
import threading
import Adafruit_BBIO.GPIO as GPIO
import csv
from datetime import datetime
from flask import Flask, render_template_string, jsonify
from flask_cors import CORS

# MPU6050 I2C Address
MPU6050_ADDR = 0x68
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B

# LED matrix, currently 4000 pixels, want it 80 on horizontal plane and 50 vertical
MATRIX_WIDTH = 80
MATRIX_HEIGHT = 50
ARTNET_IP = '192.168.1.50'
ARTNET_PORT = 6454
UNIVERSE_SIZE = 170
NUM_PIXELS = MATRIX_WIDTH * MATRIX_HEIGHT
NUM_UNIVERSES = (NUM_PIXELS + UNIVERSE_SIZE - 1) // UNIVERSE_SIZE
SAVE_BUTTON = 'P8_23'

bus = smbus2.SMBus(1)

# 4 sets rotary encorders, 2 knobs each set - 1 x and 1 y
ENCODERS = {
    'red':   {'xA': 'P8_7',  'xB': 'P8_8',  'yA': 'P8_9',  'yB': 'P8_10'},
    'green': {'xA': 'P8_11', 'xB': 'P8_12', 'yA': 'P8_13', 'yB': 'P8_14'},
    'blue':  {'xA': 'P8_15', 'xB': 'P8_16', 'yA': 'P8_17', 'yB': 'P8_18'},
    'white': {'xA': 'P8_19', 'xB': 'P8_20', 'yA': 'P8_21', 'yB': 'P8_22'}
}

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
matrix = [[(0, 0, 0) for _ in range(MATRIX_WIDTH)] for _ in range(MATRIX_HEIGHT)]

# how it writes to the Beaglebones SD card?
def mpu6050_init():
    bus.write_byte_data(MPU6050_ADDR, PWR_MGMT_1, 0)

# acceleromater detection
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

# pixel output to Pixlite 4 initialization?
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

# pixel output send?
def send_led_data():
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    flat_data = bytearray()
    for row in matrix:
        for pixel in row:
            flat_data.extend(pixel)
    total_pixels = len(flat_data) // 3
    for u in range(NUM_UNIVERSES):
        start_pixel = u * UNIVERSE_SIZE
        end_pixel = start_pixel + UNIVERSE_SIZE
        pixel_chunk = flat_data[start_pixel*3:end_pixel*3]
        if not pixel_chunk:
            continue
        packet = create_artnet_packet(u, pixel_chunk)
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

def save_matrix_to_sd():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"/media/mmcblk0p1/drawing_{timestamp}.csv"
    try:
        with open(path, mode='w', newline='') as file:
            writer = csv.writer(file)
            for row in matrix:
                writer.writerow([f"{r}:{g}:{b}" for r, g, b in row])
        print(f"Matrix saved to {path}")
    except Exception as e:
        print(f"Error saving matrix: {e}")

def erase_matrix():
    for y in range(MATRIX_HEIGHT):
        for x in range(MATRIX_WIDTH):
            matrix[y][x] = (0, 0, 0)

def drawing_loop():
    mpu6050_init()
    setup_all_encoders()
    GPIO.setup(SAVE_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    last_accel = read_acceleration()
    last_button_state = GPIO.input(SAVE_BUTTON)

    while True:
        shaken, last_accel = detect_shake(last_accel)
        if shaken:
            print("Shake detected! Erasing matrix...")
            erase_matrix()

        button_state = GPIO.input(SAVE_BUTTON)
        if last_button_state == 1 and button_state == 0:
            save_matrix_to_sd()
        last_button_state = button_state

        with position_lock:
            for user, (x, y) in positions.items():
                matrix[y][x] = colors[user]

        send_led_data()
        time.sleep(0.1)

# Flask web server for preview
app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return render_template_string("""
    <!doctype html>
    <html><head><title>LED Matrix Preview</title>
    <style>table { border-collapse: collapse; } td { width: 8px; height: 8px; }</style></head>
    <body>
    <h1>LED Matrix Preview</h1>
    <div id="matrix"></div>
    <script>
    function updateMatrix() {
        fetch('/matrix')
        .then(res => res.json())
        .then(data => {
            let html = '<table>';
            for (let row of data) {
                html += '<tr>';
                for (let pixel of row) {
                    html += `<td style="background: rgb(${pixel[0]},${pixel[1]},${pixel[2]})"></td>`;
                }
                html += '</tr>';
            }
            html += '</table>';
            document.getElementById('matrix').innerHTML = html;
        });
    }
    setInterval(updateMatrix, 500);
    </script>
    </body></html>
    """)

@app.route('/matrix')
def get_matrix():
    with position_lock:
        return jsonify(matrix)

if __name__ == '__main__':
    t = threading.Thread(target=drawing_loop)
    t.daemon = True
    t.start()
    app.run(host='0.0.0.0', port=8080)
