import os
import os.path
import subprocess

def test_pygrib_import():
    try:
        import pygrib
    except ImportError as e:
        raise ValueError('pygrib import failed, you need to install it: '+str(e))


def test_am_environment():
    assert 'AM' in os.environ, 'AM environment variable is set'
    assert os.path.isfile(os.environ['AM']), 'AM environment variable points at a file'
    comp = subprocess.run((os.environ['AM'], '-v'), check=True)
