from serial import Serial

class ServoControl:
    def __init__(self, arduino: Serial):
        self.arduino = arduino

    def send_ch3(self):
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
