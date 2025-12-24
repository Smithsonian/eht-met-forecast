from collections import namedtuple


color_list = [  # IBM palette for color-blindness
    '#648FFF',  # blue
    '#785EF0',  # purple
    '#DC267F',  # magenta
    '#FE6100',  # orange
    '#FFB000',  # dark yellow
]

# https://matplotlib.org/stable/gallery/lines_bars_and_markers/linestyles.html to add more
ls_list = ['solid', 'dashed', 'dotted', 'dashdot']
#marker_list = ['o', 'v', '^', 's', 'd']

color_count = len(color_list)
combinations = color_count * len(ls_list)


Color = namedtuple('Color', ['color', 'ls', 'lw'])


def get_colors(stations):
    colors = {}
    deduped = list(dict.fromkeys(stations))
    for i, station in enumerate(sorted(deduped)):
        print(i, station)
        color = color_list[i % color_count]
        assert i <= combinations, 'too many colors'
        ls = ls_list[i // color_count]
        lw = 1.0
        colors[station] = Color(color, ls, lw)
    return colors
