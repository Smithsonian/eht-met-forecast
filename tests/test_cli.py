import os.path
import re

import requests_mock

from eht_met_forecast.cli import main


def test_cli(capsys):
    tests = [
        [
            {'file': 'test.grb', 'args': ['--vex', 'Mm', '--one', '--stdout']},
            {'stdout': '20200316_18:00:00   7.6246e-02   2.3999e+01   1.4787e+00   0.0000e+00   0.0000e+00   2.7655e+02\n'}
        ],
    ]

    for t in tests:
        t_in, t_out = t
        if 'file' in t_in:

            fname = t_in['file']
            del t_in['file']    
            fname = os.path.split(__file__)[0] + '/' + fname
            with open(fname, 'rb') as f:
                input_buffer = f.read()

            with requests_mock.Mocker() as m:
                m.get(requests_mock.ANY, content=input_buffer)
                main(args=t_in['args'])
                out, err = capsys.readouterr()
                if 'stderr' in t_out:
                    assert err == t_out['stderr']
                if 'stdout' in t_out:
                    out = re.sub(r'#.*\n', '', out)
                    out = out[12:]
                    assert out == t_out['stdout'][12:]
