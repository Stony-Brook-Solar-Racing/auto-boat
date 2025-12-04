import serial
import pynmea2

class Gps:
    def __init__(self, PORT, BAUD):
        self.gps = serial.Serial(PORT, BAUD, timeout=1)

    def get_location(self):
        line = self.gps.readline().decode('ascii', errors='ignore')
        if line.startswith('$GPRMC'):
            msg = pynmea2.parse(line)

class Point:
    def __init__ (self, latitude, longtitude):
        self.longtitude = longtitude
        self.latitude = latitude
