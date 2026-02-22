import serial
import pynmea2
import smbus2 as smbus
import time
import math

class Point:
    def __init__(self, latitude, longitude):
        self.longitude = longitude
        self.latitude = latitude

class Gps:
    def __init__(self, PORT="/dev/ttyAMA3", BAUD=9600):
        self.gps = serial.Serial(PORT, BAUD, timeout=1)

    @staticmethod
    def _convert_dec_deg(value, direction) -> float:
        value = float(value)
        degrees = int(value//100)
        minutes = value-degrees*100
        decimal = degrees+minutes/60.0
        if direction in ("S", "W"):
            decimal = -decimal
        return decimal

    def get_satelite_count(self):
        line = self.gps.readline().decode("ascii", errors="ignore")
        if line.startswith("$GPGGA") or line.startswith("$GNGGA"):
            msg = pynmea2.parse(line)
            return(msg.num_sats)

    def get_location(self) -> Point:
        count = 20
        while count > 0:
            line = self.gps.readline().decode("ascii", errors="ignore")
            if line.startswith("$GPRMC") or line.startswith("$GNRMC"):
                msg = pynmea2.parse(line)
                if msg.status == 'A':
                    dec_deg_lat = self._convert_dec_deg(msg.lat, msg.lat_dir)
                    dec_deg_lon = self._convert_dec_deg(msg.lon, msg.lon_dir)
                    return Point(dec_deg_lat, dec_deg_lon)
                else:
                    return Point(-2, -2)
            count -= 1
        return Point(-1, -1)

class Compass:
    def __init__(self, bus_num=1, addr=0x1E, declination_deg=0.0):
        self.compass = smbus.SMBus(bus_num)
        self.addr = addr
        self.declination_rad = math.radians(declination_deg)

        self.compass.write_byte_data(self.addr, 0x00, 0x70)
        self.compass.write_byte_data(self.addr, 0x01, 0x20)
        self.compass.write_byte_data(self.addr, 0x02, 0x00)
        time.sleep(1)

    @staticmethod
    def _twos_complement(val, bits) -> float:
        if val & (1 << (bits - 1)):
            val -= (1 << bits)
        return val

    def _read_axis(self) -> tuple[float, float, float]:
        data = self.compass.read_i2c_block_data(self.addr, 0x03, 6)
        x = self._twos_complement(data[0] << 8 | data[1], 16)
        z = self._twos_complement(data[2] << 8 | data[3], 16)
        y = self._twos_complement(data[4] << 8 | data[5], 16)
        return x, y, z

    def get_heading(self) -> float:
        x, y, _ = self._read_axis()
        # In radians btw
        heading = math.atan2(y,x)
        if heading < 0:
            heading += 2 * math.pi
        if heading > 2 * math.pi:
            heading -= 2 * math.pi
        return math.degrees(heading)

if __name__ == "__main__":
    gps = Gps("/dev/ttyAMA3", 9600)
    compass = Compass()
    while True:
        longitude = gps.get_location().longitude
        heading = compass.get_heading()
        sat_count = gps.get_satelite_count()
        print(heading)
        print(longitude)
        print(sat_count)
