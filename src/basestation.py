import serial
import socket
import threading
import time
import os

# --- CONFIGURATION ---
LORA_PORT = 'COM9' # Match your ESP32's COM port
LORA_BAUD = 115200
BOAT_ADDRESS = 0 # The LoRa address of the boat

# Mission Planner UDP settings (Running in background)
MP_IP = '127.0.0.1'
MP_PORT = 14550 
BRIDGE_PORT = 14551 

print(f"Connecting to LoRa on {LORA_PORT}...")
try:
    lora = serial.Serial(LORA_PORT, LORA_BAUD, timeout=0.1)
except Exception as e:
    print(f"Failed to open serial port: {e}")
    exit(1)

def init_basestation():
    print("Configuring Base Station LoRa Module...")
    # Set Band to 915MHz, Network to 1, Address to 1, and Power to Max
    commands = [
        "AT+BAND=915000000",
        "AT+NETWORKID=1",
        "AT+ADDRESS=1",
        "AT+CRFOP=22"
    ]
    for cmd in commands:
        lora.write(f"{cmd}\r\n".encode('utf-8'))
        time.sleep(0.2) # Give the module time to process and reply
        while lora.in_waiting > 0:
            resp = lora.readline().decode(errors='ignore').strip()
            print(f"  {cmd} -> {resp}")
    print("Base Station Ready!\n")

init_basestation()

# Setup UDP Socket for when Mission Planner is ready
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp.bind(('127.0.0.1', BRIDGE_PORT))

def send_to_lora(payload):
    # Ensure it's formatted as an AT command
    cmd = f"AT+SEND={BOAT_ADDRESS},{len(payload)},{payload}\r\n"
    lora.write(cmd.encode('utf-8'))

def lora_to_mission_planner():
    """
    Reads from Serial LoRa, prints to console, and sends binary to Mission Planner UDP
    """
    while True:
        try:
            if lora.in_waiting > 0:
                line = lora.readline().decode('utf-8', errors='ignore').strip()
                
                # Check if it's a valid received packet containing MAVLink hex
                if line.startswith("+RCV="):
                    parts = line.split(',')
                    if len(parts) >= 3:
                        data_str = parts[2]
                        
                        if data_str.startswith("mav~"):
                            hex_data = data_str.replace("mav~", "")
                            # --- CLI PRINTOUT ---
                            print(f"\n[RX TELEMETRY] MAVLink packet received! Length: {len(hex_data)} chars | Preview: {hex_data[:15]}...")
                            print(">> ", end="", flush=True) # Reprint CLI prompt

                            try:
                                binary_data = bytes.fromhex(hex_data)
                                udp.sendto(binary_data, (MP_IP, MP_PORT))
                            except ValueError:
                                print(f"\n[Error] Invalid hex received: {hex_data}")
                        else:
                            # Catch any non-MAVLink messages (like standard text logs)
                            print(f"\n[RX MESSAGE] {data_str}")
                            print(">> ", end="", flush=True)
                            
        except Exception as e:
            print(f"\nSerial Read Error: {e}")
            time.sleep(1)

def mission_planner_to_lora():
    """
    Reads binary from Mission Planner UDP, hex encodes, sends via Serial LoRa AT
    """
    while True:
        try:
            data, addr = udp.recvfrom(1024)
            hex_payload = data.hex()
            msg = f"mav~{hex_payload}"
            send_to_lora(msg)
        except Exception:
            time.sleep(1)

def command_line_interface():
    """
    Allows you to type raw payloads to send to the boat without Mission Planner
    """
    time.sleep(1) # Let the initial prints finish
    print("\n" + "="*50)
    print("CLI ACTIVE. Type a payload to send to the boat.")
    print("Examples:")
    print("  waypoint~40.897/-73.125    (Sends a manual waypoint)")
    print("  mav~001122334455           (Sends fake MAVLink hex)")
    print("  Type 'quit' to exit.")
    print("="*50)
    
    while True:
        try:
            user_input = input(">> ")
            if user_input.lower() == 'quit':
                print("Shutting down...")
                os._exit(0)
            
            if user_input.strip():
                send_to_lora(user_input.strip())
                print(f"[TX] Sent: {user_input.strip()}")
        except KeyboardInterrupt:
            os._exit(0)

# Start all threads
threading.Thread(target=lora_to_mission_planner, daemon=True).start()
threading.Thread(target=mission_planner_to_lora, daemon=True).start()

# Run the CLI in the main thread
command_line_interface()