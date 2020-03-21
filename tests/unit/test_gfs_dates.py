import eht_met_forecast


def test_latest_gfs_cycle_time():
    t = eht_met_forecast.latest_gfs_cycle_time(now=1234567890., lag=5.2)
    assert t.strftime('%Y%m%d%H') == '2009021312'
    t = eht_met_forecast.latest_gfs_cycle_time(now=1234567890.)
    assert t.strftime('%Y%m%d%H') == '2009021318'
