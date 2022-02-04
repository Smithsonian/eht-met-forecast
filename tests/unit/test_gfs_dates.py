import datetime
import eht_met_forecast.gfs


def test_latest_gfs_cycle_time():
    print('hint: test time is', datetime.datetime.fromtimestamp(1234567890., tz=datetime.timezone.utc).strftime('%Y%m%d%H'))

    t = eht_met_forecast.gfs.latest_gfs_cycle_time(now=1234564890., lag=5.2)
    assert t.strftime('%Y%m%d%H') == '2009021312'
    t = eht_met_forecast.gfs.latest_gfs_cycle_time(now=1234567890.)
    assert t.strftime('%Y%m%d%H') == '2009021318'
