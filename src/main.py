import sys
import logging
from glob import glob
from time import sleep
import threading

from serial import Serial, SerialException

from decode_rc import Decode
from auto import Auto
from navigation import Gps, Compass, Point, TiltCompensatedCompass
from lora import Lora
from mavlink import MavlinkHandler

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
                break
            except (OSError, SerialException) as err:
                logging.error(err)
                arduino = None

        # Send ready signal to arduino if good
        if arduino is not None:
            ready = "PI-READY\n"
            _send(arduino, ready)
            return arduino

        # Keep retrying if arduino is not found
        logging.warning("Arduino not found\n")
        print("Arduino not found\nRetrying in 5 seconds...")
        sleep(5)

def _setup_autonomy(waypoints) -> Auto:
    gps = Gps("/dev/ttyAMA3", 9600)
    compass = TiltCompensatedCompass(
        x_offset=-253.25,        
        y_offset=-101.25,         
        x_scale=1.0,          
        y_scale=1.0
    )
    auto = Auto(gps, compass, waypoints)
    return auto

def _telemetry_loop(auto: Auto, mav_bridge: MavlinkHandler) -> None:
    while True:
        curr_loc = auto.gps.get_location()
        curr_heading = auto.compass.get_heading()
        if curr_loc and curr_heading is not None:
            mav_bridge.send_telemetry(curr_loc.latitude, curr_loc.longitude, curr_heading)
            print(f"[TX] Sending Telemetry -> Lat: {curr_loc.latitude:.5f}, Lon: {curr_loc.longitude:.5f}, Hdg: {curr_heading:.1f}")

if __name__ == "__main__":
    rc_decoder = Decode("/dev/ttyAMA0", 420000)
    count_none = 0
    while rc_decoder.decode_rc() is None:
        logging.warning("Waiting to connect to remote")
        print("Waiting to connect to remote")
        sleep(1)
        count_none += 1
        if count_none >= NONE_TIMEOUT:
            logging.warning("Resetting receiver")
            print("Resetting receiver")
            rc_decoder.reset()

    arduino = _setup_arduino()
    logging.info("Arduino set up")
    print("Arduino set up")

    auto = _setup_autonomy([Point(40.89769,-73.12574)])
    logging.info("Autonomous functions set up")
    print("Autonomous functions set up")

    lora_module = Lora(ADDRESS=0, NETWORK=1, PORT="/dev/ttyAMA4", BAUD=115200)
    mav_bridge = MavlinkHandler(lora_module, target_address=1) 
    mavlink_thread = threading.Thread(target=_telemetry_loop, daemon=True).start()
    logging.info("Mavlink set up")
    print("Mavlink set up")

    last_value = (-1.0, 0.0, -1.0)
    last_auto_throttle = -1.0
    count_none = 0

    while True:
        if not lora_module.waypoints.empty():
            # Your get_waypoints() method already returns a Point(lat, lon) object
            new_wp = lora_module.get_waypoints() 
            
            # Append it to your autonomy's waypoint list
            # Note: If your Auto class uses a specific method to add waypoints (like auto.add_waypoint(new_wp)), use that here instead
            auto.waypoints.append(new_wp) 
            
            logging.info(f"*** MISSION PLANNER WAYPOINT ADDED: {new_wp.latitude}, {new_wp.longitude} ***")
            print(f"*** MISSION PLANNER WAYPOINT ADDED: {new_wp.latitude}, {new_wp.longitude} ***")

        decoded = rc_decoder.decode_rc()

        # On timeout, attempt to reconnect
        if count_none >= NONE_TIMEOUT:
            logging.warning("Disconnected from remote, halting motor")
            print("Disconnected from remote, halting motor")
            channels = DEFAULT_CHANNELS
            _send(arduino, channels)

            while rc_decoder.decode_rc() is None:
                logging.warning("Waiting to reconnect to remote")
                print("Waiting to reconnect to remote")
                sleep(1)
                rc_decoder.reset()
            logging.info("Reconnected to remote")
            print("Reconnected to remote")
            count_none = 0
            last_value = (-1.0, 0.0, -1.0)
            last_auto_throttle = -1.0
            continue
        elif decoded is None:
            count_none += 1
            continue
        else:
            count_none = 0

        # Wait for throttle to be reset for manual controls
        last_state, _, _ = last_value
        state, rotation, throttle = (float(decoded[0]), float(decoded[1]), float(decoded[2]))
        if last_state != state and state == 0.0 and throttle != -1.0:
            logging.warning("Set throttle to 0 before continuing")
            print("Set throttle to 0 before continuing")
            _send(arduino, DEFAULT_CHANNELS)
            while True:
                rc_decoder.flush()
                decoded = rc_decoder.decode_rc()
                if decoded is None:
                    continue

                current_state, _, current_throttle = (float(decoded[0]), float(decoded[1]), float(decoded[2]))
                logging.debug(f"{current_state} _ {current_throttle}")
                print(f"{current_state} _ {current_throttle}")
                if current_state != 0.0 or current_throttle == -1.0:
                    state, rotation, throttle = (float(decoded[0]), float(decoded[1]), float(decoded[2]))
                    break
                logging.debug("Waiting for reset")
                print("Waiting for reset")
                sleep(1)

        last_value = (state, rotation, throttle)
        print(f"state: {state}")
        if state == -1.0: # Top | Off
            if last_state == 1.0:
                auto.pause()
            _send(arduino, DEFAULT_CHANNELS)
        elif state == 0.0: # Middle | Manual Control
            if last_state == 1.0:
                auto.pause()
            channels = f"{rotation} {throttle}\n"
            last_auto_throttle = throttle
            logging.debug(f"{channels}")
            print(f"Channels: {channels}")
            _send(arduino, channels)
        elif state == 1.0: # Down | Autonomous Control
            if last_state != 1.0:
                auto.start()
                last_auto_throttle = -1.0
            rotation, throttle = auto.get_values(last_auto_throttle)
            last_auto_throttle = throttle
            channels = f"{rotation} {throttle}\n"
            print(f"target waypoint: {auto.get_curr_waypoint().latitude} | {auto.get_curr_waypoint().longitude}")
            print(f"curr location: {auto.gps.get_location().latitude} | {auto.gps.get_location().longitude}")
            print(f"curr heading: {auto.compass.get_heading()}")
            print(f"Error Angle: {auto.angle_to_waypoint(auto.get_curr_waypoint()):.2f} | PID Output: {float(rotation):.2f}")
            print(f"angle to wayp: {auto.angle_to_waypoint(auto.get_curr_waypoint())}")
            print(f"channels: {channels}")
            _send(arduino, channels)
