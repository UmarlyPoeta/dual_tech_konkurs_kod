import RPi.GPIO as GPIO


# --- Setup silników ---
IN1, IN2, IN3, IN4 = 17, 18, 22, 23
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
for pin in [IN1, IN2, IN3, IN4]:
    GPIO.setup(pin, GPIO.OUT)

# --- funkcje do poruszania sie ---
def forward(): GPIO.output(IN1, GPIO.HIGH); GPIO.output(IN2, GPIO.LOW); GPIO.output(IN3, GPIO.HIGH); GPIO.output(IN4, GPIO.LOW)
def backward(): GPIO.output(IN1, GPIO.LOW); GPIO.output(IN2, GPIO.HIGH); GPIO.output(IN3, GPIO.LOW); GPIO.output(IN4, GPIO.HIGH)
def left(): GPIO.output(IN1, GPIO.LOW); GPIO.output(IN2, GPIO.HIGH); GPIO.output(IN3, GPIO.HIGH); GPIO.output(IN4, GPIO.LOW)
def right(): GPIO.output(IN1, GPIO.HIGH); GPIO.output(IN2, GPIO.LOW); GPIO.output(IN3, GPIO.LOW); GPIO.output(IN4, GPIO.HIGH)
def stop(): [GPIO.output(pin, GPIO.LOW) for pin in [IN1, IN2, IN3, IN4]]
