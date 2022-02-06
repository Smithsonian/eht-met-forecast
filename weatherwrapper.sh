#!/bin/bash
# it is important for the above line to be bash and not sh

. ~/venv/eht-met-forecast/bin/activate
export AM=./am-12.0/src/am

cd ~/github/eht-met-forecast

date -u

echo downloading in the past

bash do-all.sh

date -u

# turn this on when we're running
#echo downloading latest with wait
#WAIT=--wait bash do-all.sh

#echo doing plots
#bash do-plots.sh

# now we'd like to notify Greg and/or slack, BUT, only for the run starting at 01 UT

date -u

