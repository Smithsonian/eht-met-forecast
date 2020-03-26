import glob
import datetime
import pandas as pd
from os.path import expanduser


def read(vex, basedir='.'):
    files = glob.glob(expanduser('{}/{}/*'.format(basedir, vex)))
    if not files:
        raise ValueError('no files')

    utc = datetime.timezone.utc
    kwargs = {
        'delim_whitespace': True,
        'comment': '#',
        'names': 'datestr tau225 Tb pwv lwp iwp o3'.split(),
        'parse_dates': {'date': [0]},
        'keep_date_col': True,
        'date_parser': lambda x: datetime.datetime.strptime(x, '%Y%m%d_%H:%M:%S').replace(tzinfo=utc)
    }

    data = []
    for f in files:
        a = pd.read_csv(f, **kwargs)
        if a.empty:
            continue
        a['date0'] = a.iloc[0]['date']
        a['age'] = a['date'] - a['date0']
        data.append(a)

    gfs_cycle = max(files).split('/')[-1]

    return gfs_cycle, data
