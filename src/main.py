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
    while arduino is None:
        for port in ports:
            try:
                arduino = Serial(port=port, baudrate=BAUDRATE, timeout=TIMEOUT)
                sleep(1)
            except (OSError, SerialException) as err:
                # logging.error(err)
                print(err)

        # Send ready signal to arduino if good
        if arduino is not None:
            ready = "PI-READY\n"
            _send(arduino, ready)
            return arduino

        # Keep retrying if arduino is not found
        print("Arduino not found\n")
        print("Retrying in 5 seconds...")
        sleep(5)


if __name__ == "__main__":
    rc_decoder = Decode("/dev/ttyAMA0", 420000)
    while rc_decoder.decode_rc() is None:
        print("Waiting to connect to remote")
        sleep(1)
    arduino = _setup_arduino()
    print("Arduino set up")

    last_value = (-1, 0, -1)
    count_none = 0

    while True:
        # state, rotation, throttle
        decoded = rc_decoder.decode_rc()
        if count_none >= 20:
            print("Disconnected from remote")
            while rc_decoder.decode_rc() is None:
                print("Waiting to reconnect to remote")
                sleep(1)
            count_none = 0
        elif decoded is None:
            count_none += 1
            continue
        else:
            count_none = 0
            last_value = decoded

        state, rotation, throttle = decoded

        if state == "-1":  # Up-most
            channels = rotation + " " + throttle + "\n"
            print(channels)
            _send(arduino, channels)
        elif state == "0":  # Middle
            channels = "0 -1\n"
            print(channels)
            _send(arduino, channels)
        elif state == "1":  # Down-most
            # Implement autonomy later
            pass
