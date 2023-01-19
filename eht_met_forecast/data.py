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


def write_gfs_eu_style(allest, stations, gfs_cycle, basedir='.', verbose=False):

    dfs = []
    vex_to_eu = dict([(v, k) for k, v in eu_to_vex.items()])

    if verbose:
        print('write gfs eu style, cycle', gfs_cycle)
    first = True
    for site in stations:
        if site not in vex_to_eu:
            continue
        if verbose:
            print(' ', site)
        est = allest[site][gfs_cycle]
        est_cols = set(est.columns)
        est_cols.discard('date')
        est_cols.discard('est_mean')
        # XXX convert date column to a float64 unixtime
        df = est.drop(columns=list(est_cols))
        df.rename(columns={'est_mean': site}, inplace=True)
        if not first:
            df = df.drop(columns='date')
        else:
            first = False
            df['date'] = df.date.values.astype(float) // 1000000000
        dfs.append(df)
    df = pd.concat(dfs, axis=1)

    # rename sites to their preferred vlbimon names
    vex_to_eu = dict([(v, k) for k, v in eu_to_vex.items()])
    df.rename(columns=vex_to_eu, inplace=True)

    fname = expanduser(basedir) + '/' + gfs_cycle + '/tau225_gfs.txt'
    columns = df.columns
    with open(fname, 'w') as fd:
        # header: 12-character fields, left justified
        headerf = '{:12s}' * len(columns)
        header = headerf.format('time', *vex_to_eu.values())
        print(header, file=fd)

        rowf = '{:.11f}'
        for row in df.itertuples():
            print('{:.0f}.'.format(row[1]), end=' ', file=fd)
            print(' '.join(rowf.format(v) for v in list(row[2:])), file=fd)
