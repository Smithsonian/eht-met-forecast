#!/usr/bin/env python
import argparse
import os
import os.path
import sys
from collections import defaultdict
import datetime
import hashlib
import traceback
import time

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.offsetbox import AnchoredText
import numpy as np
from scipy.interpolate import interp1d
from astropy import units as u
from astropy.coordinates import SkyCoord, EarthLocation, AltAz

import eht_met_forecast.data
from eht_met_forecast.constants import GFS_TIMESTAMP_FULL
from eht_met_forecast import read_stations
import vex as vvex

schedule_start = '0 hours'  # midnight
schedule_end = '12 hours'

before_start = '1 day'
after_end = '1 day'
close_sites = {'Ax': 'Aa', 'Mm': 'Sw'}


def get_all_work(datadir, plotdir, gfs_cycles, stations, force=False, verbose=0):
    ret = {}
    for gfs_cycle in gfs_cycles:
        me = defaultdict(list)
        for vex in stations:
            inname = '{}/{}/{}'.format(datadir, vex, gfs_cycle)
            if not os.path.exists(inname):
                continue
            outname = '{}/{}/lindy_{}_{}.png'.format(plotdir, gfs_cycle, vex, gfs_cycle)
            me['lindy'].append(outname)

        plots = ('00', '00e', '00w', '00wg', '00p', '01')
        for p in plots:
            outname = '{}/{}/lindy_{}_{}.png'.format(plotdir, gfs_cycle, p, gfs_cycle)
            me[p].append(outname)

        csvs = ('forecast', 'trackrank')
        for csv in csvs:
            outname = '{}/{}/{}.csv'.format(plotdir, gfs_cycle, csv)
            me[csv].append(outname)

        outname = '{}/{}/tau225_gfs.txt'.format(plotdir, gfs_cycle)
        me['tau225_gfs'].append(outname)

        if verbose:
            print('gfs_cycle', gfs_cycle, 'file groups to possibly generate:', me.keys())

        ret[gfs_cycle] = me

    if force:
        return ret

    for gfs_cycle in list(ret.keys()):  # list() because I'm deleting
        for key in list(ret[gfs_cycle].keys()):  # list() because I'm deleting
            for f in ret[gfs_cycle][key]:
                needed = []
                if not os.path.exists(f):
                    needed.append(f)
            if needed:
                ret[gfs_cycle][key] = needed
            else:
                del ret[gfs_cycle][key]
        if len(ret[gfs_cycle]) == 0:
            del ret[gfs_cycle]

        if verbose and gfs_cycle in ret:
            print('gfs_cycle', gfs_cycle, 'file groups to actually generate:', ret[gfs_cycle].keys())

    return ret


# weighted geometric average and fractional error estimator
def wavg(df, xcol='tau225', scol='sigma', col="est_mean est_err est_chisq est_n".split()):
    (x, s) = (np.log(df[xcol]), df[scol]) # get original data and unscaled error columns
    n = len(x)
    ssq = s**2  # simga squared (save value)
    w = 1 / ssq # weight to use for averages (1/ssq is optimal if independent Gaussian noise)
    wsq = w**2  # weight squared (save value)
    xsum = np.sum(w*x)       # weighted sum
    ssum = np.sum(wsq * ssq) # total variance of weighted sum (this is "N" if w = 1/sigma)
    wsum = np.sum(w)         # common divisor
    xavg = xsum / wsum       # weighted mean
    tchisq = np.sum(wsq * (x-xavg)**2) # total weighted chisq (regular total chisq if w = 1/sigma)
    rchisq = tchisq / ssum # reduced chisq (we expect this to be "1" if original sigmas are correct)
    ferr = np.min(s) * np.sqrt(rchisq) # scale minimum error with reduced chisq (just a hack)
    return_cols = (np.exp(xavg), np.exp(ferr), rchisq, n)
    from collections import OrderedDict
    return pd.Series(OrderedDict(zip(col, return_cols[:len(col)])))


def wide(w=8, h=3):
    plt.setp(plt.gcf(), figwidth=w, figheight=h)
    plt.tight_layout()


# configuration parameters
tfloor = 6. # hours from start for which to assume fixed model error
tpow = 4. # model error goes as time to this power: sigma = (floor + age)**tpow


def do_plot(station, gfs_cycle, allest, allint, start, end, datadir, plotdir, force=False):
    site = station.get('vex') or station['name']
    outname = '{}/{}/lindy_{}_{}.png'.format(plotdir, gfs_cycle, site, gfs_cycle)

    data = eht_met_forecast.data.read_accumulated(site, gfs_cycle, basedir=datadir)
    if not data:
        with open(outname, 'w'):
            # touch the output file so we skip it next time
            pass
        return

    alldata = pd.concat(data, ignore_index=True).sort_values(['date', 'age'])
    alldata['sigma'] = (tfloor + alldata['age'].dt.total_seconds()/3600.)**tpow
    latest = alldata.groupby('date').first().reset_index()  # most recent forecast
    date0 = np.max(latest['date0'])

    gfs_cycle_dt = eht_met_forecast.data.gfs_cycle_to_dt(gfs_cycle)
    if date0 != gfs_cycle_dt:
        date0_str = eht_met_forecast.data.dt_to_gfs_cycle(date0)
        raise ValueError('gfs_cycle {} and first date in csv {} disagree'.format(gfs_cycle, date0_str))

    # ensemble estimator with errors
    est = alldata.groupby('date').apply(wavg).reset_index()
    est['site'] = site
    allest[site][gfs_cycle] = est
    allint[site][gfs_cycle] = interp1d(est.date.values.astype(int),
                                       est.est_mean.values, bounds_error=False)

    os.makedirs(os.path.dirname(outname), exist_ok=True)
    if not force and os.path.exists(outname):
        return

    # solid black line for the latest forecast
    label = station['name'] + ' ' + str(date0)
    plt.plot(latest.date.values, latest.tau225, lw=1, label=label, color='black')
    # vertial line at the most recent forecast run time
    plt.axvline(date0, color='black', ls='--')

    # faint black lines for all old forecasts
    for df in data:
        if df.iloc[0].date0 == date0:
            continue
        plt.plot(df.date.values, df.tau225.values, color='black', alpha=1./len(data))

    # ensemble estimator, medium ?blue? band
    # JAGGED 1 hour/3 hour
    plt.fill_between(est.date.values, est.est_mean.values/est.est_err,
                     est.est_mean.values*est.est_err, alpha=0.25)

    days = pd.date_range(start=start, end=end, freq='D')
    for d in days:
        # night markings, light blue fill
        plt.axvspan(d+pd.Timedelta(schedule_start), d+pd.Timedelta(schedule_end), color='C0', alpha=0.15, zorder=-10)
    # ensemble mean dark ?blue? line
    # JAGGED 1 hour/3 hour
    plt.plot(est.date.values, est.est_mean, label=station['name'] + ' ensemble')

    # EU forecast
    eu_data = eht_met_forecast.data.read_eu()  # ./tau255.txt
    if eu_data is not None and site in eu_data:
        # coming through orange?
        plt.plot(eu_data.date.values, eu_data[site], ls='--', label=station['name'] + ' EU')

    # formatting
    plt.ylim(0, 1.0)
    plt.yticks(np.arange(0, 1.0, .1))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator())
    #plt.gca().fmt_xdata = mdates.DateFormatter('%Y %a')  # this does nothing?
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %d\n%a'))  # this does something
    #plt.gcf().autofmt_xdate()  # this makes the labels be angled, even if they are narrow
    plt.autoscale(enable=True, axis='x', tight=True)
    plt.grid(alpha=0.25)
    plt.legend(loc='upper right')
    if site != station['name']:
        label = site + ' ' + station['name']
    else:
        label = site
    plt.gca().add_artist(AnchoredText(label, loc=2))
    plt.xlabel('UT date')
    plt.ylabel('tau225')
    plt.xlim(days[0]-pd.Timedelta(before_start), days[-1]+pd.Timedelta(after_end))

    wide(14, 5)
    plt.savefig(outname, dpi=150)
    plt.close()


def do_forecast_csv(gfs_cycle, allest, start, end, plotdir, emphasize=None, force=False):
    outname = '{}/{}/forecast.csv'.format(plotdir, gfs_cycle)
    os.makedirs(os.path.dirname(outname), exist_ok=True)
    if not force and os.path.exists(outname):
        return

    start_doy = start.dayofyear
    end_doy = end.dayofyear
    if end_doy < start_doy:
        raise ValueError('this routine breaks if it straddles the end of the year')

    the_data = [allest[site][gfs_cycle]
                for site in allest if gfs_cycle in allest[site] and (not emphasize or site in emphasize)]
    if not the_data:
        return
    print(outname)
    data = pd.concat(the_data, ignore_index=True)
    data['doy'] = data.date.dt.dayofyear

    nights = data[(data.date.dt.hour >= 0) & (data.date.dt.hour < 12) & (data.doy >= start_doy) & (data.doy <= end_doy) & (data.date.dt.year >= start.year)]
    stats = nights.groupby(['site', 'doy']).median()

    df = stats.pivot_table(index='site', columns='doy', values='est_mean')
    df.to_csv(outname)

    outname = outname.replace('forecast.csv', 'forecast_future.csv')
    the_data = [allest[site][gfs_cycle]
                for site in allest if gfs_cycle in allest[site] and (emphasize and site not in emphasize)]
    if not the_data:
        return
    print(outname)
    data = pd.concat(the_data, ignore_index=True)
    data['doy'] = data.date.dt.dayofyear

    nights = data[(data.date.dt.hour >= 0) & (data.date.dt.hour < 12) & (data.doy >= start_doy) & (data.doy <= end_doy) & (data.date.dt.year >= start.year)]
    stats = nights.groupby(['site', 'doy']).median()

    df = stats.pivot_table(index='site', columns='doy', values='est_mean')
    df.to_csv(outname)


def do_trackrank_csv(gfs_cycle, allint, start, end, vexes, plotdir, include=None, force=False):
    if not vexes:
        return
    outname = '{}/{}/trackrank.csv'.format(plotdir, gfs_cycle)
    os.makedirs(os.path.dirname(outname), exist_ok=True)
    if not force and os.path.exists(outname):
        return
    if not vexes:
        # when we aren't observing, the vexes are optional
        # create empty output
        with open(outname, mode='w', encoding='utf8') as fd:
            pass

    fmt_in = '%Yy%jd%Hh%Mm%Ss'
    # ['4524000.43000 m', '468042.14000 m', '4460309.76000 m']

    def xyz2loc(xyz):
        xyz = [float(b[0])*u.Unit(b[1]) for b in (c.split() for c in xyz)]
        return EarthLocation.from_geocentric(*xyz)

    trackrank = dict()
    Dns = 86400000000000  # 1 day in ns
    daysut = pd.date_range(start=start, end=end, freq='D')
    daysdoy = [d.dayofyear for d in daysut]
    days = np.array([d.value for d in daysut])

    count_345 = 0
    for vex in vexes:
        track = os.path.splitext(os.path.basename(vex))[0]
        a = vvex.parse(open(vex).read())
        is345 = '345 GHz' in list(a['EXPER'].values())[0]['exper_description']
        if is345:
            count_345 += 1
        station_loc = dict((b['site_ID'], xyz2loc(b['site_position']))
                           for b in a['SITE'].values())
        source_loc = dict((b, SkyCoord(c['ra'], c['dec'], equinox=c['ref_coord_frame']))
                          for (b, c) in a['SOURCE'].items())
        score = np.zeros(len(days))
        total = np.zeros(len(days))

        for b in a['SCHED'].values(): # does not necessarily loop in order!
            time = pd.Timestamp(datetime.datetime.strptime(b['start'], fmt_in))
            dtimes = days + np.mod(time.value + Dns//4, Dns) - Dns//4
            try:
                stations = set(c[0].replace('Ax', 'Aa').replace('Mm', 'Sw') for c in b['station'])
            except IndexError:
                # when there is only 1 station in a scan, the data structure is just a list instead of a list of lists
                stations = {b['station'][0].replace('Ax', 'Aa').replace('Mm', 'Sw')}
            try:
                taus = np.array([allint[s][gfs_cycle](dtimes) for s in stations])
            except KeyError:
                print('key error')
                print('gfs_cycle', gfs_cycle, 'missing station:', [s for s in stations if gfs_cycle not in allint[s]])
                print('aborting the entire trackrank computation')
                # note that we could choose to compute trackrank minus the missing station
                # need to adjust a lot of things
                return

            if is345:
                taus = 0.05 + 2.5*taus # scale up tau225 to 345 GHz
            alts = np.array([source_loc[b['source']].transform_to(
                AltAz(obstime=time, location=station_loc[s])).alt.value for s in stations])
            n = len(taus)
            am = 1./np.sin(alts*np.pi/180.)
            score += (n-1)*np.sum(np.exp(-am[:,None] * taus), axis=0)  # talking with Lindy about: / len(dtimes)
            total += (n-1)*n
        trackrank[track] = score/total
    df = pd.DataFrame.from_dict(trackrank, orient='index', columns=daysdoy).sort_index()
    df.to_csv(outname)

    if count_345 != 1:
        #raise ValueError('expected to see exactly one 345 ghz track')
        print('expected to see exactly one 345 ghz track', file=sys.stderr)


def do_00_plot(gfs_cycle, allest, start, end, plotdir, stations, force=False, include=None, exclude=None, name='00', datadir='.'):
    outname = '{}/{}/lindy_{}_{}.png'.format(plotdir, gfs_cycle, name, gfs_cycle)
    os.makedirs(os.path.dirname(outname), exist_ok=True)
    if not force and os.path.exists(outname):
        return

    date0 = eht_met_forecast.data.gfs_cycle_to_dt(gfs_cycle)

    inverted_close_sites = {v: k for k, v in close_sites.items()}

    eu_data = None
    if allest is None:
        if name in {'00w', '00wg', '00p'}:
            wind_data = {}
            for site in stations:
                wind_data[site] = eht_met_forecast.data.read_wind(site, gfs_cycle, basedir=datadir)
        elif name == '00e':
            # the EU download happens rougly at the same time as this plot, so there's a race
            try:
                eu_data = eht_met_forecast.data.read_eu()  # ./tau225.txt
                t = os.stat('./tau225.txt').st_mtime  # XXX
            except FileNotFoundError:
                time.sleep(10)
                try:
                    eu_data = eht_met_forecast.data.read_eu()  # ./tau225.txt
                    t = os.stat('./tau225.txt').st_mtime  # XXX
                except FileNotFoundError:
                    return

            t = datetime.datetime.fromtimestamp(t, tz=datetime.timezone.utc)
            eu_download_time = t.strftime(GFS_TIMESTAMP_FULL)
        else:
            raise ValueError('00_plot does not know how to make '+name)

    some = False
    actual_sites = set()
    for site in sorted(stations.keys()):
        if exclude and site in exclude:
            continue
        if include and site not in include:
            continue
        if allest and gfs_cycle not in allest[site]:
            continue
        actual_sites.add(site)

    for site in sorted(actual_sites):
        if site in close_sites and close_sites[site] in actual_sites:
            continue

        # expand site names to have all possible aliases
        sname = stations[site]['name']
        label = site
        if site != sname:
            label += ' ' + sname
        if site in inverted_close_sites:
            other_site = inverted_close_sites[site]
            if other_site in actual_sites:
                label += ' ' + other_site
                other_name = stations[other_site]['name']
                if other_site != other_name:
                    label += ' ' + other_name

        # XXX consider moving this list outside the script?
        # used to pick line style/width
        hz345 = {'Aa', 'Ax', 'Gl', 'Mg', 'Mm', 'Pv', 'Sw'}

        # pick line styles and line widths for each station, keeping them consistent
        ls_list = ['dashed', 'dashdot']  # , 'solid', 'dotted']
        if site not in hz345:
            ls = 'solid'
        else:
            i = int(hashlib.md5(site.encode('utf8')).hexdigest()[:8], 16) % len(ls_list)
            ls = ls_list[i]

        if allest:  # GFS tau
            est = allest[site][gfs_cycle]
            lw = 1.0
            if site in hz345:
                lw = 2.0  # Remo request to really emphasize 345
                # increasing the width also increases the length, so dash dot looks like solid at lw=3.0
            plt.plot(est.date.values, est.est_mean, label=label, alpha=0.75, lw=lw, ls=ls)
            some = True
        elif name == '00w':
            if wind_data is not None and site in wind_data:
                wd = wind_data[site]
                if wd is not None and '10m_wind' in wd:
                    plt.plot(wd.date.values, wd['10m_wind'], ls=ls, label=label + ' 10m wind')
                    some = True
        elif name == '00wg':
            if wind_data is not None and site in wind_data:
                wd = wind_data[site]
                if wd is not None and 'wgust' in wd:
                    wd['wgust'].mask(wd['wgust'] < 10., np.NAN, inplace=True)
                    # always do the plot so that the colors/styles are consistent with the wind speed
                    label = label + ' wind gust'
                    if wd['wgust'].count() == 0:
                        label = None  # but disappear the label if empty
                    plt.plot(wd.date.values, wd['wgust'], ls=ls, label=label)
                    some = True
        elif name == '00p':
            if wind_data is not None and site in wind_data:
                wd = wind_data[site]
                if wd is not None:
                    sump = wd['csnow']
                    for col in ('cicep', 'cfrzr', 'crain'):
                        sump += wd[col]
                    plt.plot(wd.date.values, sump, ls=ls, label=label + ' precip')
                    some = True
        elif name == '00e':
            if eu_data is not None:
                if site in eu_data:
                    plt.plot(eu_data.date.values, eu_data[site], ls=ls, label=label + ' EU')
                    some = True
                else:
                    # if site is not in eu_data, we should still plot something and then disappear the label
                    # to keep the station colors the same
                    somesite = eu_data.columns[1]  # I think [0] is 'date' ?
                    something = eu_data[somesite].copy(deep=True)
                    something[:] = np.NAN
                    plt.plot(eu_data.date.values, something, ls=ls, label=None)
                    some = True
        else:
            raise ValueError('00_plot does not know how to make '+name)

    if not some:
        plt.close()
        return

    # vertical line at the forcast time
    # but not for EU, because we don't know when the forecast was run
    if allest or name in {'00w', '00wg', '00p'}:
        plt.axvline(date0, color='black', ls='--')

    days = pd.date_range(start=start, end=end, freq='D')
    for d in days:
        # night markings, light grey fill
        plt.axvspan(d+pd.Timedelta(schedule_start), d+pd.Timedelta(schedule_end), color='black', alpha=0.05, zorder=-10)

    # formatting
    if name == '00w':
        plt.ylim(0, 40.0)  # 40 meters/sec ~ 90 mph
    elif name == '00wg':
        plt.ylim(0, 40.0)  # 40 meters/sec ~ 90 mph
    elif name == '00p':
        plt.ylim(0, 1.0)  # precip %
    else:
        plt.ylim(0, 0.5)  # tau plot
        plt.yticks(np.arange(0, 0.5, .1))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator())
    #plt.gca().fmt_xdata = mdates.DateFormatter('%Y %a')  # this does nothign?
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %d\n%a'))  # this does something
    #plt.gcf().autofmt_xdate()  # this makes the labels be angled, even if they are narrow
    plt.autoscale(enable=True, axis='x', tight=True)
    plt.grid(alpha=0.25)
    plt.legend(loc='upper right')

    if allest:
        label = 'GFS ' + gfs_cycle
    elif name == '00w':
        label = 'GFS wind ' + gfs_cycle
    elif name == '00wg':
        label = 'GFS wind gust ' + gfs_cycle
    elif name == '00p':
        label = 'GFS precip ' + gfs_cycle
    elif name == '00e':
        label = 'EU downloaded ' + eu_download_time
    else:
        raise ValueError('00_plot does not know how to make '+name)

    plt.gca().add_artist(AnchoredText(label, loc=2))  # upper left

    plt.xlabel('UT date')
    if name in {'00w', '00wg'}:
        plt.ylabel('meters/sec')
    elif name in {'00p'}:
        plt.ylabel('chance')
    else:
        plt.ylabel('tau225')  # GFS and EU

    plt.xlim(days[0]-pd.Timedelta(before_start), days[-1]+pd.Timedelta(after_end))
    wide(14, 5)
    plt.savefig(outname, dpi=150)
    plt.close()


def get_dates(args):
    def get_parts(s):
        return [int(part) for part in s.split(':')]

    def interpret_date(s):
        if ' ' not in s:
            return pd.Timestamp(*get_parts(s))
        else:
            # when not observing, we pass in start "0 days" end "14 days"
            midnight = pd.Timestamp(pd.Timestamp('today').date())
            return midnight + pd.Timedelta(s)

    start = interpret_date(args.start)
    end = interpret_date(args.end)
    return start, end


def write_gfs_eu_style(allest, stations, gfs_cycle, plotdir='.', force=False, verbose=0):
    outname = '{}/{}/tau225_gfs.txt'.format(os.path.expanduser(plotdir), gfs_cycle)
    if not force and os.path.exists(outname):
        return

    dfs = []
    vex_to_eu = dict([(v, k) for k, v in eht_met_forecast.data.eu_to_vex.items()])

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
    vex_to_eu = dict([(v, k) for k, v in eht_met_forecast.data.eu_to_vex.items()])
    df.rename(columns=vex_to_eu, inplace=True)

    columns = df.columns
    with open(outname, 'w') as fd:
        # header: 12-character fields, left justified
        headerf = '{:12s}' * len(columns)
        header = headerf.format('time', *vex_to_eu.values())
        print(header, file=fd)

        rowf = '{:.11f}'
        for row in df.itertuples():
            print('{:.0f}.'.format(row[1]), end=' ', file=fd)
            print(' '.join(rowf.format(v) for v in list(row[2:])), file=fd)


# if columns are renamed this can crash, so let's call it first thing to see if it crashes
eht_met_forecast.data.read_eu()  # ./tau255.txt

parser = argparse.ArgumentParser()
parser.add_argument('--stations', action='store', help='location of stations.json file')
parser.add_argument('--vex', action='store', nargs='+', help='list of vex files')
parser.add_argument('--emphasize', action='store', nargs='+', help='colon-delimited list of stations to emphasize, i.e. this year\'s array')
parser.add_argument('--datadir', action='store', default='~/github/eht-met-data', help='data directory')
parser.add_argument('--plotdir', action='store', default='./eht-met-plots', help='output directory for plots')
parser.add_argument('--force', action='store_true', help='make the plot even if the output file already exists')
parser.add_argument('--start', action='store', help='start date of nightly labels, YYYY:MM:DD')
parser.add_argument('--end', action='store', help='end date of nightly labels, YYYY:MM:DD')
parser.add_argument('--verbose', '-v', action='count', help='more talking')

args = parser.parse_args()
datadir = os.path.expanduser(args.datadir)
plotdir = os.path.expanduser(args.plotdir)
verbose = args.verbose

emphasize = set(station for station in args.emphasize if ':' not in station)
[emphasize.add(s) for station in args.emphasize if ':' in station for s in station.split(':')]

stations = read_stations(args.stations)

for e in emphasize:
    if e not in stations:
        raise ValueError('emphasized station {} is not known'.format(e))

gfs_cycles = eht_met_forecast.data.get_gfs_cycles(basedir=datadir)
gfs_cycles = gfs_cycles[-(384//6):]  # never work on anything but the most recent 384 hours

work = get_all_work(datadir, plotdir, gfs_cycles, stations, force=args.force, verbose=verbose)
if not work:
    print('no work to do', file=sys.stderr)
    exit(0)

# we need to fetch 384/6=64 gfs_cycles before the first gfs_cycle, in
# order to have complete data for the needed work

earliest = sorted(work.keys())[0]
earliest_loc = gfs_cycles.index(earliest)
earliest = max(0, earliest_loc - 64)
gfs_cycles = gfs_cycles[earliest:]

start, end = get_dates(args)

for gfs_cycle in gfs_cycles:
    if verbose:
        print(gfs_cycle)

    do_00_plot(gfs_cycle, None, start, end, plotdir, stations, force=args.force, include=emphasize, name='00e')
    do_00_plot(gfs_cycle, None, start, end, plotdir, stations, force=args.force, include=emphasize, name='00w', datadir=datadir)
    do_00_plot(gfs_cycle, None, start, end, plotdir, stations, force=args.force, include=emphasize, name='00wg', datadir=datadir)
    do_00_plot(gfs_cycle, None, start, end, plotdir, stations, force=args.force, include=emphasize, name='00p', datadir=datadir)

    allest = defaultdict(dict)
    allint = defaultdict(dict)

    for s, station in stations.items():
        if verbose:
            print(' ', s)
        try:
            do_plot(station, gfs_cycle, allest, allint, start, end, datadir, plotdir, force=args.force)
        except Exception as ex:
            print('station {} gfs_cycle {} saw exception {}'.format(s, gfs_cycle, str(ex)), file=sys.stderr)
            print(traceback.format_exc())

    if verbose:
        print(' ', '00')
    do_00_plot(gfs_cycle, allest, start, end, plotdir, stations, force=args.force, include=emphasize, name='00')
    do_00_plot(gfs_cycle, allest, start, end, plotdir, stations, force=args.force, exclude=emphasize, name='01')

    if verbose:
        print(' ', 'csv')
    do_forecast_csv(gfs_cycle, allest, start, end, plotdir, emphasize=emphasize, force=args.force)
    do_trackrank_csv(gfs_cycle, allint, start, end, args.vex, plotdir, include=emphasize, force=args.force)

    if verbose:
        print(' ', 'tau')
    try:
        write_gfs_eu_style(allest, stations, gfs_cycle, plotdir, force=args.force, verbose=verbose)
    except Exception as e:
        print('saw exception calling write_gfs_eu_style: '+repr(e))
        print(traceback.format_exc())
