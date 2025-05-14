from camera import *
from engine import *
from gps import *
from pyzbar.pyzbar import decode
from PIL import Image
import numpy as np

def main():
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


if __name__ == "__main__":
    main()