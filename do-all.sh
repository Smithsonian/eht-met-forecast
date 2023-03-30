#!/bin/bash

# better set lower during an observation
# if too large, the oldest ones see http 302 (redir)
BACKFILL=168

# use during an observation -- normally set in weatherwrapper.sh
#WAIT="--wait"
#FLUSH="--flush Aa"

for vex in $STATIONS; do
   eht-met-forecast --backfill $BACKFILL --dir $DEST --vex $vex $WAIT $FLUSH --log LOG &
done

wait

(cd $DEST && bash ./commit-finished.sh)

ssh $UPLOAD "cd eht-met-data && git pull"
