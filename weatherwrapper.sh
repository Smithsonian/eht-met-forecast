#!/bin/bash
# it is important for the above line to be bash and not sh

. ~/venv/eht-met-forecast/bin/activate
cd ~/github/eht-met-forecast

# die early if this isn't present or somehow won't start
export AM=./am-12.2/src/am
# -bash: -v: command not found
$AM -v > /dev/null || exit 1

date -u

# this will do nothing if the past was already downloaded with wait
echo downloading in the past

bash do-all.sh
#echo doing plots, if any
#bash do-plots.sh
#bash do-deploy.sh

date -u

# turn this on when we're running
#echo downloading latest with wait
#WAIT=--wait bash do-all.sh

#echo doing plots
#bash do-plots.sh
#bash do-deploy.sh

# now we'd like to notify Greg and/or slack, BUT, only for the run starting at 01 UT

date -u

