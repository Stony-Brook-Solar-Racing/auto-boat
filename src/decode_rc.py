import time
import serial
import struct

TYPE_RC_CHANNELS_PACKED = 0x16

def crsf_crc(data: bytes) -> int:
    crc = 0
    for b in data:
        crc ^= b
        for _ in range(8):
            if (crc & 0x80) != 0:
                crc = ((crc << 1) ^ 0xD5) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc

def ticks_to_us(ticks: int) -> float:
    return ((ticks - 992) * 5.0 / 8.0) + 1500.0

def us_to_norm(us: float) -> float:
    # Map ~1000–2000 us to -1..+1
    return max(-1.0, min(1.0, ((us - 1500.0) / 500.0)))

def unpack_16x11_bits(payload22: bytes):
    # Little-endian bitstream of 16 * 11-bit integers
    bitbuf = int.from_bytes(payload22, byteorder="little", signed=False)
    vals = []
    for i in range(16):
        start = i * 11
        mask = (1 << 11) - 1
        vals.append((bitbuf >> start) & mask)
    return vals

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def throttle_to_servo_value(throttle_0_to_1: float) -> float:
    t = clamp(throttle_0_to_1, 0.0, 1.0)
    return (t * 2.0) - 1.0

def safe_throttle(x: float) -> float:
    if x < -0.80:
        return -1
    else:
        return x

class Decode:

    def __init__(self, PORT, BAUD):
        self.serial = serial.Serial(PORT, BAUD, timeout=0.1)
        self.last = (0, 0, 0)


    def decode_rc(self):
        serial.Serial(PORT, BAUD, timeout=0.1)
        buf.extend(ser.read(512))
        # Parse frames in the buffer
        i = 0
        while i + 5 <= len(buf):
            addr = buf[i]
            length = buf[i+1]  # length includes TYPE + PAYLOAD + CRC
            frame_end = i + 2 + length
            if frame_end > len(buf):
                break  # need more data

            ftype = buf[i+2]
            payload = bytes(buf[i+3:frame_end-1])
            crc = buf[frame_end-1]
            calc = crsf_crc(bytes([ftype]) + payload)

            if crc == calc:
                if ftype == TYPE_RC_CHANNELS_PACKED and len(payload) == 22:
                    ticks = unpack_16x11_bits(payload)
                    us = [ticks_to_us(t) for t in ticks]
                    norm = [us_to_norm(u) for u in us]
                    # print("column 3:", round(norm[2]+1,3))
                    # print("column 1:", round(norm[0],3))
                    self.last = (round(norm[6]), round(norm[0]), round(norm[2]))
                    return self.last
                # Advance to next frame
                i = frame_end
            else:
                # Bad CRC: skip a byte to re-sync
                i += 1

        # drop consumed bytes
        if i:
            del buf[:i]

        return self.last
