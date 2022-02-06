import time
import sys
from contextlib import contextmanager

from hdrh.histogram import HdrHistogram

hists = {}


@contextmanager
def record_latency(name):
    try:
        start = time.time()
        yield
    finally:
        elapsed = time.time() - start
        if name not in hists:
            hists[name] = HdrHistogram(1, 30 * 1000, 2)  # 1ms-30sec, 2 sig figs
        hists[name].record_value(elapsed * 1000)  # ms


def dump_latency_histograms(log=None):
    out = '  name t50 t90 t95 t99\n'

    for name in sorted(hists.keys()):
        hist = hists[name]
        t50 = hist.get_value_at_percentile(50.0) / 1000.
        t90 = hist.get_value_at_percentile(90.0) / 1000.
        t95 = hist.get_value_at_percentile(95.0) / 1000.
        t99 = hist.get_value_at_percentile(99.0) / 1000.

        out += '  {} {} {} {} {}\n'.format(name, t50, t90, t95, t99)

    print(out, file=sys.stderr)
    if log:
        with open(log, 'a') as fd:
            print(out, file=fd)
