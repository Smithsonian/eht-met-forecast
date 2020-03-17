import sys
import datetime
import os
from argparse import ArgumentParser

from .constants import GFS_TIMESTAMP
from .timer_utils import dump_latency_histograms
from .gfs import latest_gfs_cycle_time
from .core import read_stations, ok, make_forecast_table


def interpret_args(args, station_dict):
    print_vexes = False
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
                    print_vexes = True
    if print_vexes:
        print('valid vexes are:', file=sys.stderr)
        for k, v in station_dict.items():
            print(' ', k, v['name'], file=sys.stderr)

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

    return stations, cycles


def main(args=None):
    parser = ArgumentParser(description='eht-met-forecast command line tool')
    parser.add_argument('--vex', action='append', help='station(s) to fetch')
    parser.add_argument('--stations', action='store', help='station configuration file (default: builtin list)')
    parser.add_argument('--backfill', action='store', default=0, type=int, help='hours to backfill')
    parser.add_argument('--cycle', action='store', help='gfs cycle to fetch (e.g. 2020031200)')
    parser.add_argument('--dir', action='store', default='eht-met-forecast-output',
                        help='directory to store output (default: eht-met-forecast-output')
    parser.add_argument('--wait', action='store_true', help='Retry forever on 404, awaiting data availability')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Show what would be done. Implies -v')
    parser.add_argument('--one', action='store_true', help='Just do one hour. Used for testing')
    parser.add_argument('--stdout', action='store_true', help='Print output to stdout instead of a file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Print more information')
    args = parser.parse_args(args=args)

    verbose = args.verbose
    if args.dry_run:
        verbose = True

    station_locations = read_stations(args.stations)
    station_dict = dict([(v['vex'], v) for v in station_locations])

    stations, cycles = interpret_args(args, station_dict)

    if not stations:
        print('no valid stations to fetch', file=sys.stderr)
        exit(1)

    for vex in stations:
        station = station_dict[vex]
        for gfs_cycle in cycles:
            print('checking station', vex, 'cycle', gfs_cycle.strftime(GFS_TIMESTAMP), file=sys.stderr)
            outdir = '{}/{}'.format(args.dir, vex)
            outfile = '{}/{}'.format(outdir, gfs_cycle.strftime(GFS_TIMESTAMP))
            if ok(outfile, verbose=verbose):
                if verbose:
                    print('  outfile {} seems ok, not re-fetching'.format(outfile), file=sys.stderr)
                continue
            if verbose or args.dry_run:
                print('  processing', vex, outfile, file=sys.stderr)
                if args.dry_run:
                    continue
            os.makedirs(outdir, exist_ok=True)
            if args.stdout:
                f = sys.stdout
            else:
                f = open(outfile, 'w')
            make_forecast_table(station, gfs_cycle, f, wait=args.wait, verbose=args.verbose, one=args.one)
            if not args.stdout:
                f.close()
    dump_latency_histograms()
