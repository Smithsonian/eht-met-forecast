import eht_met_forecast.gfs as gfs


def test_jiggle():
    # the algorithm adds up to 33%
    assert gfs.jiggle(10) < 14
    assert gfs.jiggle(10) < 14
    assert gfs.jiggle(10) < 14
    assert gfs.jiggle(10) < 14
    assert gfs.jiggle(10) < 14
    assert gfs.jiggle(1) < 2

