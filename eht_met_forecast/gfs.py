import datetime
import requests
import sys
import time

from .latlon import box
from .constants import GFS_DAYHOUR, GFS_HOUR, LATLON_GRID_STR, LATLON_DELTA, LEVELS


def latest_gfs_cycle_time(now=None, lag=None):
    if now is None:
        dt_gfs = datetime.datetime.utcnow()
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
        'dir': '/gfs.{}'.format(gfs_dayhour),
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
MAX_DOWNLOAD_TRIES  = 4


def fetch_gfs_download(url, params, wait=False, verbose=False):

    retry = MAX_DOWNLOAD_TRIES
    while retry > 0:
        try:
            r = requests.get(url, params=params, timeout=(CONN_TIMEOUT, READ_TIMEOUT))
            if r.status_code == requests.codes.ok:
                errflag = 0
            elif r.status_code == 404:
                errflag = 1
                if wait:
                    retry += 1  # free retry
                print('Data not yet available (404)', file=sys.stderr, end='')
            elif r.status_code in {403, 429, 503}:
                # I've never seen NOMADS send these but they are typical "slow down" status codes
                errflag = 1
                print('Received retryable status ({})'.format(r.status_code), file=sys.stderr, end='')
                retry += 0.8  # this counts as 1/5 of a retry
            elif r.status_code in {500, 502, 504}:
                # I've seen 502 from NOMADS when the website is broken
                errflag = 1
                print('Received retryable status ({})'.format(r.status_code), file=sys.stderr, end='')
                retry += 0.8  # this counts as 1/5 of a retry
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
        except requests.exceptions.ReadTimeout:
            print("Data download timed out.", file=sys.stderr, end='')
            errflag = 1
        except requests.exceptions.RequestException as e:
            print("Surprising exception of", str(e)+".", file=sys.stderr, end='')
            errflag = 1

        if errflag:
            retry = retry - 1
            if retry > 0:
                print("  Retrying...", file=sys.stderr)
                time.sleep(RETRY_DELAY)
            else:
                print("  Giving up.", file=sys.stderr)
                print("Failed URL was: ", url, file=sys.stderr)
                raise TimeoutError('gave up')  # caught in cli.py
        else:
            break

    return r.content


def download_gfs(lat, lon, alt, gfs_cycle, forecast_hour, wait=False, verbose=False):
    url, params = form_gfs_download_url(lat, lon, alt, gfs_cycle, forecast_hour)
    grib_buffer = fetch_gfs_download(url, params, wait=wait, verbose=verbose)
    return grib_buffer
