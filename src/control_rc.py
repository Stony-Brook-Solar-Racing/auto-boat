# pip install pyserial
import time
import serial
import struct
from gpiozero import Servo

esc = Servo(
        12,
        min_pulse_width=988/1_000_000.0,
        max_pulse_width=2000/1_000_000.0,
        frame_width=20_000/1_000_000.0
        )

# servo2 = Servo(13, min_pulse_width=1/1000, max_pulse_width=2/1000, frame_width=20/1000)

PORT = "/dev/ttyAMA0"
BAUD = 420000

TYPE_RC_CHANNELS_PACKED = 0x16

# CRC-8 (poly 0xD5), init 0x00, over TYPE+PAYLOAD
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

def calibrate_motor():
    print("Calibrating Motor...")
    esc.value = throttle_to_servo_value(0.0)
    time.sleep(5)
    print("Done!")


def main():
    try:
        calibrate_motor()
        
        with serial.Serial(PORT, BAUD, timeout=0.1) as ser:
            buf = bytearray()
            while True:
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
                            # Example use: print first 8 channels
                            #print("CH1-8 us:", [round(u,1) for u in us[:8]],
                            #      "norm:", [round(n,3) for n in norm[:8]])
                            # print("norm:", [round(n,3) for n in norm[:8]])
                            print("column 3:", round(norm[2]+1,3))
                            print("column 1:", round(norm[0],3))
                            esc.value = norm[2]+1
                            # servo2.value = -1*norm[3]
                        # Advance to next frame
                        i = frame_end
                    else:
                        # Bad CRC: skip a byte to re-sync
                        i += 1

                # drop consumed bytes
                if i:
                    del buf[:i]
        esc.detach()
    finally:
        esc.close()
        print("Disconnected from esc")
if __name__ == "__main__":
    print("Testing")
    main()
