#!/bin/bash

STATIONS="Aa Ax BAJA BOL GAM Gl HAY Kt LAS Lm Mg Mm Nn OVRO PIKES Pv Sw Sz VLA VLT"
DEST=~/github/eht-met-data
UPLOAD=glindahl@35.199.60.65

# die early if this isn't present
$AM -v || exit 1

# better set lower during an observation
# if too large, the oldest ones see http 302 (redir)
BACKFILL=168

# use during an observation
#WAIT="--wait"

for vex in $STATIONS; do
   eht-met-forecast --backfill $BACKFILL --dir $DEST --vex $vex $WAIT --log LOG &
done

wait

(cd $DEST && bash ./commit-finished.sh)

ssh $UPLOAD "cd eht-met-data && git pull"
