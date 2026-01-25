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
        'sep': r'\s+',
        'comment': '#',
        'names': 'date tau225 Tb pwv lwp iwp o3'.split(),
    }

    fname = expanduser('{}/{}/{}'.format(basedir, vex, gfs_cycle))
    if not exists(fname):
        return

    with open(fname) as f:
        data = pd.read_csv(f, **kwargs)
    if data.empty:
        return

    data['date'] = pd.to_datetime(data['date'], format='%Y%m%d_%H:%M:%S', utc=True)

    data = data.set_index('date').resample('1h').interpolate('linear').reset_index()

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
        'sep': r'\s+',
        'header': 0,
    }

    fname = expanduser('{}/{}/{}.extra'.format(basedir, vex, gfs_cycle))
    if not exists(fname):
        return

    with open(fname) as f:
        data = pd.read_csv(f, **kwargs)
        data['date'] = pd.to_datetime(data['date'], format='%Y%m%d_%H:%M:%S', utc=True)

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
    # added 2025
    'KVN_YS': 'Ky',
}


def read_eu(basedir='.'):
    kwargs = {
        'sep': r'\s+',
        'header': 0,
    }
    fname = expanduser(basedir) + '/tau225.txt'

    if not exists(fname):
        print('eu tau225.txt does not exist')
        return

    with open(fname) as f:
        try:
            data = pd.read_csv(f, **kwargs)
        except NotImplementedError as e:
            # this started happening when new columns were added
            print('eu read failure: '+repr(e))
            return
        except Exception as e:
            # catchall, just in case
            print('eu read failure: '+repr(e))
            return

    if data.empty:
        print('eu tau225.txt was empty')
        return

    # this is different because it's unixtime. pandas handles the trailing period.
    data['date'] = pd.to_datetime(data['time'], unit='s', utc=True)
    del data['time']

    deletes = {
        'DeBilt': '',
        'Thule': '',
        'AMT': '',
        'Meerkat': '',
    }

    data.drop(columns=deletes.keys(), errors='ignore', inplace=True)
    return data.rename(columns=eu_to_vex)
