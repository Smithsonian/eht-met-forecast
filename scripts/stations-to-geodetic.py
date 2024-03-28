import json

from astropy import units as u
from astropy.coordinates import EarthLocation

stations = [
    # https://github.com/Smithsonian/site-selection/blob/main/allsites.txt
    # Nq:NOEMA Pv:PV Gl:GLT Sz:SPT Ax:APEX Aa:ALMA Lm:LMT Kp:KP Mg:SMT Sw:SMA Mm:JCMT
    # SMA=SMAP (phased)
    # SMAR=SMA reference antenna
    # PICO=PICOVEL=IRAM30M
    # NOEMA=PDBURE
    # PITUFFIK=GLT
    {'name': 'NOEMA/PDBURE', 'vex': 'Nn', 'x': 4524000.43000, 'y': 468042.14000, 'z': 4460309.76000},  # was Nq, now Nn
    {'name': 'PICOVEL/IRAM30M', 'vex': 'Pv', 'x': 5088967.74544, 'y': -301681.18586, 'z': 3825012.20561},
    {'name': 'PITUFFIK/GLT', 'vex': 'Gl', 'x': 541547.00000, 'y': -1387978.60000, 'z': 6180982.00000},
    {'name': 'SPT', 'vex': 'Sz', 'x': 0.01000, 'y': 0.01000, 'z': -6359609.70000},
    {'name': 'APEX', 'vex': 'Ax', 'x': 2225039.52970, 'y': -5441197.62920, 'z': -2479303.35970},
    {'name': 'ALMA', 'vex': 'Aa', 'x': 2225061.16360, 'y': -5440057.36994, 'z': -2481681.15054},
    {'name': 'LMT', 'vex': 'Lm', 'x': -768715.63200, 'y': -5988507.07200, 'z': 2063354.85200},
    {'name': 'KITTPEAK', 'vex': 'Kt', 'x': -1995953.25070, 'y': -5037384.58590, 'z': 3357045.51860},  # was Kp, now Kt
    {'name': 'SMTO', 'vex': 'Mg', 'x': -1828796.20000, 'y': -5054406.80000, 'z': 3427865.20000},
    {'name': 'SMAP', 'vex': 'Sw', 'x': -5464555.49300, 'y': -2492927.98900, 'z': 2150797.17600},
    {'name': 'JCMT', 'vex': 'Mm', 'x': -5464584.67600, 'y': -2493001.17000, 'z': 2150653.98200},

    # vex not yet assigned (2024 obs)
    {'name': 'KVN-Pyeongchang', 'x': -3149221.052, 'y': 3966404.922, 'z': 3864830.701},
    {'name': 'KVN-Yonsei', 'vex': 'Ky', 'x': -3042281.0183, 'y': 4045902.6730, 'z': 3867374.3296},

    # ngEHT values
    # KVNPC,KC,Korea,37.534119,128.449676,504,Korean VLBI Network Pyeongchang,21,70,ALT-AZ,0,
    # KVNYS,KY,Korea,37.565159,126.941027,92,Korean VLBI Network Yonsei,21,70,ALT-AZ,0,
    # my xyz
    # "alt": 541, "lat": 37.533, "lon": 128.449, "name": "KVN-Pyeonchang"
    # "alt": 122, "lat": 37.565, "lon": 126.941, "name": "KVN-Yonsei"

    # don't use the KPC numbers from this pdf, they are apparently wrong ... KYS is good
    # https://radio.kasi.re.kr/status_report/files/KVN_status_report_2023.pdf

    # future... no vex assigned, from ngehtsim/files/Telescope_Site_Matrix.csv
    # new ngEHT':   ['BAJA','CNI','GAM','HAY','JELM','LAS','LLA','OVRO']
    {'name': 'BAJA', 'lat': 31.043898, 'lon': -115.463636, 'alt': 2802},
    {'name': 'CNI', 'lat': 28.299309, 'lon': -16.508709, 'alt': 2364},
    {'name': 'GAM', 'lat': -23.3393, 'lon': 16.229246, 'alt': 2342},
    {'name': 'HAY', 'lat': 42.623943, 'lon': -71.488769, 'alt': 114},
    {'name': 'JELM', 'lat': 41.096991, 'lon': -105.976692, 'alt': 2943},
    {'name': 'LAS', 'lat': -29.031711, 'lon': -70.685063, 'alt': 2321},
    {'name': 'LLA', 'lat': -24.192081, 'lon': -66.474786, 'alt': 4781},
    {'name': 'OVRO', 'lat': 37.231409, 'lon': -118.282436, 'alt': 1207},
    # GLT summit
    {'name': 'GLTS', 'x': 1500559.643, 'y': -1191855.397, 'z': 6066429.689},

    # values I had from 2020
    #{'name': 'BAJA', 'x': -2352576.31173, 'y': -4940331.41122, 'z': 3271508.49374},
    #{'name': 'CNI', 'x': 5327340.914, 'y': -1719123.635, 'z': 3051442.006},  # moved a bit in 2024
    #{'name': 'GAM', 'x': 5627251.83789, 'y': 1632172.52014, 'z': -2517405.60946},  # moved a bit in 2024
    #{'name': 'HAY', 'x': 1492420.4965, 'y': -4457272.10037, 'z': 4296891.72893},
    # no JELM
    #{'name': 'LAS', 'x': 1837842.4657, 'y': -5259233.4926, 'z': -3099889.2125},  # moved a bit in 2024
    # no LLA
    #{'name': 'OVRO', 'x': -2409598.8669, 'y': -4478350.4481, 'z': 3838603.7849},

    # no longer under consideration for ngEHT
    #{'name': 'BOL', 'x': 2282100.27386, 'y': -5685901.71836, 'z': -1785763.38112},
    #{'name': 'VLT', 'x': 1946473.62308, 'y': -5467592.1824, 'z': -2642703.01185},
    #{'name': 'PIKES', 'x': -1292058.67099, 'y': -4807190.10901, 'z': 3981241.60693},
    #{'name': 'VLA', 'x': -1601201.2, 'y': -5042007.4, 'z': 3554843.0},
    #{'name': 'CAT', 'x': 1527175.7929, 'y': -4560875.7694, 'z': -4178033.6314},
    #{'name': 'BRZ', 'x': 4459534.3070, 'y': -3987698.0176, 'z': -2211711.7988},
]

geodetic_stations = []

for s in stations:
    if 'lat' in s:
        # ngEHT new stations
        geod = s
    else:
        loc = EarthLocation.from_geocentric(s['x']*u.m, s['y']*u.m, s['z']*u.m)
        locg = loc.geodetic
        geod = {
            'name': s['name'],
            'lat': round(locg.lat.value, 3),
            'lon': round(locg.lon.value, 3),
            'alt': round(locg.height.value),
        }
        if 'vex' in s:
            geod['vex'] = s['vex']
    if 'vex' not in geod and '/' in geod['name']:
        raise ValueError('name must be a valid directory name: '+geod['name'])
    geodetic_stations.append(geod)

print(json.dumps(geodetic_stations, sort_keys=True, indent=4))
