#!/bin/bash
# it is important for the above line to be bash and not sh

set -e

. ~/venv/eht-met-forecast/bin/activate
cd ~/github/eht-met-forecast

# die early if this isn't present or somehow won't start
export AM=./am-14.0/src/am
# -bash: -v: command not found
$AM -v > /dev/null || exit 1

export GFS=$(python scripts/print-gfs-cycle.py)

#. config-nonobs.sh
. config-2025.sh

date -u

# this will do nothing if the past was already downloaded with wait
echo downloading in the past

bash do-all.sh
echo doing plots in the past, if any
bash do-plots.sh
bash do-deploy.sh
####exit 0  # only download in the past, past plots

date -u

# the rest of the script is for when we are observing
# incremental download, slack notifications

#GREGif echo $GFS | grep -q 12:00:00; then
#GREG  python scripts/slack-post.py eht ehtobs_bots "1200UT weather download starting, should finish around 1720UT"
#GREG  DEST=~/github/eht-met-data
#GREG  WATCHFILE=$DEST/Aa/$GFS
#GREG  python scripts/download-watcher.py $WATCHFILE &
#GREG  jobs -l
#GREG  disown -a
#GREG  jobs -l
#GREGfi

echo downloading latest with wait
FLUSH="--flush Aa" WAIT=--wait bash do-all.sh

#GREGif echo $GFS | grep -q 12:00:00; then
#GREG  python scripts/slack-post.py eht ehtobs_bots "1200UT weather download finished, charts in another 30 minutes"
#GREGfi

echo doing plots
bash do-plots.sh
bash do-deploy.sh

if echo $GFS | grep -q 00:00:00; then
  python scripts/slack-post.py eht ehtobs_bots "<https://wiki.ehtcc.org/~glindahl/eht-met-plots/latest/|0000UT weather charts are available>"
fi
if echo $GFS | grep -q 06:00:00; then
  python scripts/slack-post.py eht ehtobs_bots "<https://wiki.ehtcc.org/~glindahl/eht-met-plots/latest/|0600UT weather charts are available>"
fi
if echo $GFS | grep -q 12:00:00; then
  python scripts/slack-post.py eht ehtobs_bots "<https://wiki.ehtcc.org/~glindahl/eht-met-plots/latest/|1200UT weather charts are available>"
fi
if echo $GFS | grep -q 18:00:00; then
  python scripts/slack-post.py eht ehtobs_bots "<https://wiki.ehtcc.org/~glindahl/eht-met-plots/latest/|1800UT weather charts are available>"
fi

date -u

