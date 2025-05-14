import time


# --- Funkcja do parsowania GPS ---
def parse_coordinate(value, direction):
    if not value or not direction:
        return None
    try:
        degrees = int(value[:2 if direction in "NS" else 3])
        minutes = float(value[2 if direction in "NS" else 3:])
        decimal = degrees + minutes / 60
        if direction in ["S", "W"]:
            decimal *= -1
        return round(decimal, 6)
    except ValueError:
        return None

def get_gps_location():
    try:
        with open("/dev/serial0", "r", buffering=1) as gps:
            timeout = time.time() + 3  # max 3 sekundy na odczyt
            while time.time() < timeout:
                line = gps.readline().strip()
                if line.startswith("$GNGGA") or line.startswith("$GPGGA"):
                    fields = line.split(",")
                    if len(fields) >= 6:
                        time_str = fields[1]
                        lat = parse_coordinate(fields[2], fields[3])
                        lon = parse_coordinate(fields[4], fields[5])
                        if lat is not None and lon is not None:
                            hh, mm, ss = time_str[0:2], time_str[2:4], time_str[4:6]
                            return f"{hh}:{mm}:{ss}", f"{lat}°", f"{lon}°"
    except Exception as e:
        print(f"GPS error: {e}")
    return "brak GPS", "N/A", "N/A"
