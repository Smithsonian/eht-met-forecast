#!/bin/bash
# it is important for the above line to be bash and not sh

set -e

. ~/venv/eht-met-forecast/bin/activate
cd ~/github/eht-met-forecast

rm -f tau225.txt

RETRIES="--waitretry=1m -t 60"  # linear backoff, this is a total of 30 minutes
#RETRY_THINGS="--retry-connrefused --retry-on-http-error=404 --retry-on-http-error=500 --retry-on-http-error=502"  # needs more recent wget than I have
RETRY_THINGS="--retry-connrefused"
wget $RETRY_THINGS $RETRIES https://vlbimon1.science.ru.nl/img/plots/tau225.txt > /dev/null

if [ ! -f tau225.txt ]; then
  wget $RETRY_THINGS $RETRIES https://vlbimon2.science.ru.nl/img/plots/tau225.txt > /dev/null
fi

if [ ! -f tau225.txt ]; then
  echo "All download attempts failed" >&2
  exit 1
fi

cat tau225.txt | sed 's/:/ /' > tau225.txt.fixed
mv tau225.txt.fixed tau225.txt

python scripts/copy-to-timpstamped-name.py tau225.txt
