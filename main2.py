import cv2
import RPi.GPIO as GPIO
import time
from picamera2 import Picamera2
from pyzbar.pyzbar import decode
from PIL import Image
import numpy as np

# --- Funkcja do parsowania GPS ---
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
        with open("/dev/serial0", "r", buffering=1) as gps:
            timeout = time.time() + 3  # max 3 sekundy na odczyt
            while time.time() < timeout:
                line = gps.readline().strip()
                if line.startswith("$GNGGA") or line.startswith("$GPGGA"):
                    fields = line.split(",")
                    if len(fields) >= 6:
                        time_str = fields[1]
                        lat = parse_coordinate(fields[2], fields[3])
                        lon = parse_coordinate(fields[4], fields[5])
                        if lat is not None and lon is not None:
                            hh, mm, ss = time_str[0:2], time_str[2:4], time_str[4:6]
                            return f"{hh}:{mm}:{ss}", f"{lat}°", f"{lon}°"
    except Exception as e:
        print(f"GPS error: {e}")
    return "brak GPS", "N/A", "N/A"

# --- Setup silników ---
IN1, IN2, IN3, IN4 = 17, 18, 22, 23
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
for pin in [IN1, IN2, IN3, IN4]:
    GPIO.setup(pin, GPIO.OUT)

def forward(): GPIO.output(IN1, GPIO.HIGH); GPIO.output(IN2, GPIO.LOW); GPIO.output(IN3, GPIO.HIGH); GPIO.output(IN4, GPIO.LOW)
def backward(): GPIO.output(IN1, GPIO.LOW); GPIO.output(IN2, GPIO.HIGH); GPIO.output(IN3, GPIO.LOW); GPIO.output(IN4, GPIO.HIGH)
def left(): GPIO.output(IN1, GPIO.LOW); GPIO.output(IN2, GPIO.HIGH); GPIO.output(IN3, GPIO.HIGH); GPIO.output(IN4, GPIO.LOW)
def right(): GPIO.output(IN1, GPIO.HIGH); GPIO.output(IN2, GPIO.LOW); GPIO.output(IN3, GPIO.LOW); GPIO.output(IN4, GPIO.HIGH)
def stop(): [GPIO.output(pin, GPIO.LOW) for pin in [IN1, IN2, IN3, IN4]]

# --- Setup kamery ---
picam2 = Picamera2()
picam2.preview_configuration.main.size = (640, 480)
picam2.preview_configuration.main.format = "RGB888"
picam2.configure("preview")
picam2.start()


last_data = None

print("Steruj robotem za pomocą klawiszy: w/s/a/d, x - stop, q - wyjście")

while True:
    frame = picam2.capture_array()
    image = Image.fromarray(frame)
    decoded_objects = decode(image)

    for obj in decoded_objects:
        data = obj.data.decode('utf-8')

        if data and data != last_data:
            print(f"Znaleziono QR: {data}")
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            gps_time, lat, lon = get_gps_location()
            with open("qr_codes.txt", "a") as f:
                f.write(f"{timestamp} - QR: {data} | GPS {gps_time} - Lat: {lat}, Lon: {lon}\n")
            last_data = data

        # Rysowanie ramki wokół QR (opcjonalnie z użyciem cv2 lub innej biblioteki graficznej)
        pts = obj.polygon
        if len(pts) > 1:
            for i in range(len(pts)):
                pt1 = (pts[i].x, pts[i].y)
                pt2 = (pts[(i + 1) % len(pts)].x, pts[(i + 1) % len(pts)].y)
                cv2.line(frame, pt1, pt2, (0, 255, 0), 2)

    cv2.imshow("Kamera", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord('w'):
        forward()
    elif key == ord('s'):
        backward()
    elif key == ord('a'):
        left()
    elif key == ord('d'):
        right()
    elif key == ord('x'):
        stop()
    elif key == ord('q'):
        stop()
        break

cv2.destroyAllWindows()
GPIO.cleanup()
