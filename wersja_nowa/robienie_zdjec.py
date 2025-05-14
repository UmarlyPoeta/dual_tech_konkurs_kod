import os
from picamera2 import Picamera2
from time import sleep

# Parametry
num_images = 100
image_width = 1280
image_height = 720
output_base = "dataset"
image_dir = os.path.join(output_base, "images", "train")
label_dir = os.path.join(output_base, "labels", "train")

# Utwórz katalogi zgodne z formatem YOLO
os.makedirs(image_dir, exist_ok=True)
os.makedirs(label_dir, exist_ok=True)

# Inicjalizacja kamery
picam2 = Picamera2()
config = picam2.create_still_configuration(main={"size": (image_width, image_height)})
picam2.configure(config)

# Obróć kamerę o 180 stopni w pionie
picam2.set_controls({"Rotation": 180})

picam2.start()

sleep(2)  # poczekaj aż kamera się ustawi

print(f"Zaczynam robienie {num_images} zdjęć do YOLO...")

for i in range(num_images):
    img_name = f"img_{i:03}.jpg"
    label_name = f"img_{i:03}.txt"

    img_path = os.path.join(image_dir, img_name)
    label_path = os.path.join(label_dir, label_name)

    # Zrób zdjęcie
    picam2.capture_file(img_path)

    # Utwórz pusty plik etykiety (do późniejszego oznaczenia)
    open(label_path, 'w').close()

    print(f"[{i+1}/{num_images}] Zapisano: {img_path}, {label_path}")

    # Czekaj 0.3 sekundy – na zmianę pozycji obiektu
    sleep(0.3)

print("Gotowe – zdjęcia gotowe do oznaczenia.")
picam2.close()
