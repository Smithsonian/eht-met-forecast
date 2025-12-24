import random
import eht_met_forecast.colors
import pytest


def test_get_colors():
    stations = "VLBBR:VLBFD:VLBHN:VLBKP:VLBLA:VLBMK:VLBNL:VLBOV:VLBPT:VLBSC:GBT:HAY:Gl".split(':')

    colors = eht_met_forecast.colors.get_colors(stations)
    colors2 = eht_met_forecast.colors.get_colors(stations+stations)

    for k, v in colors.items():
        assert v.color
        assert v.ls
        assert v.lw
        break

    assert colors == colors2
