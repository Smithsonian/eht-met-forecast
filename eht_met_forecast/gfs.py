import datetime
import requests
import sys
import time
import random

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
    VARIABLES = ("CLWMR", "ICMR", "HGT", "O3MR", "RH", "TMP")
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
    quiet_retry = False
    r = None  # so we can use it even after an exception
    while retry > 0:
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
                # 403, 429, 503: I've never seen NOMADS send these but they are typical "slow down" status codes
                errflag = 1
                print('Received surprising retryable status ({})'.format(r.status_code), file=sys.stderr, end='')
                retry += 1  # free retry
                retry_duration = jiggle(RATELIMIT_DELAY)
                if stats:
                    stats['ratelimit_surprising'] += 1
            elif r.status_code in {302} and 'Location' not in r.headers:
                # here's what they started sending after 4/20/2021:
                # HTTP/1.1 302 Your allowed limit has been reached. Please go to https://www.weather.gov/abusive-user-block for more info
                # This 302 does not have a Location: header, so we test for it to make it less likely we'll end up in an infinite loop
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
        except requests.exceptions.RequestException as e:
            print("Surprising exception of", str(e)+".", file=sys.stderr, end='')
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
                            content = r.content[:100]
                            if content:
                                print('  Content was:', content, file=sys.stderr)
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
