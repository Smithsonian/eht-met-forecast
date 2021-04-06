#!/bin/bash

DEST=~/github/eht-met-data

$AM -v || exit 1

TIME=192

STATIONS="Aa Ax BAJA BOL GAM Gl HAY Kt LAS Lm Mg Mm Nn OVRO PIKES Pv Sw Sz VLA VLT"

for vex in $STATIONS; do
   eht-met-forecast --backfill $TIME --dir $DEST --vex $vex &
done

wait

(cd $DEST && bash ./commit-finished.sh)

