import serial
import queue
import time
import threading
import logging
from navigation import Point

# some rylr998 commands
# https://reyax.com/upload/products_download/download_file/LoRa_AT_Command_RYLR998_RYLR498_EN.pdf
# AT
# Test connection, +OK if working

# AT+RESET
# Soft reset, restarts, returns +RESET, then +READY

# AT+FACTORY
# Factory reset

# AT+ADDRESS=<id>
# Set device id, sets unique address of the particular module

# AT+NETWORKID=<id>
# Set Network ID, defined a group, only modules with the same network ID can talk to each other, default is 0

# AT+BAND=<Hz>
# Set Frequency, MUST BE 915000000 TO BE COMPLIANT

# AT+SEND=<Addr>,<Len>,<Data>
# Sent data, to a specific address

# AT+IPR=<Baud>
# Set Baud rate, default is 115200

# AT+MODE=<Mode>
# Power mode, 0: transceiver default, 1: sleep mode, wakes on serial

# AT+CRFOP=22
# Set power to max

# AT+PARAMETER=<SF>,<BW>,<CR>,<P>
# Set RF Parameters (Tuning changes speed vs. range)
# SF (Spreading Factor): 7-12 (Higher = More range, slower)
# BW (Bandwidth): 7-9 (7=125kHz, 8=250kHz, 9=500kHz)
# CR (Coding Rate): 1-4 (Higher = More reliability)

# AT+CPIN=<Password>
# Set the 8-digit hex password for AES128 encryption
# Example: AT+CPIN=11223344

# AT+UID?
# Inquire the unique 12-byte module ID

# AT+VER?
# Inquire the firmware version

# AT+IPR?
# Inquire the current baud rate setting

# can add ? to almost any command to get the current value

# INCOMING DATA WILL BE IN THIS FORMAT
# +RCV=<Address>,<Length>,<Data>,<RSSI>,<SNR>

# reserved characters used for delimmters: ',', '~', '/'

# todo:
# send logging data
# sent data from prints as logging stuff also?

class Lora:
    # default baud is 115200 idk how seriel works but if 9600 is NECCESSARY, you'll need to change serial to 115200 then send AT+IPR=9600
    def __init__(self, ADDRESS, NETWORK=1, PORT="/dev/ttyAMA4", BAUD=115200):
        self.lora = serial.Serial(PORT, BAUD, timeout=1)
        self.lock = threading.Lock()
        self.address = ADDRESS
        self.network = NETWORK

        self.running = True
        self.waypoints = queue.SimpleQueue()
        self.messages = queue.SimpleQueue()

        time.sleep(0.5) 
        self._init_module()

        self.thread = threading.Thread(target=self.parse_message, daemon=True)
        self.thread.start()

    def _init_module(self):
        commands = ["AT", "AT+BAND=915000000", "AT+CRFOP=22", f"AT+ADDRESS={self.address}", f"AT+NETWORKID={self.network}"]
        for cmd in commands:
            if not self.send_command(cmd):
                raise Exception(f"Failed to initialize: {cmd}")

    # supposedly threadsafe way to send a command
    def send_command(self, cmd):
        with self.lock:
            self.lora.reset_input_buffer() 
            self.lora.write(f"{cmd}\r\n".encode('utf-8'))
            start = time.time()
            while time.time() - start < 2:
                line = self.lora.readline().decode('utf-8').strip()
                if not line: continue
                if "+OK" in line:
                    return True
                if "+ERR" in line:
                    print(f"Command Error [{cmd}]: {line}")
                    return False
        return False

    def parse_message(self):
        while self.running:
            with self.lock:
                if self.lora.in_waiting > 0:
                    try:
                        res = self.lora.readline().decode('utf-8').strip()
                        if res.startswith("+RCV="):
                            self._handle_rcv(res)
                    except Exception as e:
                        print(f"Read Error: {e}")
            
            # grabs lock if need be
            time.sleep(0.01) 

    def _handle_rcv(self, raw_line):
        parts = raw_line.replace("+RCV=", "").split(',')
        if len(parts) != 5: return

        # <DATATYPE>~data
        # example: waypoint:-100.2302/100.230498
        data_str = parts[2]
        if '~' in data_str:
            data_type, content = data_str.split('~', 1)
            if data_type.lower() == "waypoint":
                if '/' in content:
                    self.waypoints.put(content.split('/'))
            else:
                self.messages.put({data_type: content})
        else:
            self.messages.put(data_str)

    def send_msg(self, addr, msg_type, content):
        payload = f"{msg_type}~{content}"
        # AT+SEND=<Addr>,<Len>,<Data>
        return self.send_command(f"AT+SEND={addr},{len(payload)},{payload}")

    def stop(self):
        self.running = False
        self.lora.close()

    def get_waypoints(self):
        tmp = self.waypoints.get()
        return Point(tmp[0], tmp[1])

    def get_message(self):
        return self.messages.get()
    
class LoraLogging(logging.Handler):
    def __init__(self, lora_instance, target_addr):
        super().__init__()
        self.lora = lora_instance
        self.target_addr = target_addr

    def emit(self, record):
        try:
            msg = self.format(record)
            msg_type = record.levelname.lower()
            self.lora.send_msg(self.target_addr, msg_type, msg)
        except Exception:
            self.handleError(record)