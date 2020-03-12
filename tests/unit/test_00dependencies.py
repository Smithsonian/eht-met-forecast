def test_pygrib_import():
    try:
        import pygrib
    except ImportError as e:
        raise ValueError('pygrib import failed, you need to install it but not using pip: '+str(e))
