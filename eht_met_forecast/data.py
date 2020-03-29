import glob
import datetime
from os.path import expanduser, exists
from collections import defaultdict

import pandas as pd


def gfs_cycle_to_dt(gfs_cycle):
    utc = datetime.timezone.utc
    return datetime.datetime.strptime(gfs_cycle, '%Y%m%d_%H:%M:%S').replace(tzinfo=utc)


def dt_to_gfs_cycle(gfs_cycle_dt):
    return gfs_cycle_dt.strftime('%Y%m%d_%H:%M:%S')


def get_gfs_cycles(basedir='.'):
    files = glob.glob(expanduser('{}/*/*'.format(basedir)))
    if not files:
        raise ValueError('no files')

    gfs_cycles = set()
    for f in files:
        parts = f.split('/')
        gfs_cycles.add(parts[-1])
    return sorted(list(gfs_cycles))


partial_sums = defaultdict(list)


def read_one(vex, gfs_cycle, basedir='.'):
    utc = datetime.timezone.utc
    kwargs = {
        'delim_whitespace': True,
        'comment': '#',
        'names': 'datestr tau225 Tb pwv lwp iwp o3'.split(),
        'parse_dates': {'date': [0]},
        'keep_date_col': True,
        'date_parser': lambda x: datetime.datetime.strptime(x, '%Y%m%d_%H:%M:%S').replace(tzinfo=utc)
    }

    fname = expanduser('{}/{}/{}'.format(basedir, vex, gfs_cycle))
    if not exists(fname):
        return

    with open(fname) as f:
        data = pd.read_csv(f, **kwargs)
        if data.empty:
            return
        data['date0'] = data.iloc[0]['date']
        data['age'] = data['date'] - data['date0']
        return data


def read_accumulated(vex, gfs_cycle, basedir='.'):
    data = read_one(vex, gfs_cycle, basedir=basedir)

    if data is not None:
        partial_sums[vex].append(data)

    return partial_sums[vex]
