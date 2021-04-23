#!/bin/bash
# it is important for the above line to be bash and not sh

. ~/venv/eht-met-forecast/bin/activate
export AM=./am-11.0/src/am

cd ~/github/eht-met-forecast

date

# first download anything in the past
bash do-all.sh

date

# now wait for the next one
# turn this one when we're running
#WAIT=--wait bash do-all.sh

date

