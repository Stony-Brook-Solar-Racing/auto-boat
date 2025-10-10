from serial import Serial

class ServoControl:
    def __init__(self, arduino: Serial):
        self.arduino = arduino

    def send_ch1and3(self):
        arduino = self.arduino
        value = input("Give a value between 0 and 180: ").strip()
        value = int(value)
        line = f"{value} 0 180\n".encode("ascii")
        try:
            arduino.reset_input_buffer()
        except Exception:
            pass
        arduino.write(line)
        arduino.flush()

    def send_ch1(self):
        arduino = self.arduino
        value = input("Give a value between 1000 and 2000")
        value = int(value)
        line = f"{value}\n".encode("ascii")
        try:
            arduino.reset_input_buffer()
        except Exception:
            pass
        arduino.write(line)
        arduino.flush()
