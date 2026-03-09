import serial
import pynmea2
import smbus2 as smbus
import time
import math
import threading

class Point:
    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude

class Gps:
    def __init__(self, PORT="/dev/ttyAMA3", BAUD=9600):
        self.gps = serial.Serial(PORT, BAUD, timeout=1)
        self.last_location = Point(-1, -1)
        self.last_num_sats = None
        self.last_num_visible_sats = None
        self._lock = threading.Lock()
        self.thread = threading.Thread(target=self.update_loop, daemon=True)
        self.thread.start()

    @staticmethod
    def _convert_dec_deg(value, direction) -> float:
        value = float(value)
        degrees = int(value//100)
        minutes = value-degrees*100
        decimal = degrees+minutes/60.0
        if direction in ("S", "W"):
            decimal = -decimal
        return decimal

    def update_loop(self):
        while True:
            try:
                line = self.gps.readline().decode("ascii", errors="ignore")
                
                # Check for location updates
                if line.startswith("$GPRMC") or line.startswith("$GNRMC"):
                    msg = pynmea2.parse(line)
                    if msg.status == 'A':
                        dec_deg_lat = self._convert_dec_deg(msg.lat, msg.lat_dir)
                        dec_deg_lon = self._convert_dec_deg(msg.lon, msg.lon_dir)
                        with self._lock:
                            self.last_location = Point(dec_deg_lat, dec_deg_lon)
                    else:
                        with self._lock:
                            self.last_location = Point(-2, -2)
                elif line.startswith("$GPGGA") or line.startswith("$GNGGA"):
                    msg = pynmea2.parse(line)
                    with self._lock:
                        self.last_num_sats = int(msg.num_sats) if msg.num_sats else None
                elif line.startswith("$GPGSV") or line.startswith("$GNGSV"):
                    msg = pynmea2.parse(line)
                    if msg.msg_num == '1':
                        with self._lock:
                            self.last_num_visible_sats = int(msg.num_sv_in_view) if msg.num_sv_in_view else None

            except pynmea2.ParseError:
                pass
            except Exception:
                time.sleep(0.1)

    # def update_satelite_count(self):
    #     line = self.gps.readline().decode("ascii", errors="ignore")
    #     if line.startswith("$GPGGA") or line.startswith("$GNGGA"):
    #         msg = pynmea2.parse(line)
    #         with self._lock:
    #             self.last_num_sats = msg.num_sats
    #
    #     with self._lock:
    #         self.last_num_sats = None
    #
    #
    # def update_location(self):
    #     while True:
    #         try:
    #             line = self.gps.readline().decode("ascii", errors="ignore")
    #             if line.startswith("$GPRMC") or line.startswith("$GNRMC"):
    #                 msg = pynmea2.parse(line)
    #                 if msg.status == 'A':
    #                     dec_deg_lat = self._convert_dec_deg(msg.lat, msg.lat_dir)
    #                     dec_deg_lon = self._convert_dec_deg(msg.lon, msg.lon_dir)
    #                     with self._lock:
    #                         self.last_location = Point(dec_deg_lat, dec_deg_lon)
    #                     continue
    #                 else:
    #                     with self._lock:
    #                         self.last_location = Point(-2, -2)
    #         except pynmea2.ParseError:
    #             pass

    def get_satelite_count(self):
        with self._lock:
            return self.last_num_sats

    def get_visible_satelite_count(self):
        with self._lock:
            return self.last_num_visible_sats

    def get_location(self):
        with self._lock:
            return self.last_location

    def flush(self):
        with self._lock:
            self.gps.reset_input_buffer()

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
        heading += self.declination_rad
        if heading < 0:
            heading += 2 * math.pi
        if heading > 2 * math.pi:
            heading -= 2 * math.pi
        return math.degrees(heading)

if __name__ == "__main__":
    gps = Gps("/dev/ttyAMA3", 9600)
    compass = Compass()
    while True:
        curr_location = gps.get_location()
        longitude = curr_location.longitude
        latitude = curr_location.latitude
        heading = compass.get_heading()
        sat_count = gps.get_satelite_count()
        visible_sat_count = gps.get_visible_satelite_count()
        print(f"heading: {heading}")
        print(f"longitude: {longitude} | latitude: {latitude}")
        print(f"satelite count: {sat_count}")
        print(f"visible satelite count: {visible_sat_count}")
