#!/usr/bin/env python

import glob
import os.path
from collections import defaultdict

from jinja2 import Environment, FileSystemLoader, select_autoescape

from eht_met_forecast import read_stations


stations = read_stations(None)

env = Environment(
    loader=FileSystemLoader('./templates'),
    # loader = PackageLoader('olymap', 'templates')
    autoescape=select_autoescape(['html'])
)

dirs = glob.glob('eht-met-plots/2*')

force = True

for d in dirs:
    if os.path.exists(d+'/index.html') and not force:
        continue

    gfs_cycle = d.split('/')[-1]
    files = glob.glob(d+'/*')
    prefixes = {'forecast', 'lindy'}
    groups = defaultdict(list)

    for f in sorted(files):
        f = f.split('/')[-1]
        parts = f.split('_')
        if parts[0] in prefixes:
            groups[parts[1]].append(f)

    now = {}
    future = {}
    for s in sorted(groups.keys()):
        if len(s) != 2:
            future[s] = groups[s]
        else:
            now[s] = groups[s]

    stuff = {}
    stuff['title'] = '{} Plots'.format(gfs_cycle)
    stuff['year'] = gfs_cycle[:4]
    stuff['stations'] = stations

    template = env.get_template('index.html.template')
    with open(d + '/index.html', 'w') as f:
        f.write(template.render(stuff=stuff, now=now, future=future))
