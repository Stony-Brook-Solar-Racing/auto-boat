import serial
import pynmea2
import smbus
import time
import math


class Point:
    def __init__(self, latitude, longitude):
        self.longitude = longitude
        self.latitude = latitude

class Gps:
    def __init__(self, PORT, BAUD):
        self.gps = serial.Serial(PORT, BAUD, timeout=1)

    @staticmethod
    def _convert_dec_deg(value, direction):
        value = float(value)
        degrees = int(value//100)
        minutes = value-degrees*100
        decimal = degrees+minutes/60.0
        if direction in ("S", "W"):
            decimal = -decimal
        return decimal

    def get_location(self):
        count = 20
        while count > 0:
            line = self.gps.readline().decode("ascii", errors="ignore")
            if line.startswith("$GPRMC"):
                msg = pynmea2.parse(line)
                dec_deg_lat = self._convert_dec_deg(msg.lat, msg.lat_dir)
                dec_deg_lon = self._convert_dec_deg(msg.lon, msg.lon_dir)
                return Point(dec_deg_lat, dec_deg_lon)
            count -= 1
        return None

class Compass:
    def __init__(self, bus_num=1, addr=0x1E, declination_deg=0.0):
        self.bus = smbus.SMBus(bus_num)
        self.addr = addr
        self.declination_rad = math.radians(declination_deg)

        self.bus.write_byte_data(self.addr, 0x00, 0x70)
        self.bus.write_byte_data(self.addr, 0x01, 0x20)
        self.bus.write_byte_data(self.addr, 0x02, 0x00)
        time.sleep(1)

    @staticmethod
    def _twos_complement(val, bits):
        if val & (1 << (bits - 1)):
            val -= (1 << bits)
        return val

    def _read_axis():
        

    def get_heading(self):
        pass
