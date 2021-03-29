#!/bin/bash

DEST=~/github/eht-met-data

$AM -v || exit 1

eht-met-forecast --backfill 48 --dir $DEST --stations stations.jsonl --vex Aa &
eht-met-forecast --backfill 48 --dir $DEST --stations stations.jsonl --vex Ax &
eht-met-forecast --backfill 48 --dir $DEST --stations stations.jsonl --vex BAJA &
eht-met-forecast --backfill 48 --dir $DEST --stations stations.jsonl --vex BOL &
eht-met-forecast --backfill 48 --dir $DEST --stations stations.jsonl --vex GAM &
eht-met-forecast --backfill 48 --dir $DEST --stations stations.jsonl --vex Gl &
eht-met-forecast --backfill 48 --dir $DEST --stations stations.jsonl --vex HAY &
eht-met-forecast --backfill 48 --dir $DEST --stations stations.jsonl --vex Kp &
eht-met-forecast --backfill 48 --dir $DEST --stations stations.jsonl --vex LAS &
eht-met-forecast --backfill 48 --dir $DEST --stations stations.jsonl --vex Lm &
eht-met-forecast --backfill 48 --dir $DEST --stations stations.jsonl --vex Mg &
eht-met-forecast --backfill 48 --dir $DEST --stations stations.jsonl --vex Mm &
eht-met-forecast --backfill 48 --dir $DEST --stations stations.jsonl --vex Nq &
eht-met-forecast --backfill 48 --dir $DEST --stations stations.jsonl --vex OVRO &
eht-met-forecast --backfill 48 --dir $DEST --stations stations.jsonl --vex PIKES &
eht-met-forecast --backfill 48 --dir $DEST --stations stations.jsonl --vex Pv &
eht-met-forecast --backfill 48 --dir $DEST --stations stations.jsonl --vex Sw &
eht-met-forecast --backfill 48 --dir $DEST --stations stations.jsonl --vex Sz &
eht-met-forecast --backfill 48 --dir $DEST --stations stations.jsonl --vex VLA &
eht-met-forecast --backfill 48 --dir $DEST --stations stations.jsonl --vex VLT &

wait

(cd $DEST && bash ./commit-finished.sh)

