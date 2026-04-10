from pymavlink.dialects.v20 import common as mavlink
import time
import threading
import math

class MavBuffer:
    def __init__(self):
        self.b = bytearray()
    def write(self, data):
        self.b.extend(data)
    def read_hex(self):
        res = bytes(self.b).hex()
        self.b.clear()
        return res

class MavlinkHandler:
    def __init__(self, lora_instance, target_address=1):
        self.lora = lora_instance
        self.target_address = target_address
        self.mav_buf = MavBuffer()
        # Initialize pymavlink to write binary to our buffer
        self.mav = mavlink.MAVLink(self.mav_buf, srcSystem=1, srcComponent=1)
        
        # Start a background thread to process incoming waypoints
        self.running = True
        self.thread = threading.Thread(target=self._process_incoming, daemon=True)
        self.thread.start()

    def send_heartbeat(self):
        """
        Generates and sends a dedicated MAVLink heartbeat packet via LoRa.
        """
        try:
            # 1. Create and encode the Heartbeat message
            # We use MAV_TYPE_SURFACE_BOAT since you are building a boat
            hb_msg = self.mav.heartbeat_encode(
                mavlink.MAV_TYPE_SURFACE_BOAT, 
                mavlink.MAV_AUTOPILOT_GENERIC, 
                0, 0, 0
            )
            
            hb_bytes = hb_msg.pack(self.mav)
            hb_hex = hb_bytes.hex()
            
            payload = f"mav~{hb_hex}"
            self.lora.send_mavlink(self.target_address, payload)
        except Exception as e:
            print(f"[Error] Failed to send heartbeat: {e}")

    def send_telemetry(self, lat, lon, heading):
        time_boot_ms = int(time.monotonic() * 1000) & 0xFFFFFFFF
        
        self.mav.heartbeat_send(
            mavlink.MAV_TYPE_SURFACE_BOAT, 
            mavlink.MAV_AUTOPILOT_GENERIC, 
            0, 0, 0
        )

        self.mav.global_position_int_send(
            time_boot_ms, 
            int(lat * 1e7), 
            int(lon * 1e7), 
            0, 0, 0, 0, 0, 
            int(heading * 100)
        )

        self.mav.vfr_hud_send(
                0.0, 
                0.0, 
                int(heading), 
                0, 
                0.0, 
                0.0
            )

        self.mav.attitude_send(
            time_boot_ms, 
            0,
            0,
            math.radians(heading), # yaw (must be radians)
            0,
            0,
            0
        )

        combined_hex = self.mav_buf.read_hex()
        if len(combined_hex) > 0:
            self.lora.send_mavlink(self.target_address, combined_hex)

    def _process_incoming(self):
        while self.running:
            # Check if we got MAVLink hex strings from the laptop
            if not self.lora.mavlink_messages.empty():
                hex_msg = self.lora.mavlink_messages.get()
                try:
                    raw_bytes = bytes.fromhex(hex_msg)
                    # Feed bytes into pymavlink parser
                    for b in raw_bytes:
                        parsed_msg = self.mav.parse_char(bytes([b]))
                        if parsed_msg:
                            self._handle_msg(parsed_msg)
                except Exception as e:
                    print(f"MAVLink Parse Error: {e}")
            time.sleep(0.1)

    def _handle_msg(self, msg):
        # Mission Planner sends MISSION_ITEM_INT for waypoints
        if msg.get_type() == 'MISSION_ITEM_INT':
            lat = msg.x / 1e7
            lon = msg.y / 1e7
            # Optional: msg.seq gives you the waypoint sequence number
            print(f"WAYPOINT RECEIVED via MAVLink: Lat {lat}, Lon {lon}")
            
            # Put it in your existing waypoint queue as a Point
            # Assuming you imported Point from navigation
            self.lora.waypoints.put([str(lat), str(lon)]) 

    def stop(self):
        self.running = False
