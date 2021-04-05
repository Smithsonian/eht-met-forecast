#!/bin/bash

DEST=~/github/eht-met-data

$AM -v || exit 1

TIME=192

STATIONS="Aa Ax BAJA BOL GAM Gl HAY Kp LAS Lm Mg Mm Nq OVRO PIKES Pv Sw Sz VLA VLT"

for vex in $STATIONS; do
   eht-met-forecast --backfill $TIME --dir $DEST --stations stations.jsonl --vex $vex &
done

wait

(cd $DEST && bash ./commit-finished.sh)

