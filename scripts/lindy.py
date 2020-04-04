#!/usr/bin/env python
import argparse
import os
from os.path import expanduser
import sys
from collections import defaultdict
import datetime

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.offsetbox import AnchoredText
import numpy as np
from scipy.interpolate import interp1d
from astropy import units as u
from astropy.coordinates import SkyCoord, EarthLocation, AltAz

import eht_met_forecast.data
from eht_met_forecast import read_stations
import vex as vvex


def get_all_work(datadir, outputdir, gfs_cycles, stations, force=False):
    ret = {}
    for gfs_cycle in gfs_cycles:
        me = defaultdict(list)
        for vex in stations:
            inname = '{}/{}/{}'.format(datadir, vex, gfs_cycle)
            if not os.path.exists(inname):
                continue
            outname = '{}/{}/lindy_{}_{}.png'.format(outputdir, gfs_cycle, vex, gfs_cycle)
            me['lindy'].append(outname)
        outname = '{}/{}/lindy_{}_{}.png'.format(outputdir, gfs_cycle, '00', gfs_cycle)
        me['00'].append(outname)
        outname = '{}/{}/forecast.csv'.format(outputdir, gfs_cycle)
        me['forecast'].append(outname)
        outname = '{}/{}/trackrank.csv'.format(outputdir, gfs_cycle)
        me['trackrank'].append(outname)
        ret[gfs_cycle] = me

    if force:
        return

    for gfs_cycle in list(ret.keys()):
        for key in list(ret[gfs_cycle].keys()):
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


def do_plot(station, gfs_cycle, allest, allint, datadir, outputdir, force=False):
    site = station.get('vex') or station['name']
    data = eht_met_forecast.data.read_accumulated(site, gfs_cycle, basedir=datadir)
    if not data:
        return

    alldata = pd.concat(data, ignore_index=True).sort_values(['date', 'age'])
    alldata['sigma'] = (tfloor + alldata['age'].dt.total_seconds()/3600.)**tpow
    latest = alldata.groupby('date').first().reset_index()  # most recent prediction
    date0 = np.max(latest['date0'])

    gfs_cycle_dt = eht_met_forecast.data.gfs_cycle_to_dt(gfs_cycle)
    if date0 != gfs_cycle_dt:
        print('gfs_cycle and the first date in the csv disagree', file=sys.stderr)
        print('gfs_cycle', gfs_cycle)
        print('date0', eht_met_forecast.data.dt_to_gfs_cycle(date0))
        raise ValueError

    # ensemble estimator with errors
    est = alldata.groupby('date').apply(wavg).reset_index()
    est['site'] = site
    allest[site][gfs_cycle] = est
    allint[site][gfs_cycle] = interp1d(est.date.values.astype(int),
                                       est.est_mean.values, bounds_error=False)

    outname = '{}/{}/lindy_{}_{}.png'.format(outputdir, gfs_cycle, site, gfs_cycle)
    os.makedirs(os.path.dirname(outname), exist_ok=True)
    if not force and os.path.exists(outname):
        return

    # most recent forecast
    label = station['name'] + ' ' + str(date0)
    plt.plot(latest.date.values, latest.tau225, lw=1, label=label, color='black')
    plt.axvline(date0, color='black', ls='--')

    # old forecasts
    for df in data:
        if df.iloc[0].date0 == date0:
            continue
        plt.plot(df.date.values, df.tau225.values, color='black', alpha=1./len(data))

    # ensemble estimator
    plt.fill_between(est.date.values, est.est_mean.values/est.est_err,
                     est.est_mean.values*est.est_err, alpha=0.25)

    (first, last) = (pd.Timestamp(2020, 3, 26), pd.Timestamp(2020, 4, 6))
    days = pd.date_range(start=first, end=last, freq='D')
    for d in days:
        plt.axvspan(d, d+pd.Timedelta('15 hours'), color='C0', alpha=0.15, zorder=-10)
    # do this to get pandas date fmt on xlabel
    plt.plot(est.date.values, est.est_mean, label=station['name'] + ' ensemble')

    # formatting
    plt.ylim(0, 1.0)
    plt.yticks(np.arange(0, 1.0, .1))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator())
    plt.gca().fmt_xdata = mdates.DateFormatter('%Y-%m-%d')
    plt.gcf().autofmt_xdate()
    plt.autoscale(enable=True, axis='x', tight=True)
    plt.grid(alpha=0.25)
    plt.legend(loc='upper right')
    plt.gca().add_artist(AnchoredText(station['name'], loc=2))
    plt.xlabel('UT date')
    plt.ylabel('tau225')
    plt.xlim(days[0]-pd.Timedelta('5 days'), days[-1]+pd.Timedelta('3 days'))

    wide(14, 5)
    plt.savefig(outname, dpi=75)
    plt.close()


def do_forecast_csv(gfs_cycle, allest, outputdir, force=False):
    outname = '{}/{}/forecast.csv'.format(outputdir, gfs_cycle)
    os.makedirs(os.path.dirname(outname), exist_ok=True)
    if not force and os.path.exists(outname):
        return

    the_data = [allest[site][gfs_cycle] for site in allest if gfs_cycle in allest[site] and len(site) == 2]
    if not the_data:
        return
    print(outname)
    data = pd.concat(the_data, ignore_index=True)
    data['doy'] = data.date.dt.dayofyear

    nights = data[(data.date.dt.hour >= 0) & (data.date.dt.hour < 12) & (data.doy >= 86)]
    stats = nights.groupby(['site', 'doy']).median()

    df = stats.pivot_table(index='site', columns='doy', values='est_mean')
    df.to_csv(outname)

    outname = outname.replace('forecast.csv', 'forecast_future.csv')
    the_data = [allest[site][gfs_cycle] for site in allest if gfs_cycle in allest[site] and len(site) != 2]
    if not the_data:
        return
    print(outname)
    data = pd.concat(the_data, ignore_index=True)
    data['doy'] = data.date.dt.dayofyear

    nights = data[(data.date.dt.hour >= 0) & (data.date.dt.hour < 12) & (data.doy >= 86)]
    stats = nights.groupby(['site', 'doy']).median()

    df = stats.pivot_table(index='site', columns='doy', values='est_mean')
    df.to_csv(outname)


def do_trackrank_csv(gfs_cycle, allint, outputdir, force=False):
    outname = '{}/{}/trackrank.csv'.format(outputdir, gfs_cycle)
    os.makedirs(os.path.dirname(outname), exist_ok=True)
    if not force and os.path.exists(outname):
        return

    fmt_in = '%Yy%jd%Hh%Mm%Ss'
    # ['4524000.43000 m', '468042.14000 m', '4460309.76000 m']

    def xyz2loc(xyz):
        xyz = [float(b[0])*u.Unit(b[1]) for b in (c.split() for c in xyz)]
        return EarthLocation.from_geocentric(*xyz)

    trackrank = dict()
    Dns = 86400000000000  # 1 day in ns
    (start, stop) = (pd.Timestamp(2020, 3, 26), pd.Timestamp(2020, 4, 6))
    daysut = pd.date_range(start=start, end=stop, freq='D')
    daysdoy = [d.dayofyear for d in daysut]
    days = np.array([d.value for d in daysut])

    for t in 'abcdef':
        a = vvex.parse(open('track{}.vex'.format(t)).read())
        is345 = '345 GHz' in list(a['EXPER'].values())[0]['exper_description']
        station_loc = dict((b['site_ID'], xyz2loc(b['site_position']))
                           for b in a['SITE'].values())
        source_loc = dict((b, SkyCoord(c['ra'], c['dec'], equinox=c['ref_coord_frame']))
                          for (b, c) in a['SOURCE'].items())
        score = np.zeros(len(days))
        total = np.zeros(len(days))
        for b in a['SCHED'].values(): # does not necessarily loop in order!
            time = pd.Timestamp(datetime.datetime.strptime(b['start'], fmt_in))
            dtimes = days + np.mod(time.value + Dns//4, Dns) - Dns//4
            stations = set(c[0].replace('Ax', 'Aa').replace('Mm', 'Sw') for c in b['station'])
            taus = np.array([allint[s][gfs_cycle](dtimes) for s in stations])
            if is345:
                taus = 0.05 + 2.5*taus # scale up tau225 to 345 GHz
            alts = np.array([source_loc[b['source']].transform_to(
                AltAz(obstime=time, location=station_loc[s])).alt.value for s in stations])
            n = len(taus)
            am = 1./np.sin(alts*np.pi/180.)
            score += (n-1)*np.sum(np.exp(-am[:,None] * taus), axis=0)
            total += (n-1)*n
        trackrank[t.upper()] = score/total
    df = pd.DataFrame.from_dict(trackrank, orient='index', columns=daysdoy).sort_index()
    df.to_csv(outname)


def do_00_plot(gfs_cycle, allest, outputdir, stations, force=False):
    outname = '{}/{}/lindy_{}_{}.png'.format(outputdir, gfs_cycle, '00', gfs_cycle)
    os.makedirs(os.path.dirname(outname), exist_ok=True)
    if not force and os.path.exists(outname):
        return

    date0 = eht_met_forecast.data.gfs_cycle_to_dt(gfs_cycle)

    for site in sorted(allest):
        if len(site) != 2:
            continue
        if gfs_cycle not in allest[site]:
            continue
        est = allest[site][gfs_cycle]
        plt.plot(est.date.values, est.est_mean, label=stations[site]['name'], alpha=0.75, lw=1.5)
    plt.axvline(date0, color='black', ls='--')
    (first, last) = (pd.Timestamp(2020, 3, 26), pd.Timestamp(2020, 4, 6))
    days = pd.date_range(start=first, end=last, freq='D')
    for d in days:
        plt.axvspan(d, d+pd.Timedelta('15 hours'), color='black', alpha=0.05, zorder=-10)

    # formatting
    plt.ylim(0, 1.0)
    plt.yticks(np.arange(0, 1.0, .1))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator())
    plt.gca().fmt_xdata = mdates.DateFormatter('%Y-%m-%d')
    plt.gcf().autofmt_xdate()
    plt.autoscale(enable=True, axis='x', tight=True)
    plt.grid(alpha=0.25)
    plt.legend(loc='upper right')
    plt.xlabel('UT date')
    plt.ylabel('tau225')
    plt.xlim(days[0]-pd.Timedelta('5 days'), days[-1]+pd.Timedelta('3 days'))
    wide(14, 5)
    plt.savefig(outname, dpi=75)
    plt.close()


parser = argparse.ArgumentParser()
parser.add_argument('--stations', action='store', help='location of stations.json file')
parser.add_argument('--vex', action='store', help='site to plot')
parser.add_argument('--datadir', action='store', default='~/github/eht-met-data', help='data directory')
parser.add_argument('--outputdir', action='store', default='~/eht-met-plots', help='output directory for plots')
parser.add_argument('--force', action='store_true', help='make the plot even if the output file already exists')
#parser.add_argument('--am-version', action='store', default='11.0', help='am version')
#parser.add_argument("hours",  help="hours forward (0 to 384, typically 120 or 384)", type=int)

args = parser.parse_args()
datadir = expanduser(args.datadir)
outputdir = expanduser(args.outputdir)

station_dict = read_stations(args.stations)

if not args.vex:
    stations = station_dict.keys()
else:
    stations = (args.vex,)

gfs_cycles = eht_met_forecast.data.get_gfs_cycles(basedir=datadir)
work = get_all_work(datadir, outputdir, gfs_cycles, stations, force=args.force)

# we need to fetch 384/6=64 gfs_cycles before the first gfs_cycle, in
# order to have complete data for the needed work

earliest = sorted(work.keys())[0]
earliest_loc = gfs_cycles.index(earliest)
earliest = max(0, earliest_loc - 64)
gfs_cycles = gfs_cycles[earliest:]

for gfs_cycle in gfs_cycles:
    allest = defaultdict(dict)
    allint = defaultdict(dict)

    for vex in stations:
        station = station_dict[vex]

        try:
            do_plot(station, gfs_cycle, allest, allint, datadir, outputdir, force=args.force)
        except Exception as ex:
            print('station {} gfs_cycle {} saw exception {}'.format(vex, gfs_cycle, str(ex)), file=sys.stderr)

    do_00_plot(gfs_cycle, allest, outputdir, station_dict, force=args.force)
    do_forecast_csv(gfs_cycle, allest, outputdir, force=args.force)
    do_trackrank_csv(gfs_cycle, allint, outputdir, force=args.force)
