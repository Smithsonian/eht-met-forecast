date -u

(cd $DATA && git pull)

python scripts/scott.py --verbose --plotdir ./eht-met-plots/ --datadir $DATA 384 &
python scripts/scott.py --verbose --plotdir ./eht-met-plots/ --datadir $DATA 120 &

python scripts/lindy.py $VEX --emphasize $EMPHASIZE --start "$START" --end "$END" --datadir $DATA &

wait
date -u

