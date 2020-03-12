import datetime
import os.path
import subprocess
import math
import requests
import sys
import time
import io
import contextlib
import tempfile
from argparse import ArgumentParser
import json

import pygrib

from timer_utils import record_latency, dump_latency_histograms

sites = [
    {'name': 'sma', 'desc': 'the SMA', 'lat': 19.824, 'lon': -155.478, 'alt': 4080},
]


expected_lines = 210
datadir = 'output'
appdir = '.'
header_amc = appdir + '/header.amc'
am_executable = '/usr/local/bin/am'

GFS_TIMESTAMP = '%Y%m%d_%H:00:00'
GFS_DAYHOUR = '%Y%m%d/%H'
GFS_DAY = '%Y%m%d'
GFS_HOUR = '%H'
table_header = ('#', 'date', 'tau255', 'Tb[K]', 'pwv[mm]', 'lwp[kg*m^-2]', 'iwp[kg*m^-2]', 'o3[DU]')

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


def latest_gfs_cycle_time():
    gfs_lag = 5.2  # hours
    dt_gfs_lag = datetime.timedelta(hours=gfs_lag)
    dt_gfs     = datetime.datetime.utcnow() - dt_gfs_lag
    dt_gfs     = dt_gfs.replace(hour=int(dt_gfs.hour / 6) * 6, minute=0, second=0, microsecond=0)
    return dt_gfs


def ok(outfile):
    if not os.path.exists(outfile):
        return False
    with open(outfile) as f:
        count = len(f.readlines())
        if count != expected_lines:
            print('GREG saw', count, 'lines')
            return False


table_line_string = '{:1s}{:>16s} {:>12s} {:>12s} {:>12s} {:>12s} {:>12s} {:>12s}'
table_line_floats = '{} {:12.4e} {:12.4e} {:12.4e} {:12.4e} {:12.4e} {:12.4e}'


def print_table_line(fields, f):
    print(table_line_string.format(*fields), file=f)


LATLON_GRID_STR = "0p25"
LEVELS = (1, 2, 3, 5, 7, 10, 20, 30, 50, 70, 100, 150, 200, 250, 300, 350, 400,
          450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 925, 950, 975, 1000)


def form_gfs_download_url(lat, lon, alt, gfs_cycle, forecast_hour):
    CGI_URL = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_{}_1hr.pl"
    url = CGI_URL.format(LATLON_GRID_STR)

    latlon_delta = float(LATLON_GRID_STR[0:1]) + 0.01 * float(LATLON_GRID_STR[2:])  # 0p25 -> 0.25
    leftlon = math.floor(lon / latlon_delta) * latlon_delta
    rightlon = leftlon + latlon_delta
    bottomlat = math.floor(lat / latlon_delta) * latlon_delta
    toplat = bottomlat + latlon_delta

    gfs_dayhour = gfs_cycle.strftime(GFS_DAYHOUR)
    gfs_hour = gfs_cycle.strftime(GFS_HOUR)
    gfs_product = 'f{:03d}'.format(forecast_hour)

    params = {
        'dir': '/gfs.{}'.format(gfs_dayhour),
        'file': 'gfs.t{}z.pgrb2.{}.{}'.format(gfs_hour, LATLON_GRID_STR, gfs_product),
        'subregion': '',
        'leftlon': leftlon,
        'rightlon': rightlon,
        'toplat': toplat,
        'bottomlat': bottomlat,
    }

    LEVELS = (1, 2, 3, 5, 7, 10, 20, 30, 50, 70, 100, 150, 200, 250, 300, 350, 400,
              450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 925, 950, 975, 1000)
    for lev in LEVELS:
        params['lev_{:d}_mb'.format(lev)] = 'on'
    VARIABLES = ("CLWMR", "ICMR", "HGT", "O3MR", "RH", "TMP")
    for var in VARIABLES:
        params['var_' + var] = 'on'

    return url, params


def fetch_gfs_download(url, params):
    # Timeouts and retries
    CONN_TIMEOUT        = 4        # Initial server response timeout in seconds
    READ_TIMEOUT        = 4        # Stalled download timeout in seconds
    RETRY_DELAY         = 60       # Delay before retry (NOAA requests 60 s)
    MAX_DOWNLOAD_TRIES  = 4

    retry = MAX_DOWNLOAD_TRIES
    while retry > 0:
        try:
            r = requests.get(url, params=params, timeout=(CONN_TIMEOUT, READ_TIMEOUT))
            if r.status_code == requests.codes.ok:
                errflag = 0
            else:
                errflag = 1
                print('url was', r.url, file=sys.stderr)
                print("Download failed with status code {0}".format(r.status_code),
                      file=sys.stderr, end='')
                print('content is', r.content, file=sys.stderr)
        except requests.exceptions.ConnectTimeout:
            print("Connection timed out.", file=sys.stderr, end='')
            errflag = 1
        except requests.exceptions.ReadTimeout:
            print("Data download timed out.", file=sys.stderr, end='')
            errflag = 1
        if (errflag):
            retry = retry - 1
            if (retry):
                print("  Retrying...", file=sys.stderr)
                time.sleep(RETRY_DELAY)
            else:
                print("  Giving up.", file=sys.stderr)
                print("Failed URL was: ", file=sys.stderr)
                print(url, file=sys.stderr)
                exit(1)
        else:
            break

    return r.content


def download_gfs(lat, lon, alt, gfs_cycle, forecast_hour):
    url, params = form_gfs_download_url(lat, lon, alt, gfs_cycle, forecast_hour)
    grib_buffer = fetch_gfs_download(url, params)
    return grib_buffer


def grid_interp(a, u, v):
    return (a[0][0] * (1.0 - u) * (1.0 - v) + a[1][0] * u * (1.0 - v)
          + a[0][1] * (1.0 - u) * v         + a[1][1] * u * v       )


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


def grib2_to_am_layers(grib_buffer, lat, lon, alt):
    with tempfile.NamedTemporaryFile(mode='wb', prefix='temp-', suffix='.grb') as f:
        f.write(grib_buffer)
        try:
            grbindx = pygrib.index(f.name, "name", "level")
        except Exception as e:
            # stderr is being captured so we can't print to it
            # example: RuntimeError: b'End of resource reached when reading message'
            msg = 'pygrib raised {}, length of input was {}'.format(str(e), len(grib_buffer))
            raise RuntimeError(msg)

    # in memory -- not sure what syntax actually works for this?
    # need to .index() after creation
    # grbindx = pygrib.fromstring(grib_buffer)

    latlon_delta = float(LATLON_GRID_STR[0:1]) + 0.01 * float(LATLON_GRID_STR[2:])
    leftlon = math.floor(lon / latlon_delta) * latlon_delta
    bottomlat = math.floor(lat / latlon_delta) * latlon_delta

    u = (lat - bottomlat) / latlon_delta
    v = (lon - leftlon) / latlon_delta
    Pbase     = []
    z         = []
    T         = []
    o3_vmr    = []
    RH        = []
    cloud_lmr = []
    cloud_imr = []

    for i, lev in enumerate(LEVELS):
        Pbase.append(lev)
        try:
            x = (grid_interp(grbindx.select(
                name="Geopotential Height", level=lev)[0].values, u, v))
            z.append(x)
        except:
            z.append(BADVAL)
        try:
            x = (grid_interp(grbindx.select(
                name="Temperature", level=lev)[0].values, u, v))
            T.append(x)
        except:
            T.append(BADVAL)
        try:
            x = (grid_interp(grbindx.select(
                name="Ozone mixing ratio", level=lev)[0].values, u, v))
            x *= M_AIR / M_O3  # convert mass mixing ratio to volume mixing ratio
            o3_vmr.append(x)
        except:
            o3_vmr.append(0.0)
        try:
            x = (grid_interp(grbindx.select(
                name="Relative humidity", level=lev)[0].values, u, v))
            if (lev >= RH_TOP_PLEVEL):
                RH.append(x)
            else:
                RH.append(0.0)
        except:
            RH.append(0.0)
        try:
            x = (grid_interp(grbindx.select(
                name="Cloud mixing ratio", level=lev)[0].values, u, v))
            cloud_lmr.append(x)
        except:
            cloud_lmr.append(0.0)
        try:
            x = (grid_interp(grbindx.select(
                name="Ice water mixing ratio", level=lev)[0].values, u, v))
            cloud_imr.append(x)
        except:
            cloud_imr.append(0.0)

    return Pbase, z, T, o3_vmr, RH, cloud_lmr, cloud_imr


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
        if (RH_mid > 0.0):
            if (T_mid > H2O_SUPERCOOL_LIMIT):
                print("column h2o RH {0:.2f}%".format(RH_mid))
            else:
                print("column h2o RHi {0:.2f}%".format(RH_mid))
        if (cloud_lmr_mid > 0.0):
            #
            # Convert cloud liquid water mixing ratio [kg / kg] to
            # cloud total liquid water across the layer [kg / m^2].
            # Below the supercooling limit, assume any liquid water
            # is really ice.  (GFS 15 occasionally has numerically
            # negligible amounts of liquid water at unphysically
            # low temperature.)
            #
            dP = PASCAL_ON_MBAR * (Pbase[i] - Pbase[i-1])
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
            dP = PASCAL_ON_MBAR * (Pbase[i] - Pbase[i-1])
            m = dP / G_STD
            cti = m * cloud_imr_mid
            print("column iwp_abs_Rayleigh {0:.3e} kg*m^-2".format(cti))
        print("")

    if (z[i] == alt):
        return

    u = (alt - z[i-1]) / (z[i] - z[i-1])
    logP_s = u * math.log(Pbase[i]) + (1.0 - u) * math.log(Pbase[i-1]) 
    P_s = math.exp(logP_s)
    T_s = u * T[i] + (1.0 - u) * T[i-1]

    #
    # Other variables are interpolated or extrapolated linearly in P
    # to the base level and clamped at zero.
    #
    u = (P_s - Pbase[i-1]) / (Pbase[i] - Pbase[i-1])
    o3_vmr_s    =   u * o3_vmr[i]  + (1.0 - u) *    o3_vmr[i-1]
    RH_s        =       u * RH[i]  + (1.0 - u) *        RH[i-1]
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
    if (RH_mid > 0.0):
        if (T_mid > H2O_SUPERCOOL_LIMIT):
            print("column h2o RH {0:.2f}%".format(RH_mid))
        else:
            print("column h2o RHi {0:.2f}%".format(RH_mid))
    if (cloud_lmr_mid > 0.0):
        dP = PASCAL_ON_MBAR * (Pbase[i] - Pbase[i-1])
        m = dP / G_STD
        ctw = m * cloud_lmr_mid
        print("column lwp_abs_Rayleigh {0:.3e} kg*m^-2".format(ctw))
    if (cloud_imr_mid > 0.0):
        dP = PASCAL_ON_MBAR * (Pbase[i] - Pbase[i-1])
        m = dP / G_STD
        cti = m * cloud_imr_mid
        print("column iwp_abs_Rayleigh {0:.3e} kg*m^-2".format(cti))


def gfs15_to_am10(lat, lon, alt, gfs_cycle, forecast_hour):
    grib_buffer = download_gfs(lat, lon, alt, gfs_cycle, forecast_hour)

    if len(grib_buffer) < 20000:  # should be 28kb
        print('suspiciously small grib file of length', len(grib_buffer), file=sys.stderr)

    my_stdout = io.StringIO()
    my_stderr = io.StringIO()
    with contextlib.redirect_stdout(my_stdout):
        with contextlib.redirect_stderr(my_stderr):
            print_am_header(gfs_cycle, forecast_hour, lat, lon, alt)
            Pbase, z, T, o3_vmr, RH, cloud_lmr, cloud_imr = grib2_to_am_layers(grib_buffer, lat, lon, alt)
            print_am_layers(alt, Pbase, z, T, o3_vmr, RH, cloud_lmr, cloud_imr)

    if my_stderr.tell():
        success = False
    else:
        success = True

    return success, my_stdout.getvalue(), my_stderr.getvalue()


def run_am(header_amc, layers_amc):
    with open(header_amc, 'rb') as f:
        stdin = f.read()
    stdin += layers_amc.encode()

    args = (am_executable, '-')

    completed = subprocess.run(args, input=stdin, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = completed.stdout

    return output.decode()
    # after I learn if stderr really needs to be interleaved, split it out?


def summarize_am(am_output):
    lwp = 0.
    iwp = 0.
    for line in am_output.splitlines():
        if line.startswith('#'):
            if 'h2o' in line:
                pwv = float(line.split()[2])
            if 'lwp_abs_Rayleigh' in line:
                lwp = float(line.split()[2])
            if 'iwp_abs_Rayleigh' in line:
                iwp = float(line.split()[2])
            if 'o3' in line:
                o3 = float(line.split()[2])
        elif line and line[0].isdigit():
            parts = line.split()
            tau = float(parts[1])
            Tb = float(parts[2])

    MM_PWV   = 3.3427e21
    KG_ON_M2 = 3.3427e21
    DU       = 2.6868e16

    return tau, Tb, pwv / MM_PWV, lwp / KG_ON_M2, iwp / KG_ON_M2, o3 / DU


def print_final_output(gfs_timestamp, tau, Tb, pwv, lwp, iwp, o3, f):
    out = table_line_floats.format(gfs_timestamp, tau, Tb, pwv, lwp, iwp, o3)
    print(out, file=f)
    f.flush()
    print(out, file=sys.stderr)


def compute_one_hour(site, gfs_cycle, forecast_hour, f):
    print('fetching for hour', forecast_hour, file=sys.stderr)
    with record_latency('fetch gfs data'):
        success, layers_amc, layers_err = gfs15_to_am10(site['lat'], site['lon'], site['alt'], gfs_cycle, forecast_hour)
    if not success:
        with tempfile.NamedTemporaryFile(mode='w', prefix='layers-err-', dir='.', delete=False) as tfile:
            print('some problem turning the grib into layers, saving stderr to', tfile.name)
            tfile.write(layers_err)
            return  # no line emitted

    dt_forecast_hour = gfs_cycle + datetime.timedelta(hours=forecast_hour)
    with record_latency('run am'):
        am_output = run_am(header_amc, layers_amc)

    try:
        tau, Tb, pwv, lwp, iwp, o3 = summarize_am(am_output)
    except UnboundLocalError:
        with tempfile.NamedTemporaryFile(mode='w', prefix='weird-am-output-', dir='.', delete=False) as tfile:
            print('Did not see complete output from AM, saving AM output to', tfile.name)
            # example: -(35) : The volume mixing ratio must be in the range 0 to 1.
            # ! Error: parse error.
            tfile.write('Input:\n\n')
            with open(header_amc, 'rb') as f:
                tfile.write(f.read())
            tfile.write(layers_amc)
            tfile.write('\nOutput:\n\n')
            tfile.write(am_output)
            return  # no line emitted
    print_final_output(dt_forecast_hour.strftime(GFS_TIMESTAMP), tau, Tb, pwv, lwp, iwp, o3, f)
    dump_latency_histograms()
    time.sleep(1)


def make_forecast_table(site, gfs_cycle, f):
    print_table_line(table_header, f)
    for forecast_hour in range(0, 121):
        compute_one_hour(site, gfs_cycle, forecast_hour, f)
    for forecast_hour in range(123, 385, 3):
        compute_one_hour(site, gfs_cycle, forecast_hour, f)


def read_stations(filename):
    with open(filename, 'r') as f:
        return json.load(f)

        
def main(args=None):
    parser = ArgumentParser(description='gfs-tau-fetcher command line tool')
    parser.add_argument('--vex', action='append', help='station(s) to fetch')
    parser.add_argument('--stations', action='store', default='stations.json', help='station configuration file (default: stations.json)')
    parser.add_argument('--backfill', action='store', default=0, type=int, help='hours to backfill')
    parser.add_argument('--cycle', action='store', help='gfs cycle to fetch (e.g. 2020031200)')
    args = parser.parse_args(args=args)

    station_locations = read_stations(args.stations)
    station_dict = dict([(v['vex'], v) for v in station_locations])

    if not args.vex:
        stations = station_dict.keys()
    else:
        stations = []
        for vex in args.vex:
            if ',' in vex:
                vexes = vex.split(',')
            else:
                vexes = (vex,)
            for v in vexes:
                if v in station_dict:
                    stations.append(v)
                else:
                    print('unknown vex', v, file=sys.stderr)

    cycles = []
    if args.cycle:
        c = args.cycle
        if len(c) not in (8, 10):
            raise ValueError('unknown cycle time format, expecting YYYYMMDDHH: '+args.cycle)
        if len(c) == 8:
            c += '00'
        gfs_starting_cycle = datetime.datetime.strptime(c, '%Y%m%d%H')
    else:
        gfs_starting_cycle = latest_gfs_cycle_time()

    end_hours = 1
    if args.backfill:
        end_hours = args.backfill + 1
    for hours_ago in range(0, end_hours, 6):
        dt_gfs_lag = datetime.timedelta(hours=-hours_ago)
        gfs_cycle = (gfs_starting_cycle + dt_gfs_lag)
        cycles.append(gfs_cycle)

    for vex in stations:
        station = station_dict[vex]
        for gfs_cycle in cycles:
            print('processing station', vex, 'cycle', gfs_cycle.strftime(GFS_TIMESTAMP), file=sys.stderr)
            outdir = '{}/{}'.format(datadir, vex)
            outfile = '{}/{}'.format(outdir, gfs_cycle.strftime(GFS_TIMESTAMP))
            if ok(outfile):
                print('outfile {} seems ok, not re-fetching'.format(outfile), file=sys.stder)
                continue
            os.makedirs(outdir, exist_ok=True)
            with open(outfile, 'w') as f:
                make_forecast_table(station, gfs_cycle, f)


if __name__ == '__main__':
    main()
