import os
import cv2
from picamera2 import Picamera2
from time import sleep

# Parametry
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
config = picam2.create_preview_configuration(main={"size": (image_width, image_height)})
picam2.configure(config)
picam2.set_controls({"Rotation": 180})
picam2.start()

sleep(2)  # poczekaj aż kamera się ustawi

print("Naciśnij i trzymaj klawisz 'x', aby robić zdjęcia. Wciśnij 'q', aby zakończyć.")

i = 0
try:
    while True:
        # Pobierz klatkę z kamery
        frame = picam2.capture_array()

        # Wyświetl obraz w oknie
        cv2.imshow("Podgląd (naciśnij 'x' by zrobić zdjęcie, 'q' by zakończyć)", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('x'):
            img_name = f"img_{i:03}.jpg"
            label_name = f"img_{i:03}.txt"

            img_path = os.path.join(image_dir, img_name)
            label_path = os.path.join(label_dir, label_name)

            # Zapisz zdjęcie
            cv2.imwrite(img_path, frame)
            open(label_path, 'w').close()

            print(f"[{i+1}] Zapisano: {img_path}, {label_path}")
            i += 1

            sleep(0.3)

        elif key == ord('q'):
            break

except KeyboardInterrupt:
    print("Zatrzymano ręcznie.")

cv2.destroyAllWindows()
picam2.close()
print("Gotowe – zdjęcia gotowe do oznaczenia.")
