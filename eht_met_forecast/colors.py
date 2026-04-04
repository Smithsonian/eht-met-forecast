from collections import namedtuple


#color_list = [  # IBM palette for color-blindness
#    '#648FFF',  # blue
#    '#785EF0',  # purple
#    '#DC267F',  # magenta
#    '#FE6100',  # orange
#    '#FFB000',  # dark yellow
#]

# Wong colors https://davidmathlogic.com/colorblind/
#color_list = [
#    '#000000',  # black
#    '#0072b2',  # blue -- most successful line
#    '#56b4e9',  # sky-blue
#    '#009e73',  # bluish-green
#    '#f0e442',  # yellow
#    '#d55e00',  # vermillion
#    '#cc79a7',  # reddish-purple
#    '#e69f00',  # organge -- least successful line
#]

# vibrant https://sronpersonalpages.nl/~pault/
color_list = [
    '#EE7733',  # blue
    '#0077BB',  # cyan
    '#33BBEE',  # teal
    '#EE3377',  # orange
    '#CC3311',  # red
    '#009988',  # magenta
    '#BBBBBB',  # grey
]

# https://matplotlib.org/stable/gallery/lines_bars_and_markers/linestyles.html to add more
ls_list = ['solid', 'dashed', 'dashdot', 'dotted']
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
