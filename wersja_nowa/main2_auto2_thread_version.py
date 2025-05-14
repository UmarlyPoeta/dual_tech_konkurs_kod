import cv2
import RPi.GPIO as GPIO
import time
from picamera2 import Picamera2
from pyzbar.pyzbar import decode
from PIL import Image
import numpy as np
import json
import datetime
import serial
import threading

# --- RAPORT ---
objects = []

# --- GLOBALNE ZMIENNE ---
latest_gps = {"time": "brak GPS", "lat": "N/A", "lon": "N/A", "alt": "N/A"}
last_qr_data = None
gps_lock = threading.Lock()
qr_lock = threading.Lock()
frame_for_qr = None
qr_result = None
movement_log = []
start_time = None

# --- GPIO silników ---
IN1, IN2, IN3, IN4 = 17, 22, 23, 24
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
for pin in [IN1, IN2, IN3, IN4]:
    GPIO.setup(pin, GPIO.OUT)

def forward(): GPIO.output(IN1, 1); GPIO.output(IN2, 0); GPIO.output(IN3, 1); GPIO.output(IN4, 0)
def backward(): GPIO.output(IN1, 0); GPIO.output(IN2, 1); GPIO.output(IN3, 0); GPIO.output(IN4, 1)
def left(): GPIO.output(IN1, 0); GPIO.output(IN2, 1); GPIO.output(IN3, 1); GPIO.output(IN4, 0)
def right(): GPIO.output(IN1, 1); GPIO.output(IN2, 0); GPIO.output(IN3, 0); GPIO.output(IN4, 1)
def stop(): [GPIO.output(pin, 0) for pin in [IN1, IN2, IN3, IN4]]

# --- GPS funkcje ---
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

def gps_thread():
    global latest_gps
    try:
        with serial.Serial("/dev/ttyAMA0", baudrate=115200, timeout=1) as gps:
            while True:
                line = gps.readline().decode(errors="ignore").strip()
                if line.startswith("$GNGGA") or line.startswith("$GPGGA"):
                    fields = line.split(",")
                    if len(fields) >= 11:
                        time_str = fields[1]
                        lat = parse_coordinate(fields[2], fields[3])
                        lon = parse_coordinate(fields[4], fields[5])
                        altitude = fields[9]
                        if lat and lon:
                            hh, mm, ss = time_str[0:2], time_str[2:4], time_str[4:6]
                            with gps_lock:
                                latest_gps = {
                                    "time": f"{hh}:{mm}:{ss}",
                                    "lat": f"{lat:.7f}",
                                    "lon": f"{lon:.7f}",
                                    "alt": f"{float(altitude):.2f}"
                                }
    except Exception as e:
        print("Błąd GPS:", e)

# --- QR thread ---
def qr_thread():
    global frame_for_qr, qr_result
    while True:
        if frame_for_qr is not None:
            image = Image.fromarray(frame_for_qr)
            decoded_objects = decode(image)
            with qr_lock:
                qr_result = decoded_objects
            frame_for_qr = None
        time.sleep(0.1)

# --- Log ruchu ---
def log_movement(action):
    global start_time
    if start_time:
        duration = time.time() - start_time
        if movement_log:
            movement_log[-1][2] = duration
    start_time = time.time()
    movement_log.append([action, start_time, 0])

# --- Inicjalizacja kamery ---
picam2 = Picamera2()
picam2.preview_configuration.main.size = (320, 240)
picam2.preview_configuration.main.format = "RGB888"
picam2.configure("preview")
picam2.start()
time.sleep(0.5)

# --- Start wątków ---
threading.Thread(target=gps_thread, daemon=True).start()
threading.Thread(target=qr_thread, daemon=True).start()

print("Tryby: ręczny (w/s/a/d, x-stop, m-zapis trasy, t-auto), q - wyjście")
current_mode = "manual"
frame_count, last_write = 0, time.time()

while True:
    frame = picam2.capture_array("main")
    frame_count += 1

    # co 5 klatek: uruchamiamy dekodowanie QR
    if frame_count % 5 == 0:
        frame_for_qr = frame.copy()

    # Rysowanie QR
    with qr_lock:
        if qr_result:
            for obj in qr_result:
                data = obj.data.decode('utf-8')
                if data != last_qr_data:
                    print(f"Znaleziono QR: {data}")
                    with gps_lock:
                        gps = latest_gps.copy()
                    timestamp = time.strftime('%H:%M:%S')
                    with open("qr_log.txt", "a") as f:
                        f.write(f"{timestamp} - QR: {data} | GPS {gps['time']} - Lat: {gps['lat']}, Lon: {gps['lon']}\n")
                    last_qr_data = data

                pts = obj.polygon
                for i in range(len(pts)):
                    pt1 = (pts[i].x, pts[i].y)
                    pt2 = (pts[(i + 1) % len(pts)].x, pts[(i + 1) % len(pts)].y)
                    cv2.line(frame, pt1, pt2, (0, 255, 0), 2)

    cv2.imshow("Kamera", frame)
    key = cv2.waitKey(1) & 0xFF

    # Buforowany zapis trasy co sekundę
    if time.time() - last_write >= 1:
        with gps_lock:
            gps = latest_gps.copy()
        formatted_time = datetime.datetime.now().strftime("%H:%M:%S.") + str(int(datetime.datetime.now().microsecond / 100000))
        with open("trasa.log", "a", encoding="utf-8") as f:
            f.write(f"{formatted_time} {gps['lat']} {gps['lon']} {gps['alt']}\n")
        last_write = time.time()

    # Sterowanie ręczne
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
            with open("track_log.json", "w") as f:
                json.dump(movement_log, f)
            print("Trasa zapisana.")
        elif key == ord('t'):
            stop()
            current_mode = "auto"
            print("== Tryb automatyczny ==")
        elif key == ord('q'):
            stop()
            break

    elif current_mode == "auto":
        print("== Tryb auto: odtwarzanie ==")
        try:
            with open("track_log.json", "r") as f:
                track = json.load(f)
            for move, _, dur in track:
                if move == 'forward': forward()
                elif move == 'backward': backward()
                elif move == 'left': left()
                elif move == 'right': right()
                elif move == 'stop': stop()
                time.sleep(dur)
            stop()
            print("== Koniec trasy ==")
        except FileNotFoundError:
            print("Brak pliku trasy!")
        current_mode = "manual"

cv2.destroyAllWindows()
GPIO.cleanup()
