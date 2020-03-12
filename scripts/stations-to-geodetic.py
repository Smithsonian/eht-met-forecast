import json

from astropy import units as u
from astropy.coordinates import EarthLocation

stations = [
    {'name': 'PDBURE', 'vex': 'Nq', 'x': 4524000.43000, 'y': 468042.14000, 'z': 4460309.76000},
    {'name': 'PICOVEL', 'vex': 'Pv', 'x': 5088967.74544, 'y': -301681.18586, 'z': 3825012.20561},
    {'name': 'THULE', 'vex': 'Gl', 'x': 541547.00000, 'y': -1387978.60000, 'z': 6180982.00000},
    {'name': 'SPT', 'vex': 'Sz', 'x': 0.01000, 'y': 0.01000, 'z': -6359609.70000},
    {'name': 'APEX', 'vex': 'Ax', 'x': 2225039.52970, 'y': -5441197.62920, 'z': -2479303.35970},
    {'name': 'ALMA', 'vex': 'Aa', 'x': 2225061.16360, 'y': -5440057.36994, 'z': -2481681.15054},
    {'name': 'LMT', 'vex': 'Lm', 'x': -768715.63200, 'y': -5988507.07200, 'z': 2063354.85200},
    {'name': 'KITTPEAK', 'vex': 'Kp', 'x': -1995953.25070, 'y': -5037384.58590, 'z': 3357045.51860},
    {'name': 'SMTO', 'vex': 'Mg', 'x': -1828796.20000, 'y': -5054406.80000, 'z': 3427865.20000},
    {'name': 'SMAP', 'vex': 'Sw', 'x': -5464555.49300, 'y': -2492927.98900, 'z': 2150797.17600},
    {'name': 'JCMT', 'vex': 'Mm', 'x': -5464584.67600, 'y': -2493001.17000, 'z': 2150653.98200},
]

geodetic_stations = []

for s in stations:
    loc = EarthLocation.from_geocentric(s['x']*u.m, s['y']*u.m, s['z']*u.m)
    locg = loc.geodetic
    geod = {
        'name': s['name'],
        'vex': s['vex'],
        'lat': round(locg.lat.value, 3),
        'lon': round(locg.lon.value, 3),
        'alt': round(locg.height.value),
    }
    geodetic_stations.append(geod)

print(json.dumps(geodetic_stations, sort_keys=True, indent=4))
      
