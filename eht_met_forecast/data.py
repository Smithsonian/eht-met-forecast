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
    # don't be confused by pre2024 etc
    files = glob.glob(expanduser('{}/*/2*'.format(basedir)))
    if not files:
        raise ValueError('no files')

    gfs_cycles = set()
    for f in files:
        if '.extra' in f:
            continue
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

    data.set_index('date').resample('1H').interpolate('linear').reset_index()

    data['date0'] = data.iloc[0]['date']
    data['age'] = data['date'] - data['date0']
    return data


def read_accumulated(vex, gfs_cycle, basedir='.'):
    data = read_one(vex, gfs_cycle, basedir=basedir)

    if data is not None:
        partial_sums[vex].append(data)

    return partial_sums[vex]


def read_wind(vex, gfs_cycle, basedir='.'):
    utc = datetime.timezone.utc
    kwargs = {
        'delim_whitespace': True,
        'header': 0,
        'parse_dates': {'date_temp': [0]},
        'date_parser': lambda x: datetime.datetime.strptime(x, '%Y%m%d_%H:%M:%S').replace(tzinfo=utc)
    }

    fname = expanduser('{}/{}/{}.extra'.format(basedir, vex, gfs_cycle))
    if not exists(fname):
        return

    with open(fname) as f:
        data = pd.read_csv(f, **kwargs)
        data['date'] = data['date_temp']
        del data['date_temp']

    return data


eu_to_vex = {
    'ALMA': 'Aa',
    'APEX': 'Ax',
    'SMTO': 'Mg',
    'LMT': 'Lm',
    'SPT': 'Sz',
    'PICO': 'Pv',
    'JCMT': 'Mm',
    'KP': 'Kt',
    'GLT': 'Gl',
    'NOEMA': 'Nn',
    'SMA': 'Sw',
    # added April 10, 2021, not present in 2023
    #'IRAM_PV': 'Pv',
    #'SPTDUMMY': 'Sz',
    #'IRAM_PdB': 'Nn',
}


def read_eu(basedir='.'):
    kwargs = {
        'delim_whitespace': True,
        'header': 0,
        'parse_dates': {'date': [0]},
        'date_parser': lambda x: datetime.datetime.utcfromtimestamp(int(x.replace('.', ''))),
    }
    fname = expanduser(basedir) + '/tau225.txt'

    if not exists(fname):
        return

    with open(fname) as f:
        data = pd.read_csv(f, **kwargs)
    if data.empty:
        return

    deletes = {
        'DeBilt': '',
        'Thule': '',
        'AMT': '',
        'Meerkat': '',
    }

    data.drop(columns=deletes.keys(), errors='ignore', inplace=True)
    return data.rename(columns=eu_to_vex)
