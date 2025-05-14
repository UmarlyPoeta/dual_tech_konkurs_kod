from flask import Flask, request
import RPi.GPIO as GPIO
import time

# Inicjalizacja Flask
app = Flask(__name__)

# Ustawienia GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Definicja pinów dla L298N
IN1 = 17
IN2 = 27
IN3 = 22
IN4 = 23
ENA = 24
ENB = 25

# Konfiguracja pinów jako wyjścia
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)
GPIO.setup(IN3, GPIO.OUT)
GPIO.setup(IN4, GPIO.OUT)
GPIO.setup(ENA, GPIO.OUT)
GPIO.setup(ENB, GPIO.OUT)

# Tworzenie obiektów PWM dla regulacji prędkości
pwm_A = GPIO.PWM(ENA, 1000)
pwm_B = GPIO.PWM(ENB, 1000)
pwm_A.start(50)  # Domyślna moc: 50%
pwm_B.start(50)

# Funkcje sterujące silnikami
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
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)

# Endpointy API do sterowania
@app.route('/move', methods=['GET'])
def move():
    direction = request.args.get('dir', default='', type=str)
    speed = request.args.get('speed', default=50, type=int)
    
    pwm_A.ChangeDutyCycle(speed)
    pwm_B.ChangeDutyCycle(speed)

    if direction == "forward":
        forward()
    elif direction == "backward":
        backward()
    elif direction == "left":
        left()
    elif direction == "right":
        right()
    elif direction == "stop":
        stop()
    else:
        return "Invalid direction", 400

    return f"Moving {direction} at speed {speed}"

# Uruchomienie serwera
if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000)  # Dostępne dla całej sieci lokalnej
    except KeyboardInterrupt:
        GPIO.cleanup()
