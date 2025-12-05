import math

class Auto:
    def __init__ (self, gps, PORT_COMPASS):
        self.gps = gps
        self.PORT_COMPASS = PORT_COMPASS
        
    def distance (point1, point2): # Should be in degress
        D_lat = (point2.latitude - point1.latitude) * math.pi / 180.0
        D_lon = (point2.longtitude - point1.longitude) * math.pi / 180.0
        
        lat1 = (point1.latitude) * math.pi / 180.0
        lat2 = (point2.longitude) * math.pi / 180.0

        a = (pow(math.sin(D_lat / 2), 2) + 
             pow(math.sin(D_lon / 2), 2) * 
                 math.cos(lat1) * math.cos(lat2));
        print(point1.latitude, point2.latitude, lat1, lat2, a)
        rad = 6371
        c = 2 * math.asin(math.sqrt(a))
        return rad * c

    def speed (dist, time): #Use dist func above, time is set
        return dist/time
