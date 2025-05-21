import cv2
import time
from picamera2 import Picamera2
from pyzbar.pyzbar import decode
from PIL import Image
import numpy as np
import json
import datetime
import serial

# --- RAPORT ---
objects = []


# --- GPS ---
def parse_coordinate(value, direction):
    if not value or not direction:
        return None
    try:
        degrees = int(value[:2 if direction in "NS" else 3])
        minutes = float(value[2 if direction in "NS" else 3:])
        decimal = degrees + minutes / 60
        if direction in ["S", "W"]:
            decimal *= -1
        return round(decimal, 6)
    except ValueError:
        return None

def get_gps_location():
    try:
        with serial.Serial("/dev/ttyAMA0", baudrate=115200, timeout=1) as gps:
            timeout = time.time() + 3
            while time.time() < timeout:
                line = gps.readline().decode(errors="ignore").strip()
                if line.startswith("$GNGGA") or line.startswith("$GPGGA"):
                    fields = line.split(",")
                    if len(fields) >= 11:
                        time_str = fields[1]
                        lat = parse_coordinate(fields[2], fields[3])
                        lon = parse_coordinate(fields[4], fields[5])
                        altitude = fields[9]
                        if lat is not None and lon is not None:
                            hh, mm, ss = time_str[0:2], time_str[2:4], time_str[4:6]
                            formatted_time = f"{hh}:{mm}:{ss}"
                            formatted_lat = f"{lat:.7f}"
                            formatted_lon = f"{lon:.7f}"
                            formatted_alt = f"{float(altitude):.2f}"
                            return formatted_time, formatted_lat, formatted_lon, formatted_alt
    except Exception as e:
        print(f"GPS error: {e}")
    return "brak GPS", "N/A", "N/A", "N/A"


# --- GPIO silników ---
IN1, IN2, IN3, IN4 = 17, 22, 23, 24
from gpiozero import Motor
from time import sleep

# Silniki (zakładam dwa silniki: lewy i prawy)
# Dostosuj piny do swojego układu!
left_motor = Motor(forward=17, backward=22)
right_motor = Motor(forward=23, backward=24)

def forward():
    left_motor.forward()
    right_motor.forward()

def backward():
    left_motor.backward()
    right_motor.backward()

def left():
    left_motor.backward()
    right_motor.forward()

def right():
    left_motor.forward()
    right_motor.backward()

def stop():
    left_motor.stop()
    right_motor.stop()

# --- Kamera ---
picam2 = Picamera2()
picam2.preview_configuration.main.size = (640, 480)
picam2.preview_configuration.main.format = "RGB888"
picam2.configure("preview")
picam2.start()

# --- Logi i śledzenie ruchu ---
movement_log = []
start_time = None
TRACK_FILE = "track_log.json"

def log_movement(action):
    global start_time
    if start_time:
        duration = time.time() - start_time
        if movement_log:
            movement_log[-1][2] = duration
    start_time = time.time()
    movement_log.append([action, start_time, 0])

# --- Main loop ---
last_data = None
current_mode = "manual"

print("Tryby: ręczny (sterowanie: w/s/a/d, x-stop, m-zapis trasy, t-tryb auto), q - wyjście")

while True:
    frame = picam2.capture_array()
    image = Image.fromarray(frame)
    decoded_objects = decode(image)

    for obj in decoded_objects:
        data = obj.data.decode('utf-8')
        if data and data != last_data:
            print(f"Znaleziono QR: {data}")
            timestamp = time.strftime('%H:%M:%S')
            gps_time, lat, lon, _ = get_gps_location()
            with open(".txt", "a") as f:
                f.write(f"{timestamp} - QR: {data} | GPS {gps_time} - Lat: {lat}, Lon: {lon}\n")
            last_data = data

        pts = obj.polygon
        if len(pts) > 1:
            for i in range(len(pts)):
                pt1 = (pts[i].x, pts[i].y)
                pt2 = (pts[(i + 1) % len(pts)].x, pts[(i + 1) % len(pts)].y)
                cv2.line(frame, pt1, pt2, (0, 255, 0), 2)

    cv2.imshow("Kamera", frame)
    key = cv2.waitKey(1) & 0xFF

    with open("trasa.log", "a", encoding="utf-8") as f:
        now = datetime.now()
        formatted_time = now.strftime("%H:%M:%S.") + str(int(now.microsecond / 100000))
        _ , lat, lon, alt = get_gps_location()
        f.write(f"{formatted_time} {lat} {lon} {alt}")

    if current_mode == "manual":
        if key == ord('w'):
            forward(); log_movement("forward")
        elif key == ord('s'):
            backward(); log_movement("backward")
        elif key == ord('a'):
            left(); log_movement("left")
        elif key == ord('d'):
            right(); log_movement("right")
        elif key == ord('x'):
            stop(); log_movement("stop")
        elif key == ord('m'):
            with open(TRACK_FILE, "w") as f:
                json.dump(movement_log, f)
            print("Trasa zapisana.")
        elif key == ord('t'):
            stop()
            current_mode = "auto"
            print("== Przełączenie na tryb automatyczny ==")
        elif key == ord('q'):
            stop()
            break

    elif current_mode == "auto":
        print("== Tryb automatyczny: odtwarzanie trasy ==")
        try:
            with open(TRACK_FILE, "r") as f:
                recorded_track = json.load(f)
            print(f"Odtwarzanie {len(recorded_track)} kroków...")
            for move, _, duration in recorded_track:
                if move == 'forward':
                    forward()
                elif move == 'backward':
                    backward()
                elif move == 'left':
                    left()
                elif move == 'right':
                    right()
                elif move == 'stop':
                    stop()
                time.sleep(duration)
            stop()
            print("== Koniec trasy. Powrót do trybu manualnego ==")
        except FileNotFoundError:
            print("Brak zapisu trasy!")
        current_mode = "manual"

cv2.destroyAllWindows()

