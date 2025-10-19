import sys
from glob import glob
from time import sleep

from serial import Serial, SerialException

from decode_rc import Decode

# Constants
BAUDRATE = 9600
TIMEOUT = 1


def _send(arduino, text):
    line = text.encode("ascii")
    try:
        arduino.reset_input_buffer()
    except Exception:
        pass
    arduino.write(line)
    arduino.flush()


def _setup_arduino():
    arduino = None
    # Check platform type
    if sys.platform == "linux":
        ports = glob("/dev/ttyACM*")
    elif sys.platform.startswith("win"):
        ports = [f"COM{i}" for i in range(10)]
    else:
        raise Exception("Platform not supported")

    # Find arduino
    while arduino == None:
        for port in ports:
            try:
                arduino = Serial(port=port, baudrate=BAUDRATE, timeout=TIMEOUT)
                sleep(1)
            except (OSError, SerialException) as err:
                # logging.error(err)
                print(err)

        # Send ready signal to arduino if good
        if arduino != None:
            ready = "PI-READY\n"
            _send(arduino, ready)
            return arduino

        # Keep retrying if arduino is not found
        print("Arduino not found\n")
        print("Retrying in 5 seconds...")
        sleep(5)


if __name__ == "__main__":
    arduino = _setup_arduino()
    rc_decoder = Decode("/dev/ttyAMA0", 420000)

    while True:
        (sa, ch1, ch3) = rc_decoder.decode_rc()
        if sa == "1":
            channels = ch1 + " " + ch3 + "\n"
            print(channels)
            _send(arduino, channels)
        elif sa == "0":
            channels = "0 0\n"
            print(channels)
            _send(arduino, channels)
        elif sa == "-1":
            # Implement autonomy later
            pass
