from datetime import datetime

# Ścieżka do portu UART
serial_port_path = "/dev/serial0"
output_file = "gps_log.csv"


# Konwersja NMEA (DDDMM.MMMM) do stopni dziesiętnych
def convert_to_degrees(raw_value, direction):
    if not raw_value or direction not in ["N", "S", "E", "W"]:
        return None
    degrees = int(float(raw_value) / 100)
    minutes = float(raw_value) - degrees * 100
    decimal = degrees + minutes / 60
    if direction in ["S", "W"]:
        decimal *= -1
    return round(decimal, 6)


# Otwórz port UART i plik do zapisu
with open(serial_port_path, "r") as serial_file, open(output_file, "a") as out:
    out.write("Timestamp,Latitude,Longitude\n")
    print("Odczyt GPS z $GPRMC")
    try:
        while True:
            line = serial_file.readline().strip()
            if line.startswith("$GPRMC"):
                parts = line.split(",")
                if len(parts) > 6 and parts[2] == "A":  # aktywny sygnał GPS
                    lat = convert_to_degrees(parts[3], parts[4])
                    lon = convert_to_degrees(parts[5], parts[6])
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"{timestamp} | LAT: {lat}, LON: {lon}")
                    out.write(f"{timestamp},{lat},{lon}\n")
    except KeyboardInterrupt:
        print("Zapis zakończony.")
