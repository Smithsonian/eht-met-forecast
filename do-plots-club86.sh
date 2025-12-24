date -u

echo pulling
(cd $DATA && git pull)

python scripts/scott.py --verbose --plotdir $PLOTS/ --datadir $DATA --stations "$STATIONS" 384 &
python scripts/scott.py --verbose --plotdir $PLOTS/ --datadir $DATA --stations "$STATIONS" 120 &

python scripts/lindy-club86.py $VEX --emphasize $EMPHASIZE --start "$START" --end "$END" --datadir $DATA --stations "$STATIONS" --plotdir $PLOTS &

wait
date -u

