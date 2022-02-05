# eht-met-forecast

[![Build Status](https://dev.azure.com/lindahl0577/eht-met-forecast/_apis/build/status/lindahl0577.eht-met-forecast?branchName=main)](https://dev.azure.com/lindahl0577/eht-met-forecast/_build/latest?definitionId=3&branchName=main) [![Coverage](https://coveralls.io/repos/github/wumpus/eht-met-forecast/badge.svg?branch=main)](https://coveralls.io/github/wumpus/eht-met-forecast?branch=main) [![Apache License 2.0](https://img.shields.io/github/license/wumpus/eht-met-forecast.svg)](LICENSE)

eht-met-forecast creates radio-astronomy-relevant weather forecast
graphs for the
[Event Horizon Telescope](https://eventhorizontelescope.org/).

This code downloads raw weather forecast data from the NOAA GFS weather model.
It then runs this forecast through Scott Paine's
[AM radiative transfer code](https://doi.org/10.5281/zenodo.640645)
to compute values of interest to radio astronomy, such as the opacity
at millimeter frequencies. These derived values are then archived.
These values are also used to create graphs of near-future weather, which are
embedded in a webpage. These webpages are then used by the
EHT Array Operations Center for daily GO/NO-GO decisions during our observations.

## Graphs



## Running

```
% eht-met-forecast -h
% eht-met-forecast --backfill 168 --dir . --vex Sw --wait --log LOG
```

## Installation Clues

This code depends on two dependencies, `pygrib` and `am`. The [azure
pipelines configuration file for this repo](azure-pipelines.yml) shows
a working solution for both in the azure pipelines Ubuntu and
MacOS-based environment. Here are some rough notes:

### pygrib

The python pygrib package requires a few OS packages:

```
# Ubuntu 18.04 or later -- libeccodes isn't available earlier -- tested in the CI
apt-get install libeccodes-dev proj-bin libproj-dev libcairo2-dev
# RedHat flavored distros -- not tested
yum install eccodes-devel proj proj-devel cairo-devel
# Homebrew -- tested in the CI on MacOS
brew install eccodes proj cairo
# conda-forge: guesses, not tested
conda install -c conda-forge eccodes proj cairo
```

Once these OS packages are installed, the following sequence is needed in order:

- pip install cython
- pip install pygrib

The `setup.py` file does this for you.

Finally, on MacOS XCode 12 and later, you need:

`export CFLAGS="-Wno-implicit-function-declaration"`

because cython generates C code that triggers this warning (which becomes a fatal error).

### am

The am code is straightforward C and does not require any unusual libraries.

The included `Makefile` has instructions to build it:

`make am11`

Before running `eht-met-forecast`, you need to set an environment variable:

```
export AM=./am-11.0/src/am
$AM -v
```

### this code

Once the OS pacakges for `pygrib` and `am` are installed,

```
pip install .
pip install .[test]  # if you want to run tests
pytest
```

## Credits and similar projects

This code mainly a refactoring of Scott Paine's
[sma-met-forecast](https://github.com/Smithsonian/sma-met-forecast) repo.
The graph code is descended from code written by Scott Paine and Lindy
Blackburn. Many members of the EHT Collaboration have made helpful comments.

[CK Chan and Phani Datta Velicheti have independently refactored Scott Paine's code.](https://github.com/focisrc/ucast)

Alex Raymond has used [MERRA-2 historical weather data](https://gmao.gsfc.nasa.gov/reanalysis/MERRA-2/) to [evaluate
potential next-generation EHT sites.](https://arxiv.org/abs/2102.05482)

Our European colleagues have similar code to process a European weather forecast.
