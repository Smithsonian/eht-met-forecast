#!/bin/bash

DEST=~/github/eht-met-data

$AM -v || exit 1

BACKFILL=24

#WAIT="--wait"
#WAIT=""

STATIONS="Aa Ax BAJA BOL GAM Gl HAY Kt LAS Lm Mg Mm Nn OVRO PIKES Pv Sw Sz VLA VLT"

for vex in $STATIONS; do
   eht-met-forecast --backfill $BACKFILL --dir $DEST --vex $vex $WAIT &
done

wait

(cd $DEST && bash ./commit-finished.sh)

ssh glindahl@35.199.60.65 "cd eht-met-data && git pull"
