import subprocess
import pygrib
import math
import os
import sys
import math

from .constants import LEVELS, GFS_DAY, LATLON_DELTA
from .latlon import box

header_amc = '''
#
# This header is prepended to the atmospheric layers generated by
# gfs16_to_am10.py to generate a complete am configuration file.
#
f 225 GHz 225 GHz 1 GHz
output f GHz tau Tb K
T0 2.7 K
'''
# XXX hint: this for 345 ghz 'f  345 GHz 345 GHz 1 GHz'

LAYER_HEADER = """
#
# Layer data below were derived from NCEP GFS model data obtained
# from the NOAA Operational Model Archive Distribution System
# (NOMADS).  See http://nomads.ncep.noaa.gov for more information.
#
#         Production date: {0}
#                   Cycle: {1:02d} UT
#                 Product: {2}
#
# Interpolated to
#
#                latitude: {3} deg. N
#               longitude: {4} deg. E
#   Geopotential altitude: {5} m
#
"""


def grid_interp(a, u, v):
    return (a[0][0] * (1.0 - u) * (1.0 - v) + a[1][0] * u * (1.0 - v)
          + a[0][1] * (1.0 - u) * v         + a[1][1] * u * v       )


def grid_interp_vector(a, b, u, v):
    c = [None, None]
    c[0] = [None, None]
    c[1] = [None, None]
    for i in range(0, 2):
        for j in range(0, 2):
            c[i][j] = math.sqrt(a[i][j]**2 + b[i][j]**2)

    return grid_interp(c, u, v)


# Numerical and physical constants
BADVAL              = -99999.  # placeholder for missing or undefined data
BADVAL_TEST         = -99998.
G_STD               = 9.80665  # standard gravity [m / s^2]
M_AIR               = 28.964   # average dry air mass [g / mole]
M_O3                = 47.997   # O3 mass [g / mole]
H2O_SUPERCOOL_LIMIT = 238.     # Assume ice below this temperature [K]
PASCAL_ON_MBAR      = 100.     # conversion from mbar (hPa) to Pa

RH_TOP_PLEVEL = 29.
STRAT_H2O_VMR = 5e-6

# https://www.nco.ncep.noaa.gov/pmb/products/gfs/gfs.t00z.pgrb2.0p25.anl.shtml
# https://www.nco.ncep.noaa.gov/pmb/products/gfs/gfs.t00z.pgrb2.0p25.f000.shtml
# https://www.nco.ncep.noaa.gov/pmb/products/gfs/gfs.t00z.pgrb2.0p25.f003.shtml -- layers beyond 0

# https://www.nco.ncep.noaa.gov/pmb/products/gfs/gfs.t00z.pgrb2b.0p25.anl.shtml
# https://www.nco.ncep.noaa.gov/pmb/products/gfs/gfs.t00z.pgrb2b.0p25.f000.shtml
# https://www.nco.ncep.noaa.gov/pmb/products/gfs/gfs.t00z.pgrb2b.0p25.f003.shtml -- layers beyond 0

scalar_gribs = [  # this table is not yet used
    {'lev': 'surface', 'var': ['CSNOW'], 'name': 'Categorial snow', 'level': [0]},  # f000 and f003 but not anl (?) and it's "3 hour fcst" and "0-3 hour ave" in "Forecast Valid"... "analysis" in f000
    {'lev': 'surface', 'var': ['CICEP'], 'name': 'Categorical ice pellets', 'level': [0]},
    {'lev': 'surface', 'var': ['CFRZR'], 'name': 'Categorical freezing rain', 'level': [0]},
    {'lev': 'surface', 'var': ['CRAIN'], 'name': 'Categorical rain', 'level': [0]},
    {'lev': 'surface', 'var': ['GUST'], 'name': 'Wind speed (gust)', 'level': [0]},  # f000 and f003 surface and not anl? "3 hour fcst" at f003, "analysis" in f000
]

vector_gribs = [  # this table is not yet used
    # these come in pairs and need a different interpolation function
    {'lev': ['max_wind'], 'var': ['GUST'], 'name': 'U component of wind', 'level': [0], 'ourname': 'wind gust'},  # f0003 "3 hour fcst" vs "analysis" and "analyis" for anl and f000
    {'lev': ['max_wind'], 'var': ['GUST'], 'name': 'V component of wind', 'level': [0], 'ourname': 'wind gust'},
    {'lev': ['1'], 'var': ['UGRD'], 'name': 'U component of wind', 'level': [1], 'ourname': 'low wind'},  # anl: level 1 and up, also PV=blah, f000: "planwetary boundary layer", layer 1, "10 m above ground"
    {'lev': ['1'], 'var': ['VGRD'], 'name': 'V component of wind', 'level': [1], 'ourname': 'low wind'},
]


def grib2_to_extra_information(grbindx, u, v):
    '''
pygrib clues
grbindx.select only works on the named args named in the pygrib.index() call (name and level, here)
didn't have much luck having more than 2 index names in the pygrib.index call -- could probably make multiple indices
or you can use pygrib.open() instead, to not have an index, it's supposedly slower but these grib files are small (2k/station)
    '''
    ret = {}

    try:
        # appears for lev_surface at level 0
        # if the grib comes back damaged, the crash is going to be here
        k = 'csnow'
        ret['csnow'] = (grid_interp(grbindx.select(name='Categorical snow', level=0)[0].values, u, v))
        k = 'cicep'
        ret['cicep'] = (grid_interp(grbindx.select(name='Categorical ice pellets', level=0)[0].values, u, v))
        k = 'cfrzr'
        ret['cfrzr'] = (grid_interp(grbindx.select(name='Categorical freezing rain', level=0)[0].values, u, v))
        k = 'crain'
        ret['crain'] = (grid_interp(grbindx.select(name='Categorical rain', level=0)[0].values, u, v))

        # appears for lev_surface at level 0
        k = 'wgust'
        ret['wgust'] = (grid_interp(grbindx.select(name='Wind speed (gust)', level=0)[0].values, u, v))

        # appears for lev_max_wind at level 0
        k = 'max wind u'
        a = grbindx.select(name='U component of wind', level=0)[0].values
        k = 'max wind v'
        b = grbindx.select(name='V component of wind', level=0)[0].values
        ret['max_wind'] = grid_interp_vector(a, b, u, v)

        # appears for lev_10_m_above_ground
        a = grbindx.select(name='10 metre U wind component', level=10)[0].values
        b = grbindx.select(name='10 metre V wind component', level=10)[0].values
        ret['10m_wind'] = grid_interp_vector(a, b, u, v)
    except Exception as e:
        print('key:', k, 'exception:', e, file=sys.stderr)
        raise
    return ret


def grib2_to_am_layers(gribname, lat, lon, alt):
    grbindx = pygrib.index(gribname, "name", "level")  # on-disk

    # in memory -- not sure what syntax actually works for this?
    # need to .index() after creation
    # gribfile = pygrib.fromstring(grib_buffer)
    # gribindx = ???

    # is the grib valid? Categorical snow is our known occasional crash
    try:
        grbindx.select(name='Categorical snow', level=0)
    except ValueError:
        print('invalid grib seen', file=sys.stderr)
        names = set()
        for mess in pygrib.open(gribname):
            names.add(mess['name'])
        print(' grib names are:', sorted(names))
        raise

    leftlon, rightlon, bottomlat, toplat = box(lat, lon, LATLON_DELTA)

    # from a complete grib to the subset:
    # data, lats, lons = grb.data(lat1=20,lat2=70,lon1=220,lon2=320)

    u = (lat - bottomlat) / LATLON_DELTA
    v = (lon - leftlon) / LATLON_DELTA
    Pbase     = []
    z         = []
    T         = []
    o3_vmr    = []
    RH        = []
    cloud_lmr = []
    cloud_imr = []

    extra = grib2_to_extra_information(grbindx, u, v)

    for i, lev in enumerate(LEVELS):
        Pbase.append(lev)
        try:
            x = (grid_interp(grbindx.select(
                name="Geopotential Height", level=lev)[0].values, u, v))
            z.append(x)
        except:
            print('point 1', file=sys.stderr)
            raise  # XXX debug these bad gribs
            z.append(BADVAL)
        try:
            x = (grid_interp(grbindx.select(
                name="Temperature", level=lev)[0].values, u, v))
            T.append(x)
        except:
            print('point 2', file=sys.stderr)
            raise  # XXX debug these bad gribs
            T.append(BADVAL)
        try:
            x = (grid_interp(grbindx.select(
                name="Ozone mixing ratio", level=lev)[0].values, u, v))
            x *= M_AIR / M_O3  # convert mass mixing ratio to volume mixing ratio
            o3_vmr.append(x)
        except:
            # this is not unusual
            o3_vmr.append(0.0)
        try:
            x = (grid_interp(grbindx.select(
                name="Relative humidity", level=lev)[0].values, u, v))
            # Greg: this used to have 'if (lev >= RH_TOP_PLEVEL)' in gfs15_to_am
            # now it throws the exception
            RH.append(x)
        except:
            RH.append(0.0)
            print('point 4', file=sys.stderr)
        try:
            x = (grid_interp(grbindx.select(
                name="Cloud mixing ratio", level=lev)[0].values, u, v))
            cloud_lmr.append(x)
        except:
            # this is not unusual
            cloud_lmr.append(0.0)
        try:
            x = (grid_interp(grbindx.select(
                name="Ice water mixing ratio", level=lev)[0].values, u, v))
            cloud_imr.append(x)
        except:
            # this is not unusual
            cloud_imr.append(0.0)

    return Pbase, z, T, o3_vmr, RH, cloud_lmr, cloud_imr, extra


def print_extra(gfs_cycle, forecast_hour, extra):
    # extra is a dict
    # gfs_cycle forms the filename
    # forecast hour
    fname = gfs_cycle.strftime(GFS_TIMESTAMP)
    dt_forecast_hour = gfs_cycle + datetime.timedelta(hours=forecast_hour)
    rowname = dt_forecast_hour.strftime(GFS_TIMESTAMP)
    # XXX write a csv line
    # the normal output file is f, passed to print_final_output, passed into compute_one_hour, by make_forecast_table, which is called by cli.main
    pass


def print_am_header(gfs_cycle, forecast_hour, lat, lon, alt):
    gfs_day = gfs_cycle.strftime(GFS_DAY)
    gfs_hour = gfs_cycle.hour
    gfs_product = 'f{:03d}'.format(forecast_hour)
    if (gfs_product == "anl"):
        product_str = "analysis"
    else:
        product_str = gfs_product[1:] + " hour forecast"
    print(LAYER_HEADER.format(gfs_day, gfs_hour, product_str, lat, lon, alt))


def print_am_layers(alt, Pbase, z, T, o3_vmr, RH, cloud_lmr, cloud_imr):
    for i, lev in enumerate(LEVELS):
        if (z[i] < alt):
            break
        print("layer")
        print("Pbase {0:.1f} mbar  # {1:.1f} m".format(Pbase[i], z[i]))
        print("Tbase {0:.1f} K".format(T[i]))
        print("column dry_air vmr")
        if (i > 0):
            o3_vmr_mid    = 0.5 * (   o3_vmr[i-1] +    o3_vmr[i])
            RH_mid        = 0.5 * (       RH[i-1] +        RH[i])
            cloud_lmr_mid = 0.5 * (cloud_lmr[i-1] + cloud_lmr[i])
            cloud_imr_mid = 0.5 * (cloud_imr[i-1] + cloud_imr[i])
            T_mid         = 0.5 * (        T[i-1] +         T[i])
        else:
            o3_vmr_mid    = o3_vmr[i]
            RH_mid        = RH[i]
            cloud_lmr_mid = cloud_lmr[i]
            cloud_imr_mid = cloud_imr[i]
            T_mid         = T[i]
        if (o3_vmr_mid > 0.0):
            print("column o3 vmr {0:.3e}".format(o3_vmr_mid))
        if (Pbase[i] > RH_TOP_PLEVEL):
            if (T_mid < H2O_SUPERCOOL_LIMIT):
                print("column h2o RHi {0:.2f}%".format(RH_mid))
            else:
                print("column h2o RH {0:.2f}%".format(RH_mid))
        else:
            print("column h2o vmr {0:.3e}".format(STRAT_H2O_VMR))
        if (cloud_lmr_mid > 0.0):
            #
            # Convert cloud liquid water mixing ratio [kg / kg] to
            # cloud total liquid water across the layer [kg / m^2].
            # Below the supercooling limit, assume any liquid water
            # is really ice.  (GFS 15 occasionally had numerically
            # negligible amounts of liquid water at unphysically
            # low temperature.)
            #
            dP = PASCAL_ON_MBAR * (Pbase[0] if i == 0 else Pbase[i] - Pbase[i-1])
            m = dP / G_STD
            ctw = m * cloud_lmr_mid
            if (T_mid < H2O_SUPERCOOL_LIMIT):
                print("column iwp_abs_Rayleigh {0:.3e} kg*m^-2".format(ctw))
            else:
                print("column lwp_abs_Rayleigh {0:.3e} kg*m^-2".format(ctw))
        if (cloud_imr_mid > 0.0):
            #
            # Convert cloud ice mixing ratio [kg / kg] to cloud total
            # ice across the layer [kg / m^2].
            #
            dP = PASCAL_ON_MBAR * (Pbase[0] if i == 0 else Pbase[i] - Pbase[i-1])
            m = dP / G_STD
            cti = m * cloud_imr_mid
            print("column iwp_abs_Rayleigh {0:.3e} kg*m^-2".format(cti))
        print("")

    if (z[i] == alt):
        return

    u      = (alt - z[i-1]) / (z[i] - z[i-1])
    logP_s = u * math.log(Pbase[i]) + (1.0 - u) * math.log(Pbase[i-1])
    P_s    = math.exp(logP_s)
    T_s    = u * T[i] + (1.0 - u) * T[i-1]
    T_mid  = 0.5 * (T_s + T[i-1])

    #
    # Other variables are interpolated or extrapolated linearly in P
    # to the base level and clamped at zero.
    #
    u = (P_s - Pbase[i-1]) / (Pbase[i] - Pbase[i-1])
    o3_vmr_s    = u *    o3_vmr[i] + (1.0 - u) *    o3_vmr[i-1]
    RH_s        = u *        RH[i] + (1.0 - u) *        RH[i-1]
    cloud_lmr_s = u * cloud_lmr[i] + (1.0 - u) * cloud_lmr[i-1]
    cloud_imr_s = u * cloud_imr[i] + (1.0 - u) * cloud_imr[i-1]
    if (o3_vmr_s < 0.0):
        o3_vmr_s = 0.0
    if (RH_s < 0.0):
        RH_s = 0.0
    if (cloud_lmr_s < 0.0):
        cloud_lmr_s = 0.0
    if (cloud_imr_s < 0.0):
        cloud_imr_s = 0.0
    o3_vmr_mid    = 0.5 * (   o3_vmr[i-1] +    o3_vmr_s)
    RH_mid        = 0.5 * (       RH[i-1] +        RH_s)
    cloud_lmr_mid = 0.5 * (cloud_lmr[i-1] + cloud_lmr_s)
    cloud_imr_mid = 0.5 * (cloud_imr[i-1] + cloud_imr_s)
    print("layer")
    print("Pbase {0:.1f} mbar  # {1:.1f} m".format(P_s, alt))
    print("Tbase {0:.1f} K".format(T_s))
    print("column dry_air vmr")
    if (o3_vmr_mid > 0.0):
        print("column o3 vmr {0:.3e}".format(o3_vmr_mid))
    if (P_s > RH_TOP_PLEVEL):
        if (T_mid < H2O_SUPERCOOL_LIMIT):
            print("column h2o RHi {0:.2f}%".format(RH_mid))
        else:
            print("column h2o RH {0:.2f}%".format(RH_mid))
    else:
        print("column h2o vmr {0:.3e}".format(STRAT_H2O_VMR))
    if (cloud_lmr_mid > 0.0):
        dP = PASCAL_ON_MBAR * (Pbase[0] if i == 0 else Pbase[i] - Pbase[i-1])
        m = dP / G_STD
        ctw = m * cloud_lmr_mid
        if (T_mid < H2O_SUPERCOOL_LIMIT):
            print("column iwp_abs_Rayleigh {0:.3e} kg*m^-2".format(ctw))
        else:
            print("column lwp_abs_Rayleigh {0:.3e} kg*m^-2".format(ctw))
    if (cloud_imr_mid > 0.0):
        dP = PASCAL_ON_MBAR * (Pbase[0] if i == 0 else Pbase[i] - Pbase[i-1])
        m = dP / G_STD
        cti = m * cloud_imr_mid
        print("column iwp_abs_Rayleigh {0:.3e} kg*m^-2".format(cti))


def run_am(layers_amc):
    stdin = header_amc.encode() + layers_amc.encode()

    args = (os.environ['AM'], '-')

    completed = subprocess.run(args, input=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    returncode = completed.returncode
    stdout = completed.stdout.decode()  # one line with the integrated opacity
    stderr = completed.stderr.decode()  # verbose stuff

    return returncode, stdout, stderr


def summarize_am(am_output, am_error):
    lwp = 0.
    iwp = 0.
    for line in am_error.splitlines():
        if line.startswith('#'):
            if 'h2o' in line:
                pwv = float(line.split()[2])
            if 'lwp_abs_Rayleigh' in line:
                lwp = float(line.split()[2])
            if 'iwp_abs_Rayleigh' in line:
                iwp = float(line.split()[2])
            if 'o3' in line:
                o3 = float(line.split()[2])

    parts = am_output.split()
    tau = float(parts[1])
    Tb = float(parts[2])

    MM_PWV   = 3.3427e21
    KG_ON_M2 = 3.3427e21
    DU       = 2.6868e16

    return tau, Tb, pwv / MM_PWV, lwp / KG_ON_M2, iwp / KG_ON_M2, o3 / DU
