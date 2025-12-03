import math
EARTH_RADIUS = 6371 # WE ARE USING KILOMETERS

class Auto:

    def __init__ (self, gps, PORT_COMPASS):
        self.gps = gps
        self.PORT_COMPASS = PORT_COMPASS
        
    def distance (point1, point2) -> float: # Should be in degress
        radians = math.pi / 180.0

        D_lon = (point2.longtitude - point1.longtitude) * radians
        D_lat = (point2.latitude - point1.latitude) * radians
        
        lat1 = point1.latitude * radians
        lat2 = point2.latitude * radians

        a = math.sin(D_lat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(D_lon/2) ** 2
        return 2 * EARTH_RADIUS * math.asin(math.sqrt(a))

class Point:
    def __init__ (self, longtitude, latitude):
        self.longtitude = longtitude
        self.latitude = latitude

print("lon -180 to 180 and lat -90 to 90\n ")
point1 = Point(float(input("lon1: ")), float(input("lat1: ")))
point2 = Point(float(input("lon2: ")), float(input("lat2: ")))
print(Auto.distance(point1, point2))
        
    
    




