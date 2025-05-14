import cv2
import numpy as np
from flask import Flask, Response

# Załaduj model YOLOv5 ONNX
net = cv2.dnn.readNetFromONNX("/home/pi/yolov5n.onnx")

app = Flask(__name__)

def generate_frames():
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # YOLO przetwarzanie
        blob = cv2.dnn.blobFromImage(frame, scalefactor=1/255.0, size=(640, 640), swapRB=True, crop=False)
        net.setInput(blob)
        detections = net.forward()

        # Rysowanie detekcji (dla uproszczenia tylko bboxy)
        for detection in detections[0, 0]:
            confidence = detection[2]
            if confidence > 0.5:
                x1, y1, x2, y2 = map(int, detection[3:7] * [frame.shape[1], frame.shape[0], frame.shape[1], frame.shape[0]])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
