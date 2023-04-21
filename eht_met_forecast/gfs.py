import datetime
import requests
import sys
import time
import random
import http.client

from .latlon import box
from .constants import GFS_DAYHOUR, GFS_HOUR, LATLON_GRID_STR, LATLON_DELTA, LEVELS


def latest_gfs_cycle_time(now=None, lag=None):
    if now is None:
        dt_gfs = datetime.datetime.now(datetime.timezone.utc)
    else:
        dt_gfs = datetime.datetime.fromtimestamp(now, tz=datetime.timezone.utc)

    if lag:
        dt_gfs_lag = datetime.timedelta(hours=lag)
        dt_gfs -= dt_gfs_lag

    return dt_gfs.replace(hour=int(dt_gfs.hour / 6) * 6, minute=0, second=0, microsecond=0)


def form_gfs_download_url(lat, lon, alt, gfs_cycle, forecast_hour):
    CGI_URL = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_{}_1hr.pl"
    url = CGI_URL.format(LATLON_GRID_STR)

    leftlon, rightlon, bottomlat, toplat = box(lat, lon, LATLON_DELTA)

    gfs_dayhour = gfs_cycle.strftime(GFS_DAYHOUR)
    gfs_hour = gfs_cycle.strftime(GFS_HOUR)
    gfs_product = 'f{:03d}'.format(forecast_hour)

    params = {
        'dir': '/gfs.{}/atmos'.format(gfs_dayhour),
        'file': 'gfs.t{}z.pgrb2.{}.{}'.format(gfs_hour, LATLON_GRID_STR, gfs_product),
        'subregion': '',
        'leftlon': leftlon,
        'rightlon': rightlon,
        'toplat': toplat,
        'bottomlat': bottomlat,
    }

    for lev in LEVELS:
        params['lev_{:d}_mb'.format(lev)] = 'on'
    params['lev_10_m_above_ground'] = 'on'  # wind level=10
    params['lev_surface'] = 'on'  # CRAIN etc, GUST, maps to level=0
    params['lev_max_wind'] = 'on'  # UGRD, VGRD, maps to level=0

    # hint: https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25_1hr.pl
    # shows an interactive page where you can click on stuff

    VARIABLES = ["CLWMR", "ICMR", "HGT", "O3MR", "RH", "TMP"]  # for AM
    VARIABLES += ["UGRD", "VGRD"]  # wind
    VARIABLES += ["CRAIN", "CFRZR", "CICEP", "CSNOW"]  # yes/no 1/0 rain, freezing rain, ice pellets, snow
    VARIABLES += ["GUST"]  # lev_surface level=0
    '''
    these are all of the levels -- get_gfs.pl download of all variables

    95:Geopotential Height:gpm (instant):regular_ll:isobaricInhPa:level 100 Pa:fcst time 0 hrs:from 202202060000
    96:Temperature:K (instant):regular_ll:isobaricInhPa:level 100 Pa:fcst time 0 hrs:from 202202060000
    97:Relative humidity:% (instant):regular_ll:isobaricInhPa:level 100 Pa:fcst time 0 hrs:from 202202060000
    98:Specific humidity:kg kg**-1 (instant):regular_ll:isobaricInhPa:level 100 Pa:fcst time 0 hrs:from 202202060000
    99:Vertical velocity:Pa s**-1 (instant):regular_ll:isobaricInhPa:level 100 Pa:fcst time 0 hrs:from 202202060000
    100:Geometric vertical velocity:m s**-1 (instant):regular_ll:isobaricInhPa:level 100 Pa:fcst time 0 hrs:from 202202060000
    101:U component of wind:m s**-1 (instant):regular_ll:isobaricInhPa:level 100 Pa:fcst time 0 hrs:from 202202060000
    102:V component of wind:m s**-1 (instant):regular_ll:isobaricInhPa:level 100 Pa:fcst time 0 hrs:from 202202060000
    103:Absolute vorticity:s**-1 (instant):regular_ll:isobaricInhPa:level 100 Pa:fcst time 0 hrs:from 202202060000
    104:Ozone mixing ratio:kg kg**-1 (instant):regular_ll:isobaricInhPa:level 100 Pa:fcst time 0 hrs:from 202202060000
    642:Temperature:K (instant):regular_ll:heightAboveGround:level 100 m:fcst time 0 hrs:from 202202060000
    643:100 metre U wind component:m s**-1 (instant):regular_ll:heightAboveGround:level 100 m:fcst time 0 hrs:from 202202060000
    644:100 metre V wind component:m s**-1 (instant):regular_ll:heightAboveGround:level 100 m:fcst time 0 hrs:from 202202060000

    level 0, yet to figure out how to fetch them. maxWind? maybe this is at any altitude?!
    the level 100+ winds above work with the normal levels

    626:U component of wind:m s**-1 (instant):regular_ll:maxWind:level 0:fcst time 0 hrs:from 202202060000
    627:V component of wind:m s**-1 (instant):regular_ll:maxWind:level 0:fcst time 0 hrs:from 202202060000
    https://www.weatheronline.co.uk/cgi-bin/expertcharts?LANG=en&CONT=ukuk&MODELL=gfs&MODELLTYP=1&VAR=uv10&INFO=1&
    "surface wind" which is wind at 10 meters above the ground
    https://www.tropicaltidbits.com/analysis/models/?model=gfs&region=us&pkg=mslp_wind&runtime=2022020618&fh=6
    also says "10m wind"

    585:10 metre U wind component:m s**-1 (instant):regular_ll:heightAboveGround:level 10 m:fcst time 0 hrs:from 202202060000
    586:10 metre V wind component:m s**-1 (instant):regular_ll:heightAboveGround:level 10 m:fcst time 0 hrs:from 202202060000



    these next ones are the lowest height

    level 0, also called surface, actually works with lev_surface

    590:Categorical snow:(Code table 4.222) (instant):regular_ll:surface:level 0:fcst time 0 hrs:from 202202060000
    591:Categorical ice pellets:(Code table 4.222) (instant):regular_ll:surface:level 0:fcst time 0 hrs:from 202202060000
    592:Categorical freezing rain:(Code table 4.222) (instant):regular_ll:surface:level 0:fcst time 0 hrs:from 202202060000
    593:Categorical rain:(Code table 4.222) (instant):regular_ll:surface:level 0:fcst time 0 hrs:from 202202060000

    these are the only 'precip' or 'percent' entries:
    588:Percent frozen precipitation:% (instant):regular_ll:surface:level 0:fcst time 0 hrs:from 202202060000
    PRATE 589:Precipitation rate:kg m**-2 s**-1 (instant):regular_ll:surface:level 0:fcst time 0 hrs:from 202202060000
    PWAT 604:Precipitable water:kg m**-2 (instant):regular_ll:atmosphereSingleLayer:level 0 considered as a single layer:fcst time 0 hrs:from 202202060000
    CWAT

    test me: not in the inventory (!)
    not useful, it's at any altitue https://www.weatheronline.co.uk/cgi-bin/expertcharts?MODELL=gfs&MODELLTYP=1&VAR=boen&INFO=1
    14:Wind speed (gust):m s**-1 (instant):regular_ll:surface:level 0:fcst time 0 hrs:from 202202060000
    would be useful to have this, because it might be related to the atmospheric coherance time
    550 and 551? https://www.nco.ncep.noaa.gov/pmb/products/gfs/gfs.t00z.pgrb2.0p25.anl.shtml



    '''

    for var in VARIABLES:
        params['var_' + var] = 'on'

    return url, params


# Timeouts and retries
CONN_TIMEOUT        = 60       # Initial server response timeout in seconds
READ_TIMEOUT        = 60       # Stalled download timeout in seconds
RETRY_DELAY         = 60       # Delay before retry (NOAA requests 60 s)
FOUROHFOUR_DELAY    = 300      # Delay after a 404 (data not ready, wait=True)
RATELIMIT_DELAY     = 60
MAX_DOWNLOAD_TRIES  = 8


def jiggle(seconds):
    jig = seconds // 3
    return random.randint(seconds, seconds + jig)


def fetch_gfs_download(url, params, wait=False, verbose=False, stats=None):

    retry = MAX_DOWNLOAD_TRIES
    actual_tries = 0
    r = None  # so we can use it even after an exception
    while retry > 0:
        quiet_retry = False
        try:
            actual_tries += 1
            retry_duration = RETRY_DELAY
            r = requests.get(url, params=params, timeout=(CONN_TIMEOUT, READ_TIMEOUT))
            if stats:
                stats[str(r.status_code)] += 1
            if r.status_code == requests.codes.ok:
                errflag = 0
            elif r.status_code == 404:
                errflag = 1
                if wait:
                    retry += 1  # free retry
                    retry_duration = jiggle(FOUROHFOUR_DELAY)
                print('Data not yet available (404)', file=sys.stderr, end='')
            elif r.status_code in {403, 429, 503}:
                # 403, 429: I've never seen NOMADS send these but they are typical "slow down" status codes
                # NOMADS behind CDN will start sending 403s Aug 23, 2022 ?? the 403 has a reference number in the content
                #   this didn't happen, they are still sending 302 with no Location: for slow down
                # 503 example: Dec 2022, Apr 2023: "Error: An error occurred while processing your request." (wrapped in html)
                errflag = 1
                print('Received surprising retryable status ({})'.format(r.status_code), file=sys.stderr, end='')
                #if r.status_code == 403 and r.content:
                if r.content:
                    print(', text: '+r.text[:100], file=sys.stderr, end='')
                retry += 1  # free retry
                retry_duration = jiggle(RATELIMIT_DELAY)
                if stats:
                    stats['ratelimit_surprising'] += 1
            elif r.status_code in {302} and 'Location' not in r.headers:
                # here's what they started sending after 4/20/2021:
                # HTTP/1.1 302 Your allowed limit has been reached. Please go to https://www.weather.gov/abusive-user-block for more info
                # This 302 does not have a Location: header, so we test for it to make it less likely we'll end up in an infinite loop
                # These still happen (but very rarely) after the aug 2022 change to using a CDN
                errflag = 1
                if actual_tries > 1:
                    # this happens ~ 33 times per run (out of 209) so make it quieter
                    print('Received retryable status ({})'.format(r.status_code), file=sys.stderr, end='')
                else:
                    quiet_retry = True
                retry += 1  # free retry
                retry_duration = jiggle(RATELIMIT_DELAY)
                if stats:
                    stats['ratelimit_302_no_location'] += 1
            elif r.status_code in {302}:
                # ? this can happen if you ask for a date too far in the past
                # allow_redirects=True is the default for .get() so by default the redir will be followed
                # so a 302 shouldn't be visible
                errflag = 1
                print('should not happen: 302 with Location: {} seen'.format(r.headers['Location']), file=sys.stderr, end='')
                if stats:
                    stats['302_with_location'] += 1
            elif r.status_code in {500, 502, 504}:
                # I've seen 502 from NOMADS when the website is broken
                # 500s when the lev_ or var_ are incorrect, detailed message in the contents
                errflag = 1
                print('Received retryable status ({})'.format(r.status_code), file=sys.stderr, end='')
                retry += 0.8  # this counts as 1/5 of a retry
                if stats:
                    stats['website_broken'] += 1
            else:
                errflag = 1
                print("Download failed with status code {0}".format(r.status_code),
                      file=sys.stderr, end='')
                if verbose:
                    print('url:', r.url, file=sys.stderr)
                    print('content:', r.content, file=sys.stderr)
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
            print("Connection timed out.", file=sys.stderr, end='')
            errflag = 1
            if wait:
                retry += 1
                if stats:
                    stats['timeout_with_wait'] += 1
            else:
                if stats:
                    stats['timeout_without_wait'] += 1
        except requests.exceptions.ReadTimeout:
            print("Data download timed out.", file=sys.stderr, end='')
            errflag = 1
            if stats:
                stats['timeout_read'] += 1
        except requests.exceptions.ChunkedEncodingError:
            print("Incomplete read.", file=sys.stderr, end='')
            errflag = 1
            if stats:
                stats['incomplete_read'] += 1
        except requests.exceptions.RequestException as e:
            print("Surprising exception of", repr(e)+".", file=sys.stderr, end='')
            errflag = 1
            if stats:
                stats['exception_'+str(e)] += 1

        if errflag:
            retry = retry - 1
            if retry > 0:
                if not quiet_retry:
                    print(' tries={}'.format(actual_tries), file=sys.stderr, end='')
                    print("  Retrying...", file=sys.stderr)
                    if r:
                        try:  # I don't think this can fail, but anyway
                            text = r.text[:100]
                            if text:
                                print('  Text was:', text, file=sys.stderr)
                        except Exception:
                            pass
                time.sleep(retry_duration)
            else:
                print("  Giving up.", file=sys.stderr)
                print("Failed URL was: ", url, file=sys.stderr)
                if stats:
                    stats['giving_up'] += 1
                raise TimeoutError('gave up')  # caught in cli.py
        else:
            break

    return r.content


def download_gfs(lat, lon, alt, gfs_cycle, forecast_hour, wait=False, verbose=False, stats=None):
    url, params = form_gfs_download_url(lat, lon, alt, gfs_cycle, forecast_hour)
    grib_buffer = fetch_gfs_download(url, params, wait=wait, verbose=verbose, stats=stats)
    return grib_buffer
