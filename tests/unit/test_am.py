from pytest import approx
from math import sqrt

from eht_met_forecast import am


def test_grid_interp():
    t = [[1, 2], [3, 4]]
    u, v = .1, .1
    assert am.grid_interp(t, u, v) == approx(1.3)

    t = [[0, 1], [0, 1]]
    u, v = .1, .1
    # 0 + 0 + 1*.9*.1 + 1*.1*.1 = .09+.01
    assert am.grid_interp(t, u, v) == approx(0.1)
    u, v = .1, .2
    # 0 + 0 + 1*.9*.2 + 1*.1*.2 = .18+.02 = 0.2
    assert am.grid_interp(t, u, v) == approx(0.2)
    u, v = .2, .1
    # 0 + 0 + 1*.8*.1 + 1*.2*.1 = .08 + .02 = 0.1
    assert am.grid_interp(t, u, v) == approx(0.1)

    assert am.grid_interp(t, 0.1, 0.1) * 2.0 == approx(am.grid_interp(t, 0.2, 0.2)), 'diagonal is a line'

    t = [[0, 1], [1, 1]]  # symmetric in u,v
    u, v = .1, .3
    assert am.grid_interp(t, u, v) == approx(am.grid_interp(t, v, u)), 'symmetric, is symmetric'
    assert am.grid_interp(t, 0.1, 0.0) * 2.0 == approx(am.grid_interp(t, 0.2, 0.0)), 'symmetric, edges are lines'

    t = [[0, 1], [1, 2]]  # flat
    u, v = .1, .3
    assert am.grid_interp(t, u, v) == approx(am.grid_interp(t, v, u)), 'flat, is symmetric'

    assert am.grid_interp(t, 0.1, 0.1) * 2.0 == approx(am.grid_interp(t, 0.2, 0.2)), 'flat, diagonal is a line'
    assert am.grid_interp(t, 0.1, 0.0) * 2.0 == approx(am.grid_interp(t, 0.2, 0.0)), 'flat, edges are lines'


def test_grid_interp_vector():
    t1 = [[1, 2], [3, 4]]
    t2 = [[1, 2], [3, 4]]
    u, v = .1, .1
    assert am.grid_interp_vector(t1, t2, u, v) == approx(1.8384776)

    c = [[sqrt(2.), sqrt(8.)], [sqrt(18.), sqrt(32.)]]
    assert am.grid_interp(c, u, v) == approx(1.8384776)

    assert am.grid_interp_vector(t1, t2, u, v) == am.grid_interp(c, u, v)

    t1 = [[0, 1], [0, 1]]
    t2 = [[0, 1], [0, 1]]
    u, v = .1, .1
    assert am.grid_interp_vector(t1, t2, u, v) == approx(0.1 * sqrt(2.))
