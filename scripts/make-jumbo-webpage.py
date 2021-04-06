#!/usr/bin/env python

import glob
import os.path
from collections import defaultdict
import sys
import argparse

from jinja2 import Environment, FileSystemLoader, select_autoescape

from eht_met_forecast import read_stations

# argparse
# --force,-f
# --emphasize

parser = argparse.ArgumentParser()
parser.add_argument('--stations', action='store', help='location of stations.json file')
parser.add_argument('--emphasize', action='store', nargs='+', help='colon-delimited list of stations to emphasize, i.e. this year\'s array')
parser.add_argument('--plotdir', action='store', default='./eht-met-plots', help='output directory for plots')
parser.add_argument('--force', action='store_true', help='make the plot even if the output file already exists')

args = parser.parse_args()
plotdir = os.path.expanduser(args.plotdir)

emphasize = set(station for station in args.emphasize if ':' not in station)
[emphasize.add(s) for station in args.emphasize if ':' in station for s in station.split(':')]
if '00' not in emphasize:
    emphasize.add('00')

stations = read_stations(args.stations)
stations['00'] = {'name': 'Current stations'}
stations['01'] = {'name': 'Future stations'}

for e in emphasize:
    if e not in stations and e != '00':
        raise ValueError('emphasized station {} is not known'.format(e))

env = Environment(
    # XXX make templates be relative to __file__?
    loader=FileSystemLoader('./templates'),
    autoescape=select_autoescape(['html'])
)

# XXX
dirs = glob.glob(args.plotdir + '/2*')

for d in dirs:
    if os.path.exists(d+'/index.html') and not args.force:
        continue

    gfs_cycle = d.split('/')[-1]
    files = glob.glob(d+'/*')
    prefixes = {'forecast', 'lindy'}
    groups = defaultdict(list)

    for f in sorted(files):
        if f.endswith('.csv'):
            continue
        f = f.split('/')[-1]
        parts = f.split('_')
        if parts[0] in prefixes:
            groups[parts[1]].append(f)

    now = {}
    future = {}

    for s in sorted(groups.keys()):
        if emphasize:
            if s in emphasize:
                now[s] = groups[s]
            else:
                future[s] = groups[s]
        else:
            if len(s) != 2:
                future[s] = groups[s]
            else:
                now[s] = groups[s]

    stuff = {}
    stuff['title'] = '{} Plots'.format(gfs_cycle)
    stuff['year'] = gfs_cycle[:4]
    stuff['stations'] = stations

    # XXX need to read trackrank.csv to compute these
    stuff['trackmin'] = 0.
    stuff['trackmax'] = 1.

    template = env.get_template('index.html.template')
    with open(d + '/index.html', 'w') as f:
        try:
            f.write(template.render(stuff=stuff, now=now, future=future))
        except Exception as e:
            print('got exception {} processing {}, skipping'.format(str(e), d), file=sys.stderr)
