#!/usr/bin/env python

import glob
import os.path
from collections import defaultdict
import sys
import argparse
import traceback

from jinja2 import Environment, FileSystemLoader, select_autoescape

from eht_met_forecast import read_stations
from eht_met_forecast.gfs import latest_gfs_cycle_time
from eht_met_forecast.data import gfs_cycle_to_dt
from eht_met_forecast.constants import GFS_TIMESTAMP

parser = argparse.ArgumentParser()
parser.add_argument('--stations', action='store', help='location of stations.json file')
parser.add_argument('--emphasize', action='store', nargs='+', help='colon-delimited list of stations to emphasize, i.e. this year\'s array')
parser.add_argument('--plotdir', action='store', default='./eht-met-plots', help='output directory for plots')
parser.add_argument('--force', action='store_true', help='generate index.html even if it already exists')

args = parser.parse_args()
plotdir = os.path.expanduser(args.plotdir)

emphasize = set(station for station in args.emphasize if ':' not in station)
[emphasize.add(s) for station in args.emphasize if ':' in station for s in station.split(':')]

not_stations = {
    '00': 'Current stations GFS weather (estimators, scroll down for full details per station)',
    '00e': 'Current stations EU weather',
    '00w': 'Current stations GFS 10m wind',
    '00wg': 'Current stations GFS wind gusts > 10 m/s',
    '00p': 'Current stations GFS precip chance',
    '01': 'Future stations',
}

for ns in not_stations.keys():
    if ns == '01':
        continue
    if ns not in emphasize:
        emphasize.add(ns)

stations = read_stations(args.stations)
for ns, name in not_stations.items():
    stations[ns] = {'name': name}

for e in emphasize:
    if e not in stations and e not in not_stations:
        raise ValueError('emphasized station {} is not known'.format(e))

env = Environment(
    # XXX make templates be relative to __file__?
    loader=FileSystemLoader('./templates'),
    autoescape=select_autoescape(['html'])
)

dirs = glob.glob(args.plotdir + '/202[456789]*')

symlinks = set(['lindy_{}.png'.format(ns) for ns in not_stations.keys()])

for d in dirs:
    if os.path.exists(d+'/index.html') and not args.force:
        continue

    gfs_cycle = d.split('/')[-1]
    files = glob.glob(d+'/*')
    prefixes = {'forecast', 'lindy'}
    groups = defaultdict(list)

    t = gfs_cycle_to_dt(gfs_cycle).timestamp()
    previous = latest_gfs_cycle_time(now=t, lag=6).strftime(GFS_TIMESTAMP)  # hours
    current = gfs_cycle
    next = latest_gfs_cycle_time(now=t, lag=-6).strftime(GFS_TIMESTAMP)  # hours

    for f in sorted(files):
        if f.endswith('.csv'):
            continue
        f = f.split('/')[-1]
        if f in symlinks:
            continue
        parts = f.split('_')
        if parts[0] in prefixes:
            groups[parts[1]].append(f)

    now = {}
    future = {}

    for s in sorted(groups.keys()):
        if s not in stations:
            # renamed stations end up here
            print('I found files for station {} but it is not in stations'.format(s))
            continue
        if s in emphasize:
            now[s] = groups[s]
        else:
            future[s] = groups[s]

    stuff = {
        'gfs_cycle': gfs_cycle,
        'title': '{} Plots'.format(gfs_cycle),
        'year': gfs_cycle[:4],
        'stations': stations,
        'trackmin': 0.55,  # used to color the trackrank csv
        'trackmax': 0.75,
        'previous': previous,
        'current': current,
        'next': next,
    }

    template = env.get_template('index.html.template')
    with open(d + '/index.html', 'w') as f:
        try:
            f.write(template.render(stuff=stuff, now=now, future=future))
        except Exception as e:
            print('got exception {} processing {}, skipping'.format(str(e), d), file=sys.stderr)
            print(traceback.format_exc())
