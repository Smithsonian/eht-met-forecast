import datetime
import os.path
import sys
import time
import io
import contextlib
import tempfile
import json

from .constants import GFS_TIMESTAMP
from .timer_utils import record_latency
from .am import grib2_to_am_layers, print_am_header, print_am_layers, run_am, summarize_am, header_amc
from .gfs import download_gfs

expected_lines = 210
table_header = ('#', 'date', 'tau255', 'Tb[K]', 'pwv[mm]', 'lwp[kg*m^-2]', 'iwp[kg*m^-2]', 'o3[DU]')


def ok(outfile, verbose=False):
    if not os.path.exists(outfile):
        if verbose:
            print(outfile, 'does not exist', file=sys.stderr)
        return False
    with open(outfile) as f:
        count = len(f.readlines())
        if count != expected_lines:
            if verbose:
                print(outfile, 'saw', count, 'lines, not good', file=sys.stderr)
            return False
    if verbose:
        print(outfile, 'exists and has the correct count')
    return True


table_line_string = '{:1s}{:>16s} {:>12s} {:>12s} {:>12s} {:>12s} {:>12s} {:>12s}'
table_line_floats = '{} {:12.4e} {:12.4e} {:12.4e} {:12.4e} {:12.4e} {:12.4e}'


def print_table_line(fields, f):
    print(table_line_string.format(*fields), file=f)


def gfs15_to_am10(lat, lon, alt, gfs_cycle, forecast_hour, wait=False, verbose=False, stats=None):
    grib_buffer = download_gfs(lat, lon, alt, gfs_cycle, forecast_hour, wait=wait, verbose=verbose, stats=stats)

    grib_problem = False
    # development hint: use delete=False to save all of these
    delete = False
    with tempfile.NamedTemporaryFile(mode='wb', prefix='temp-', suffix='.grb', delete=delete) as f:
        f.write(grib_buffer)
        f.flush()

        try:
            Pbase, z, T, o3_vmr, RH, cloud_lmr, cloud_imr, extra = grib2_to_am_layers(f.name, lat, lon, alt)
        except Exception as e:
            # example: RuntimeError: b'End of resource reached when reading message'
            # example: UserWarning: file temp.grb has multi-field messages, keys inside multi-field messages will not be indexed correctly
            grib_problem = str(e)
            print('problem reading grib:', grib_problem, file=sys.stderr)

    my_stdout = io.StringIO()

    if not grib_problem:
        with contextlib.redirect_stdout(my_stdout):
            try:
                print_am_header(gfs_cycle, forecast_hour, lat, lon, alt)
                print_am_layers(alt, Pbase, z, T, o3_vmr, RH, cloud_lmr, cloud_imr)
            except Exception as e:
                # example: ZeroDivisionError after a bunch of
                #   ECCODES INFO    :  grib_file_open: cannot open file foo.grb (No such file or directory)
                grib_problem = str(e)
                print('problem printing am', grib_problem, file=sys.stderr)

    if False:
        with tempfile.NamedTemporaryFile(mode='wb', prefix='layers-err-', suffix='.grb', dir='.', delete=False) as tfile:
            print('some problem turning the grib into layers, saving ', tfile.name, file=sys.stderr)
            tfile.write(grib_buffer)
            tfile.flush()
            fname = tfile.name[:-4]+'.info'
            with open(fname, 'w') as f:
                print(grib_problem, file=f)
                print('lat', lat, 'lon', lon, 'alt', alt, 'gfs_cycle', gfs_cycle, 'forecast_hour', forecast_hour, file=f)
        return None, None

    return my_stdout.getvalue(), extra


def print_final_output(gfs_timestamp, tau, Tb, pwv, lwp, iwp, o3, f, verbose=False):
    out = table_line_floats.format(gfs_timestamp, tau, Tb, pwv, lwp, iwp, o3)
    print(out, file=f)
    if verbose:
        print(out, file=sys.stderr)
        sys.stderr.flush()


def print_extra(fcast_pretty, extra, f2, verbose=False):
    if f2:
        extra['date'] = fcast_pretty
        f2.writerow(extra)


def compute_one_hour(site, gfs_cycle, forecast_hour, f, f2, wait=False, verbose=False, stats=None):
    if verbose:
        print(site['name'], 'fetching for hour', forecast_hour, file=sys.stderr)
    with record_latency('fetch gfs data'):
        layers_amc, extra = gfs15_to_am10(site['lat'], site['lon'], site['alt'], gfs_cycle, forecast_hour, wait=wait, verbose=verbose, stats=stats)
    if layers_amc is None:
        return  # no line emitted

    dt_forecast_hour = gfs_cycle + datetime.timedelta(hours=forecast_hour)
    fcast_pretty = dt_forecast_hour.strftime(GFS_TIMESTAMP)

    am_problem = False
    with record_latency('run am'):
        returncode, am_output, am_error = run_am(layers_amc)
    if returncode not in (0, 1):
        # am exits 1 for warnings: '! Warning: Water ice was encountered on a layer where models were'
        am_problem = 'saw returncode of {}'.format(returncode)

    if not am_problem:
        try:
            tau, Tb, pwv, lwp, iwp, o3 = summarize_am(am_output, am_error)
        except Exception as e:
            am_problem = str(e)

    if am_problem:
        with tempfile.NamedTemporaryFile(mode='w', prefix='am-problem-', dir='.', delete=False) as tfile:
            print('problem running am, saving input and output to', tfile.name, file=sys.stderr)
            # example: -(35) : The volume mixing ratio must be in the range 0 to 1.
            # ! Error: parse error.
            tfile.write('am_problem: {}\n'.format(am_problem))
            tfile.write('Input:\n\n')
            tfile.write(header_amc)
            tfile.write(layers_amc)
            tfile.write('\nOutput:\n\n')
            tfile.write(am_error)
            tfile.write(am_output)
            return  # no line emitted

    fcast_pretty = dt_forecast_hour.strftime(GFS_TIMESTAMP)
    print_final_output(fcast_pretty, tau, Tb, pwv, lwp, iwp, o3, f, verbose=verbose)
    print_extra(fcast_pretty, extra, f2, verbose=verbose)
    time.sleep(1)


def make_forecast_table(site, gfs_cycle, f, f2, wait=False, verbose=False, hours=-1, stats=None):
    print_table_line(table_header, f)
    for forecast_hour in range(0, 121):
        if forecast_hour >= hours:
            return
        compute_one_hour(site, gfs_cycle, forecast_hour, f, f2, wait=wait, verbose=verbose, stats=stats)
    for forecast_hour in range(123, 385, 3):
        if forecast_hour >= hours:
            return
        compute_one_hour(site, gfs_cycle, forecast_hour, f, f2, wait=wait, verbose=verbose, stats=stats)


def read_stations(filename):
    if filename is None:
        filename = os.path.split(__file__)[0] + '/data/stations.json'
    with open(filename, 'r') as f:
        stations = json.load(f)

    stations_dict = {}
    for s in stations:
        if 'vex' in s:
            stations_dict[s['vex']] = s
        elif 'name' in s:
            stations_dict[s['name']] = s
        else:
            raise ValueError('need vex or name')

    return stations_dict


def dump_stats(stats, log=None):
    headers = ('gfs_time', 'stations', 'start')
    out = ''
    for key in headers:
        out += '{}: {}\n'.format(key, stats[key])
    for key in sorted(stats.keys()):
        if key in headers:
            continue
        out += '  {}: {}\n'.format(key, stats[key])

    print(out, file=sys.stderr)
    if log:
        with open(log, 'a') as fd:
            print(out, file=fd)
