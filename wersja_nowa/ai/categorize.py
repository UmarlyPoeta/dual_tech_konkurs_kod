import os
import cv2
import numpy as np
import onnxruntime as ort
from collections import Counter

# Ścieżki
MODEL_PATH = "model.onnx"
IMAGES_FOLDER = "images"
INPUT_SIZE = 640  # lub 416 – zależnie od modelu

# Nazwy klas (YOLOv8 domyślnie ma 80 klas COCO, możesz podać swoje)
CLASS_NAMES = ["T62", "T80U", "Tir", "czerwone auto", "fioletowy samochod", "hummer",
                "hummer niebieski", "radar", "samochod niebieski", "zielone auto", "autobus"]

# Załaduj model
session = ort.InferenceSession(MODEL_PATH)

def preprocess(image):
    image = cv2.resize(image, (INPUT_SIZE, INPUT_SIZE))
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = image.astype(np.float32) / 255.0
    image = np.transpose(image, (2, 0, 1))[np.newaxis, :]
    return image

def postprocess(outputs, conf_threshold=0.3):
    preds = outputs[0][0]  # [num_boxes, 85] dla YOLOv5/v8
    boxes = []
    class_ids = []
    for pred in preds:
        conf = pred[4]
        if conf > conf_threshold:
            class_scores = pred[5:]
            class_id = np.argmax(class_scores)
            boxes.append(pred[:4])
            class_ids.append(class_id)
    return class_ids

def categorize_image(image_path):
    image = cv2.imread(image_path)
    input_tensor = preprocess(image)
    outputs = session.run(None, {"images": input_tensor})
    class_ids = postprocess(outputs)

    if class_ids:
        most_common_class = Counter(class_ids).most_common(1)[0][0]
        return CLASS_NAMES[most_common_class]
    else:
        return "unknown"

# Przetwarzaj folder
results = []
for filename in os.listdir(IMAGES_FOLDER):
    if filename.lower().endswith((".jpg", ".jpeg", ".png")):
        path = os.path.join(IMAGES_FOLDER, filename)
        category = categorize_image(path)
        results.append((filename, category))
        print(f"{filename}: {category}")

# Zapisz wyniki do pliku
with open("results.txt", "w") as f:
    for filename, category in results:
        if category in ["T62", "T80U", "radar", "hummer", "hummer niebieski"]:
            d = "mil"
        else:
            d = "cyw"
        f.write(f"{filename}: {category} {d}\n")
