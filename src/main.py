import sys
import logging
from glob import glob
from time import sleep

from serial import Serial, SerialException

from decode_rc import Decode
from auto import Auto

# Constants
BAUDRATE = 9600
TIMEOUT = 1
DEFAULT_CHANNELS = "0 -1\n"
NONE_TIMEOUT = 20

logging.basicConfig(
    format='%(relativeCreated)dms:%(levelname)s - %(message)s',
    filename="pi.log", filemode="w+", level=logging.NOTSET
)


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
                logging.error(err)

        # Send ready signal to arduino if good
        if arduino is not None:
            ready = "PI-READY\n"
            _send(arduino, ready)
            return arduino

        # Keep retrying if arduino is not found
        logging.warning("Arduino not found\n"
                        "Retrying in 5 seconds...")
        sleep(5)

# def _setup_autonomy() -> Auto:

if __name__ == "__main__":
    rc_decoder = Decode("/dev/ttyAMA0", 420000)
    count_none = 0
    while rc_decoder.decode_rc() is None:
        logging.warning("Waiting to connect to remote")
        sleep(1)
        if count_none >= NONE_TIMEOUT:
            logging.warning("Resetting receiver")
            rc_decoder.reset()

    arduino = _setup_arduino()
    logging.info("Arduino set up")

    last_value = (-1, 0, -1)
    count_none = 0
    while True:
        decoded = rc_decoder.decode_rc()

        # On timeout, attempt to reconnect
        if count_none >= NONE_TIMEOUT:
            logging.warning("Disconnected from remote, halting motor")
            channels = DEFAULT_CHANNELS
            _send(arduino, channels)

            while rc_decoder.decode_rc() is None:
                logging.warning("Waiting to reconnect to remote")
                sleep(1)
                rc_decoder.reset()
            logging.info("Reconnected to remote")
            count_none = 0
            last_value = (-1, 0, -1)
            continue
        elif decoded is None:
            count_none += 1
            continue
        else:
            count_none = 0

        # Wait for throttle to be reset for manual controls
        last_state, _, _ = last_value
        state, rotation, throttle = decoded
        if last_state != state and state == "0" and throttle != "-1.0":
            logging.warning("Set throttle to 0 before continuing")
            _send(arduino, DEFAULT_CHANNELS)
            while True:
                rc_decoder.flush()
                decoded = rc_decoder.decode_rc()
                if decoded is None:
                    continue

                current_state, _, current_throttle = decoded
                logging.debug(f"{current_state} _ {current_throttle}")
                if current_state != "0" or current_throttle == "-1.0":
                    state, rotation, throttle = decoded
                    break
                logging.debug("Waiting for reset")
                sleep(1)

        last_value = decoded
        if state == "-1": # Top | Off
            _send(arduino, DEFAULT_CHANNELS)
        elif state == "0": # Middle | Manual Control
            channels = f"{rotation} {throttle}\n"
            logging.debug(f"{channels}")
            _send(arduino, channels)
        elif state == "1": # Down | Autonomous Control
            _send(arduino, DEFAULT_CHANNELS)
