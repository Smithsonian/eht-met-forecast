#!/bin/bash
# it is important for the above line to be bash and not sh

set -e

. ~/venv/eht-met-forecast/bin/activate
cd ~/github/eht-met-forecast

# die early if this isn't present or somehow won't start
export AM=./am-12.2/src/am
# -bash: -v: command not found
$AM -v > /dev/null || exit 1

export GFS=$(python scripts/print-gfs-cycle.py)

. config-2024dr.sh

date -u

# this will do nothing if the past was already downloaded with wait
echo downloading in the past

bash do-all.sh
#exit 0  # download in the past, no plots
echo doing plots in the past, if any
bash do-plots.sh
bash do-deploy.sh
exit 0  # download in the past, yes plots

date -u

# the rest of the script is for when we are observing
# incremental download, slack notifications

if echo $GFS | grep -q 12:00:00; then
  python scripts/slack-post.py eht ehtobs_bots "1200UT weather download starting, should finish around 1720UT"
  DEST=~/github/eht-met-data
  WATCHFILE=$DEST/Aa/$GFS
  python scripts/download-watcher.py $WATCHFILE &
  jobs -l
  disown -a
  jobs -l
fi

echo downloading latest with wait
FLUSH="--flush Aa" WAIT=--wait bash do-all.sh

if echo $GFS | grep -q 12:00:00; then
  python scripts/slack-post.py eht ehtobs_bots "1200UT weather download finished, charts in another 20 minutes"
fi

echo doing plots
bash do-plots.sh
bash do-deploy.sh

if echo $GFS | grep -q 06:00:00; then
  python scripts/slack-post.py eht ehtobs_bots "<https://wiki.ehtcc.org/~glindahl/eht-met-plots/latest/|0600UT weather charts are available>"
fi
if echo $GFS | grep -q 12:00:00; then
  python scripts/slack-post.py eht ehtobs_bots "<https://wiki.ehtcc.org/~glindahl/eht-met-plots/latest/|1200UT weather charts are available>"
fi

date -u

