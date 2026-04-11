import serial
import pynmea2
import smbus2 as smbus
import time
import math
import threading

class Point:
    def __init__(self, latitude, longitude):
        self.longitude = longitude
        self.latitude = latitude

class Gps:
    def __init__(self, PORT="/dev/ttyAMA3", BAUD=9600):
        self.gps = serial.Serial(PORT, BAUD, timeout=1)
        self.last_location = None
        self.last_num_sats = None
        self.last_num_visible_sats = None
        self._lock = threading.Lock()
        self.thread = threading.Thread(target=self.update_loop, daemon=True)
        self.thread
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
                            self.last_location = None
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

    def get_satelite_count(self):
        return self.get_satelite_count

    def get_location(self):
        with self._lock:
            return self.last_location

    def flush(self):
        with self._lock:
            self.gps.reset_input_buffer()

class MPU6050:
    def __init__(self, bus_num=1, addr=0x68):
        self.bus = smbus.SMBus(bus_num)
        self.addr = addr
        # Wake up the MPU-6050 (Write 0 to power management register 1)
        self.bus.write_byte_data(self.addr, 0x6B, 0x00)
        time.sleep(0.1)

    @staticmethod
    def _twos_complement(val, bits) -> float:
        if val & (1 << (bits - 1)):
            val -= (1 << bits)
        return val

    def read_accel(self) -> tuple[float, float, float]:
        data = self.bus.read_i2c_block_data(self.addr, 0x3B, 6)
        ax = self._twos_complement(data[0] << 8 | data[1], 16)
        ay = self._twos_complement(data[2] << 8 | data[3], 16)
        az = self._twos_complement(data[4] << 8 | data[5], 16)
        return ax / 16384.0, ay / 16384.0, az / 16384.0

class TiltCompensatedCompass:
    def __init__(self,
                 bus_num=1,
                 compass_addr=0x1E,
                 declination_deg=0.0,
                 x_offset=0.0,
                 y_offset=0.0,
                 x_scale=1.0,
                 y_scale=1.0
                 ):
        self.compass_bus = smbus.SMBus(bus_num)
        self.compass_addr = compass_addr
        self.declination_rad = math.radians(declination_deg)
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.x_scale = x_scale
        self.y_scale = y_scale
        self.accel = MPU6050(bus_num=bus_num)

        self.compass_bus.write_byte_data(self.compass_addr, 0x00, 0x70)
        self.compass_bus.write_byte_data(self.compass_addr, 0x01, 0x20)
        self.compass_bus.write_byte_data(self.compass_addr, 0x02, 0x00)
        time.sleep(0.1)

    @staticmethod
    def _twos_complement(val, bits) -> float:
        if val & (1 << (bits - 1)):
            val -= (1 << bits)
        return val

    def _read_mag_axis(self) -> tuple[float, float, float]:
        data = self.compass_bus.read_i2c_block_data(self.compass_addr, 0x03, 6)
        x = self._twos_complement(data[0] << 8 | data[1], 16)
        z = self._twos_complement(data[2] << 8 | data[3], 16)
        y = self._twos_complement(data[4] << 8 | data[5], 16)
        return x, y, z

    def get_heading(self) -> float:
        raw_mx, raw_my, raw_mz = self._read_mag_axis()
        ax, ay, az = self.accel.read_accel()

        cal_mx = (raw_mx - self.x_offset) * self.x_scale
        cal_my = (raw_my - self.y_offset) * self.y_scale
        cal_mz = raw_mz 

        roll = math.atan2(ay, az)
        pitch = math.atan2(-ax, math.sqrt(ay * ay + az * az))

        x_comp = cal_mx * math.cos(pitch) + cal_mz * math.sin(pitch)
        y_comp = cal_mx * math.sin(roll) * math.sin(pitch) + \
                 cal_my * math.cos(roll) - \
                 cal_mz * math.sin(roll) * math.cos(pitch)
        heading = math.atan2(y_comp, x_comp)
        heading += self.declination_rad
        
        if heading < 0:
            heading += 2 * math.pi
        if heading > 2 * math.pi:
            heading -= 2 * math.pi
            
        return math.degrees(heading)

class Compass:
    def __init__(self, bus_num=1, addr=0x1E, declination_deg=0.0):
        self.compass = smbus.SMBus(bus_num)
        self.addr = addr
        self.declination_rad = math.radians(declination_deg)

        self.compass.write_byte_data(self.addr, 0x00, 0x70)
        self.compass.write_byte_data(self.addr, 0x01, 0x20)
        self.compass.write_byte_data(self.addr, 0x02, 0x00)
        time.sleep(0.1)

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
    compass = TiltCompensatedCompass(
        x_offset=-253.25,        
        y_offset=-101.25,         
        x_scale=1.0,          
        y_scale=1.0
    )
    while True:
        curr_location = gps.get_location()
        heading = compass.get_heading()
        sat_count = gps.get_satelite_count()
        visible_sat_count = gps.last_num_visible_sats
        print(f"heading: {heading}")
        if gps.get_location() != None:
            longitude = curr_location.longitude
            latitude = curr_location.latitude
            print(f"longitude: {longitude} | latitude: {latitude}")
        else:
            print("NO GPS")
        print(f"satelite count: {sat_count}")
        print(f"visible satelite count: {visible_sat_count}")
        time.sleep(0.1)
