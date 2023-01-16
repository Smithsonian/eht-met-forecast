#!/bin/bash
# it is important for the above line to be bash and not sh

. ~/venv/eht-met-forecast/bin/activate
cd ~/github/eht-met-forecast

rm tau225.txt

RETRIES="--waitretry=1m -t 60"  # linear backoff, this is a total of 30 minutes
#RETRY_THINGS="--retry-connrefused --retry-on-http-error=404 --retry-on-http-error=500 --retry-on-http-error=502"  # needs more recent wget than I have
RETRY_THINGS="--retry-connrefused"
wget $RETRY_THINGS $RETRIES https://vlbimon1.science.ru.nl/img/plots/tau225.txt > /dev/null

python scripts/copy-to-timpstamped-name.py tau225.txt
