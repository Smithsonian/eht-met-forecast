#!/bin/bash
# it is important for the above line to be bash and not sh

. ~/venv/eht-met-forecast/bin/activate
export AM=./am-11.0/src/am

cd ~/github/eht-met-forecast

WAIT=--wait bash do-all.sh


