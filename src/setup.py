from glob import glob
from serial import Serial, SerialException
import sys
from time import sleep
import logging

from servo_control import ServoControl

# Constants
BAUDRATE = 9600
TIMEOUT = 1
"""
logging.basicConfig(
    filename="/var/log/pwm/pwm.log",
    filemode='w+',
    level=logging.DEBUG
)
"""
class Setup:

    def __setup_arduino(self):
        self.arduino = None
        if sys.platform == "linux":
            ports = glob("/dev/ttyACM*")
        elif sys.platform.startswith('win'):
            ports = [f"COM{i}" for i in range(10)]
        else:
           raise Exception("Platform not supported")

        for port in ports:
            try:
                self.arduino = Serial(port=port, baudrate=BAUDRATE, timeout=TIMEOUT)
                sleep(1)
            except(OSError, SerialException) as err:
                logging.error(err)
        
        while self.arduino == None:
            print("Arduino not found\n")
            print("Retrying in 5 seconds...")
            sleep(5)
            self.__setup_arduino()

    def __init__(self):
        self.__setup_arduino()
        print("Got here")
        
if __name__ == "__main__":
    sleep(2)
    setup = Setup()
    controller = ServoControl(setup.arduino)
    while(True):
        controller.send_ch3()
        
        
