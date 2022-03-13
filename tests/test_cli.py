import os.path
import re
import sys

import pytest
import requests_mock

from eht_met_forecast.cli import main


def whack_timeouts():
    # don't do this at home
    import eht_met_forecast.gfs
    eht_met_forecast.gfs.CONN_TIMEOUT = 1
    eht_met_forecast.gfs.READ_TIEMOUT = 1
    eht_met_forecast.gfs.RETRY_DELAY = 0.1


count_403 = 0


def content_403_second(request, context):
    global count_403
    if count_403:
        fname = os.path.split(__file__)[0] + '/' + 'test.grb'
        with open(fname, 'rb') as f:
            content = f.read()
        context.status_code = 200
        return content
    else:
        count_403 = 1
        return


def test_cli(capsys):

    # AM 11.0 gfs15_to_am
    #stdout = '00:00   7.6246e-02   2.3999e+01   1.4787e+00   0.0000e+00   0.0000e+00   2.7655e+02\n'
    # AM 11.0 gfs16_to_am and bugfixes 2/5/22
    #stdout =  '00:00   7.6247e-02   2.3999e+01   1.4794e+00   0.0000e+00   0.0000e+00   2.7655e+02\n'
    # AM 12.0 gfs16 is the same
    # new test.grb with wind (but not 10 meter wind)
    #stdout = '00:00   1.1151e-01   3.2311e+01   2.4032e+00   0.0000e+00   0.0000e+00   2.6272e+02\n'
    # new test.grb with 10 meter wind
    stdout = '00:00   3.2899e-02   1.2753e+01   4.5020e-01   0.0000e+00   0.0000e+00   3.2356e+02\n'

    stdout = '20200316+18:' + stdout

    tests = [
        [
            {'contentf': 'test.grb', 'args': ['--vex', 'Mm', '--hours', '1', '--stdout']},
            {'stdout': stdout}
        ],
        [
            {'contentf': 'test.grb', 'args': ['--vex', 'Mm', '--hours', '1', '--stdout', '--log', 'LOG.pytest']},
            {'stdout': stdout, 'ofile': 'LOG.pytest'}
        ],
        [
            {'status_code': 500, 'whack_timeouts': True, 'exception': SystemExit,
             'args': ['--vex', 'Mm', '--hours', '1', '--stdout']},
            {'stdout': ''},
        ],
        [
            {'contentc': content_403_second, 'status_code': 403, 'whack_timeouts': True,
             'args': ['--vex', 'Mm', '--hours', '1', '--stdout']},
            {'stdout': stdout},
        ],
    ]

    for t in tests:
        t_in, t_out = t

        kwargs = {}

        if 'contentf' in t_in:
            fname = t_in['contentf']
            fname = os.path.split(__file__)[0] + '/' + fname
            with open(fname, 'rb') as f:
                content = f.read()
            kwargs['content'] = content

        if 'contentc' in t_in:
            kwargs['content'] = t_in['contentc']

        if 'status_code' in t_in:
            kwargs['status_code'] = t_in['status_code']

        if 'ofile' in t_out:
            try:
                os.unlink(t_out['ofile'])
            except FileNotFoundError:
                pass

        if t_in.get('whack_timeouts'):
            whack_timeouts()

        with requests_mock.Mocker() as m:
            m.get(requests_mock.ANY, **kwargs)
            if 'exception' in t_in:
                with pytest.raises(t_in['exception']):
                    main(args=t_in['args'])
            else:
                main(args=t_in['args'])

        out, err = capsys.readouterr()

        if 'stderr' in t_out:
            assert err == t_out['stderr']
        else:
            print(err, file=sys.stderr)
        if 'stdout' in t_out:
            if 'exeption' in t_in:
                print(out)
                assert False
            out = re.sub(r'#.*\n', '', out)
            out = out[12:]  # drop date at the start of the line
            assert out == t_out['stdout'][12:]
        if 'ofile' in t_out:
            assert os.path.isfile(t_out['ofile'])
