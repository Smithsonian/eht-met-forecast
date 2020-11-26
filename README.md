# eht-met-forecast

[![Build Status](https://dev.azure.com/lindahl0577/eht-met-forecast/_apis/build/status/lindahl0577.eht-met-forecast?branchName=master)](https://dev.azure.com/lindahl0577/eht-met-forecast/_build/latest?definitionId=3&branchName=master) [![Coverage](https://img.shields.io/azure-devops/coverage/lindahl0577/eht-met-forecast/3)](https://dev.azure.com/lindahl0577/eht-met-forecast/_build/latest?definitionId=3&branchName=master) [![Apache License 2.0](https://img.shields.io/github/license/wumpus/eht-met-forecast.svg)](LICENSE)

eht-met-forecast creates radio-astronomy-relevant weather forecast
data for the
[Event Horizon Telescope](https://eventhorizontelescope.org/),
downloading data from the
GFS weather model and running it through the
[AM radiative transfer program](https://doi.org/10.5281/zenodo.640645).

This code mainly a refactoring of
Scott Paine's
[sma-met-forecast](https://github.com/Smithsonian/sma-met-forecast) repo.

## Running

% eht-met-forecast -h

## Installation

This code depends on two relatively hard-to-install dependencies,
pygrib and am. The [azure pipelines configuration file for this repo](azure-pipelines.yml)
shows a working solution for both in the azure pipelines Ubuntu and MacOS-based environment. Here
are some rough notes:

### pygrib

```
apt-get install libeccodes-dev proj-bin libproj-dev  # ubuntu 18.04 or later
# yum install eccodes-devel proj proj-devel  # RH flavored distros
# brew install eccodes proj
pip install cython  # must be installed early to rebuild for newer python versions

# temporary: work around setup.cfg in the pygrib 2.0.5 tarball
export PYGRIBSETUPCFG=None
# MacOS only: XCode 12 makes this warning an error? the function is in cython-generated code
export CFLAGS="-Wno-implicit-function-declaration"

pip install pygrib
```

### am

```
curl 'https://zenodo.org/record/3406483/files/am-11.0.tgz?download=1' > am-11.0.tgz
tar xf am-11.0.tgz
cd am-11.0/src
make serial
cd ../..
export AM=./am-11.0/src/am
$AM -v
```

### this code

Once `pygrib` and `am` are installed,

```
pip install .
pip install .[test]  # if you want to run tests
pytest
```
