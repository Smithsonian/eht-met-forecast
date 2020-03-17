import math


def box(lat, lon, latlon_delta):
    leftlon = math.floor(lon / latlon_delta) * latlon_delta
    rightlon = leftlon + latlon_delta
    bottomlat = math.floor(lat / latlon_delta) * latlon_delta
    toplat = bottomlat + latlon_delta
    return leftlon, rightlon, bottomlat, toplat
