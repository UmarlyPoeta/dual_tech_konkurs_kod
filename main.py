import cv2
import RPi.GPIO as GPIO
import time
from picamera2 import Picamera2

# Setup silników
IN1, IN2, IN3, IN4 = 17, 18, 22, 23
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
for pin in [IN1, IN2, IN3, IN4]:
    GPIO.setup(pin, GPIO.OUT)

def forward():
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)

def backward():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)

def left():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)

def right():
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)

def stop():
    for pin in [IN1, IN2, IN3, IN4]:
        GPIO.output(pin, GPIO.LOW)

# Setup kamery
picam2 = Picamera2()
picam2.preview_configuration.main.size = (640, 480)
picam2.preview_configuration.main.format = "RGB888"
picam2.configure("preview")
picam2.start()

print("Steruj robotem za pomocą klawiszy: w/s/a/d, q - wyjście")

while True:
    frame = picam2.capture_array()
    cv2.imshow("Kamera", frame)
    key = cv2.waitKey(1)

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
