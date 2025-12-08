import math
from gps import Gps, Point, Compass

class Auto:
    def __init__(self, gps: Gps, compass: Compass):
        self.gps = gps
        self.compass = compass
        
    def distance(self, point1: Point, point2: Point) -> float: # Should be in degress
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

    def speed(self, dist, time): #Use dist func above, time is set
        return dist/time
    
    def a_to_w(self, point1: Point, point2: Point) -> float:
        dLon = (point2.longitude - point1.longitude) * math.pi / 180.0
        lat1 = (point1.latitude) * math.pi / 180.0
        lat2 = (point2.latitude) * math.pi / 180.0

        y = math.sin(dLon) * math.cos(lat2)
        x = (math.cos(lat1) * math.sin(lat2) - 
             math.sin(lat1) * math.cos(lat2) * math.cos(dLon))
        brng = math.atan2(y, x)
        brng = math.degrees(brng)
        brng = (brng + 360) % 360
        return brng - self.compass.get_heading()
    


