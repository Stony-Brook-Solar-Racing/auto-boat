import math
from navigation import Point, Gps, Compass
from simple_pid import PID

def distance(point1: Point, point2: Point) -> float: # Returns in km
    D_lat = (point2.latitude - point1.latitude) * math.pi / 180.0
    D_lon = (point2.longitude - point1.longitude) * math.pi / 180.0
    
    lat1 = (point1.latitude) * math.pi / 180.0
    lat2 = (point2.longitude) * math.pi / 180.0

    a = (pow(math.sin(D_lat / 2), 2) + 
         pow(math.sin(D_lon / 2), 2) * 
             math.cos(lat1) * math.cos(lat2));
    print(point1.latitude, point2.latitude, lat1, lat2, a)
    rad = 6371
    c = 2 * math.asin(math.sqrt(a))
    return rad * c


def speed(point1, point2, time):
    dist = distance(point1, point2)
    return dist/time

class Auto:
    def __init__(self, gps: Gps, compass: Compass, max_rudder = 0.3, min_rudder = -0.3):
        self.gps = gps
        self.compass = compass
        self.rudder_pid = PID(1, 0.0, 0.0, setpoint=1)
        self.rudder_pid.output_limits = (min_rudder, max_rudder)
    
    # Returns angle to waypoint
    def angle_to_waypoint(self, waypoint: Point) -> float:
        curr_pos = self.gps.get_location()
        dLon = (waypoint.longitude - curr_pos.longitude) * math.pi / 180.0
        lat1 = (curr_pos.latitude) * math.pi / 180.0
        lat2 = (waypoint.latitude) * math.pi / 180.0

        y = math.sin(dLon) * math.cos(lat2)
        x = (math.cos(lat1) * math.sin(lat2) - 
             math.sin(lat1) * math.cos(lat2) * math.cos(dLon))
        brng = math.atan2(y, x)
        brng = math.degrees(brng)
        brng = (brng + 360) % 360
        # Maps it to [-180, 180)
        angle = (brng - self.compass.get_heading() + 180) % 360 - 180
        return angle

    # Returns the values for throttle and rudder
    def get_values(self, waypoint: Point, last_throttle: float) -> tuple[float, float]:
        # Get throttle value
        last_throttle = last_throttle
        dist = distance(waypoint, self.gps.get_location())
        throttle, rudder = (-1.0, 0.0)
        if dist > 30:
            desired_throttle = 1
        else:
            desired_throttle = dist/30

        # Gradual increase/decrease
        if last_throttle < desired_throttle:
            throttle = last_throttle+0.01
        elif last_throttle == desired_throttle:
            throttle = last_throttle
        else:
            throttle = last_throttle-0.01

        # Get rudder value
        angle_to_w = self.angle_to_waypoint(waypoint)
        rudder = self.rudder_pid(angle_to_w)
        
        return (throttle, rudder)

    # Needed to keep PID alive
    def start(self):
        self.rudder_pid.auto_mode = True
    def pause(self):
        self.rudder_pid.auto_mode = False
