import cv2
import time
from picamera2 import Picamera2
from pyzbar.pyzbar import decode
from PIL import Image
import numpy as np
import json
import datetime
import serial
import threading
import onnxruntime as ort

# --- RAPORT ---
objects = []

def rozpoznaj_grafike_pod_qr(frame, bbox_qr):
    pts = np.array([(pt.x, pt.y) for pt in bbox_qr], dtype=np.float32)
    x, y, w, h = cv2.boundingRect(pts)
    margin = int(h * 0.6)
    y2 = y + h + margin
    roi = frame[y + h:y2, x:x + w]
    if roi.size == 0:
        return "---"

    best_match = "---"
    best_score = float("inf")

    for i in range(1, 11):
        try:
            template = cv2.imread(f"{i}.JPG", cv2.IMREAD_GRAYSCALE)
            roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            template_resized = cv2.resize(template, (roi_gray.shape[1], roi_gray.shape[0]))
            diff = cv2.absdiff(template_resized, roi_gray)
            score = np.sum(diff)
            if score < best_score:
                best_score = score
                best_match = f"{i}.JPG"
        except Exception as e:
            print(f"Błąd porównania z {i}.JPG:", e)

    return best_match


# --- MODEL ---

session = ort.InferenceSession("best.onnx")

class_labels = ["T62", "T80U", "Tir", "czerwone auto", "fioletowy samochod", "hummer",
                "hummer niebieski", "radar", "samochod niebieski", "zielone auto", "autobus"]

def preprocess(image):
    img = cv2.resize(image, (640, 640))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))
    img = np.expand_dims(img, axis=0)
    return img

def detect_objects(image):
    input_tensor = preprocess(image)
    outputs = session.run(None, {"images": input_tensor})[0]
    results = []
    for det in outputs[0]:
        x0, y0, x1, y1, score, class_id = det[:6]
        if score > 0.5:
            class_id = int(class_id)
            label = class_labels[class_id]
            results.append({
                "bbox": (int(x0), int(y0), int(x1), int(y1)),
                "score": float(score),
                "label": label
            })
    return results


# --- GLOBALNE ZMIENNE ---
latest_gps = {"time": "brak GPS", "lat": "N/A", "lon": "N/A", "alt": "N/A"}
last_qr_data = None
gps_lock = threading.Lock()
qr_lock = threading.Lock()
frame_for_qr = None
qr_result = None
movement_log = []
start_time = None

from gpiozero import DigitalOutputDevice

# Przypisanie numerów pinów BCM
IN1_pin = 17
IN2_pin = 22
IN3_pin = 23
IN4_pin = 24

# Inicjalizacja pinów jako wyjścia
IN1 = DigitalOutputDevice(IN1_pin)
IN2 = DigitalOutputDevice(IN2_pin)
IN3 = DigitalOutputDevice(IN3_pin)
IN4 = DigitalOutputDevice(IN4_pin)

def set_gpio_state(state):
    # state: lista 4 elementów (0 lub 1) dla pinów [IN1, IN2, IN3, IN4]
    IN1.value = state[0]
    IN2.value = state[1]
    IN3.value = state[2]
    IN4.value = state[3]

def forward():
    set_gpio_state([1, 0, 1, 0])

def backward():
    set_gpio_state([0, 1, 0, 1])

def left():
    set_gpio_state([0, 1, 1, 0])

def right():
    set_gpio_state([1, 0, 0, 1])

def stop():
    set_gpio_state([0, 0, 0, 0])

# --- GPS funkcje ---
def parse_coordinate(value, direction):
    if not value or not direction:
        return None
    try:
        deg_len = 2 if direction in "NS" else 3
        degrees = int(value[:deg_len])
        minutes = float(value[deg_len:])
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
                        if lat is not None and lon is not None:
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
    
    if frame_count % 10 == 0:
        detections = detect_objects(frame)
        for i, det in enumerate(detections):
            x0, y0, x1, y1 = det["bbox"]
            label = det["label"]
            crop = frame[y0:y1, x0:x1]

            if label in ["T62", "T80U", "radar"]:
                category = "mil"
            elif label in ["Tir", "autobus"]:
                category = "civil"
            else:
                category = "---"

            typ = label.replace(" ", "_").lower()

            with gps_lock:
                gps = latest_gps.copy()
            lat = gps["lat"] if gps["lat"] != "N/A" else "00.00000000"
            lon = gps["lon"] if gps["lon"] != "N/A" else "00.00000000"

            qr_data = last_qr_data if last_qr_data else "---"

            img_filename = f"zdj{frame_count}_{i}.png"
            cv2.imwrite(img_filename, crop)

            obj_num = len(objects) + 1

            entry = f"{obj_num}  {lat} {lon}   {category}   {typ}   {qr_data}  {img_filename}"
            print("Dodano wpis:", entry)
            objects.append(entry)

            with open("rozpoznane_obiekty.txt", "a") as f:
                f.write(entry + "\n")

    if frame_count % 5 == 0:
        frame_for_qr = frame.copy()

    with qr_lock:
        if qr_result:
            for obj in qr_result:
                data = obj.data.decode('utf-8')
                if data != last_qr_data:
                    print(f"Znaleziono QR: {data}")
                    grafika = rozpoznaj_grafike_pod_qr(frame, obj.polygon)
                    print(f"Pod kodem QR znajduje się grafika: {grafika}")
                    last_qr_data = f"{data} ({grafika})"

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

    frame = cv2.flip(frame, 0)
    cv2.imshow("Kamera", frame)
    key = cv2.waitKey(1) & 0xFF

    if time.time() - last_write >= 1:
        with gps_lock:
            gps = latest_gps.copy()
        formatted_time = datetime.datetime.now().strftime("%H:%M:%S.") + str(int(datetime.datetime.now().microsecond / 100000))
        with open("trasa.log", "a", encoding="utf-8") as f:
            f.write(f"{formatted_time} {gps['lat']} {gps['lon']} {gps['alt']}\n")
        last_write = time.time()

    if current_mode == "manual":
        if key == ord('w'):
            forward()
            log_movement("forward")
        elif key == ord('s'):
            backward()
            log_movement("backward")
        elif key == ord('a'):
            left()
            log_movement("left")
        elif key == ord('d'):
            right()
            log_movement("right")
        elif key == ord('x'):
            stop()
            log_movement("stop")
        elif key == ord('m'):
            stop()
            with open("trasa.log", "r") as f:
                content = f.read()
            print("Zawartość trasy.log:\n", content)
        elif key == ord('t'):
            current_mode = "auto"
            print("Przełączono na tryb automatyczny")
        elif key == ord('q'):
            break
    elif current_mode == "auto":
        # Możesz dodać logikę automatycznego sterowania
        pass

# Zwolnienie GPIO i zamknięcie okien
stop()
cv2.destroyAllWindows()
