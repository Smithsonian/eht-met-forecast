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
from .gfs import latest_gfs_cycle_time, download_gfs

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


def gfs15_to_am10(lat, lon, alt, gfs_cycle, forecast_hour, wait=False, verbose=False):
    grib_buffer = download_gfs(lat, lon, alt, gfs_cycle, forecast_hour, wait=wait, verbose=verbose)

    grib_problem = False
    with tempfile.NamedTemporaryFile(mode='wb', prefix='temp-', suffix='.grb') as f:
        f.write(grib_buffer)
        f.flush()
        try:
            Pbase, z, T, o3_vmr, RH, cloud_lmr, cloud_imr = grib2_to_am_layers(f.name, lat, lon, alt)
        except Exception as e:
            # example: RuntimeError: b'End of resource reached when reading message'
            # example: UserWarning: file temp.grb has multi-field messages, keys inside multi-field messages will not be indexed correctly
            grib_problem = str(e)

    if not grib_problem:
        my_stdout = io.StringIO()
        with contextlib.redirect_stdout(my_stdout):
            try:
                print_am_header(gfs_cycle, forecast_hour, lat, lon, alt)
                print_am_layers(alt, Pbase, z, T, o3_vmr, RH, cloud_lmr, cloud_imr)
            except Exception as e:
                # example: ZeroDivisionError after a bunch of
                #   ECCODES INFO    :  grib_file_open: cannot open file foo.grb (No such file or directory)
                grib_problem = str(e)

    if grib_problem:
        with tempfile.NamedTemporaryFile(mode='wb', prefix='layers-err-', suffix='.grb', dir='.', delete=False) as tfile:
            print('some problem turning the grib into layers, saving ', tfile.name, file=sys.stderr)
            tfile.write(grib_buffer)
            tfile.flush()
            fname = tfile.name[:-4]+'.info'
            with open(fname, 'w') as f:
                print(grib_problem, file=f)
                print('lat', lat, 'lon', lon, 'alt', alt, 'gfs_cycle', gfs_cycle, 'forecast_hour', forecast_hour, file=f)
        return

    return my_stdout.getvalue()


def print_final_output(gfs_timestamp, tau, Tb, pwv, lwp, iwp, o3, f):
    out = table_line_floats.format(gfs_timestamp, tau, Tb, pwv, lwp, iwp, o3)
    print(out, file=f)
    f.flush()
    print(out, file=sys.stderr)


def compute_one_hour(site, gfs_cycle, forecast_hour, f, wait=False, verbose=False):
    print('fetching for hour', forecast_hour, file=sys.stderr)
    with record_latency('fetch gfs data'):
        layers_amc = gfs15_to_am10(site['lat'], site['lon'], site['alt'], gfs_cycle, forecast_hour, wait=wait, verbose=verbose)
    if layers_amc is None:
        return  # no line emitted

    dt_forecast_hour = gfs_cycle + datetime.timedelta(hours=forecast_hour)
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

    print_final_output(dt_forecast_hour.strftime(GFS_TIMESTAMP), tau, Tb, pwv, lwp, iwp, o3, f)
    time.sleep(1)


def make_forecast_table(site, gfs_cycle, f, wait=False, verbose=False, one=False):
    print_table_line(table_header, f)
    for forecast_hour in range(0, 121):
        compute_one_hour(site, gfs_cycle, forecast_hour, f, wait=wait, verbose=verbose)
        if one:
            return
    for forecast_hour in range(123, 385, 3):
        compute_one_hour(site, gfs_cycle, forecast_hour, f, wait=wait, verbose=verbose)


def read_stations(filename):
    if filename is None:
        filename = os.path.split(__file__)[0] + '/data/stations.json'
    with open(filename, 'r') as f:
        return json.load(f)
