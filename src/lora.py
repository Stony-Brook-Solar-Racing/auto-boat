import serial

class Lora:
    def __init__(self, PORT="/dev/ttyAMA4", BAUD=9600):
        self.lora = serial.Serial(PORT, BAUD, timeout=1)
        self.waypoints = []
        self.messages = []

    def get_waypoints(self):
        return self.waypoints.pop()

    def get_message(self):
        return self.messages = []

