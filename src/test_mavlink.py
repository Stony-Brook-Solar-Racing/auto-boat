import time
from lora import Lora
from mavlink import MavlinkHandler

def main():
    # 1. Initialize LoRa
    # Make sure PORT matches your Pi's configuration (e.g., "/dev/ttyAMA4" or "/dev/serial0")
    print("Initializing LoRa Module...")
    # NOTE: Ensure this ADDRESS matches what basestation is sending to, 
    # and NETWORK matches basestation network
    lora_module = Lora(ADDRESS=0, NETWORK=1, PORT="/dev/ttyAMA4", BAUD=115200)

    # 2. Initialize MAVLink Handler
    # target_address=1 assumes the laptop/basestation LoRa module is set to address 1
    print("Initializing MAVLink Handler...")
    mav_bridge = MavlinkHandler(lora_module, target_address=1)

    print("Starting MAVLink telemetry stream. Press Ctrl+C to stop.")
    print("Listening for incoming commands...\n")
    
    # Dummy starting data (Stony Brook, NY)
    lat = 40.89769
    lon = -73.12574
    heading = 0.0

    try:
        while True:
            # --- 1. SEND FAKE TELEMETRY ---
            print(f"[TX] Sending Telemetry -> Lat: {lat:.5f}, Lon: {lon:.5f}, Hdg: {heading:.1f}")
            mav_bridge.send_telemetry(lat, lon, heading)
            
            # Simulate movement for the next packet
            lat += 0.0001
            lon += 0.0001
            heading = (heading + 15.0) % 360  
            
            # --- 2. CHECK FOR INCOMING PACKETS ---
            
            # Check for generic messages (text, logs, etc)
            while not lora_module.messages.empty():
                msg = lora_module.get_message()
                print(f"\n<<< [RX MESSAGE] Received: {msg} >>>\n")

            # Check for waypoints (sent like: waypoint~40.999/-73.222)
            while not lora_module.waypoints.empty():
                wp = lora_module.get_waypoints()
                print(f"\n<<< [RX WAYPOINT] New Target: Lat {wp.latitude}, Lon {wp.longitude} >>>\n")
            
            # (Note: incoming "mav~" messages are handled automatically 
            # by the MavlinkHandler background thread and will print 
            # "WAYPOINT RECEIVED via MAVLink..." if it successfully parses one)

            time.sleep(1)  # Send at 1Hz

    except KeyboardInterrupt:
        print("\nTest stopped by user.")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        # Clean up threads and serial ports
        mav_bridge.stop()
        lora_module.stop()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()