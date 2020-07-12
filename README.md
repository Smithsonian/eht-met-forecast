# eht-met-forecast

eht-met-forecast creates radio-astronomy-relevant weather forecast
data for the
[Event Horizon Telescope](https://eventhorizontelescope.org/),
downloading data from the
GFS weather model and running it through the
[AM radiative transfer program](https://doi.org/10.5281/zenodo.640645).

This code has a lot of code from
[sma-met-forecast](https://github.com/Smithsonian/sma-met-forecast),
with a lot of refactoring.

## Running

% eht-met-forecast -h

## Installation

This code depends on two relatively hard-to-install dependencies,
pygrib and am.

### pygrib

pygrib can't be usefully installed using pip; I recommend installing
from the git repo using
[the clues in this gist](https://gist.github.com/emmanuelnk/406eee50c388f4f73dcdff521f2aa7b2).
Depending on your python version, you may get an error installing
pygrib due to the version of Cython used to generate pygrib.c not being
modern enough. To fix that, right before generating the zip file:

```
pip install cython
python setup.py build_ext --inplace
```

