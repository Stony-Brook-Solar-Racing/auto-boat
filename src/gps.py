import serial
import pynmea2

def _convert_dec_deg(value, direction):
    value = float(value)
    degrees = int(value//100)
    minutes = value-degrees*100
    decimal = degrees+minutes/60.0
    if direction in ("S", "W"):
        decimal = -decimal
    return decimal

class Gps:
    def __init__(self, PORT, BAUD):
        self.gps = serial.Serial(PORT, BAUD, timeout=1)

    def get_location(self):
        count = 20
        while count > 0:
            line = self.gps.readline().decode("ascii", errors="ignore")
            if line.startswith("$GPRMC"):
                msg = pynmea2.parse(line)
                dec_deg_lat = _convert_dec_deg(msg.lat, msg.lat_dir)
                dec_deg_lon = _convert_dec_deg(msg.lon, msg.lon_dir)
                return Point(dec_deg_lat, dec_deg_lon)
            count -= 1
        return None

class Point:
    def __init__ (self, latitude, longtitude):
        self.longtitude = longtitude
        self.latitude = latitude
