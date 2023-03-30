date -u

# this data directory should be the checked in data, with no partial files
DATA=~/github/eht-met-data-prod

(cd $DATA && git pull)

python scripts/scott.py --verbose --plotdir ./eht-met-plots/ --datadir $DATA 384 &
python scripts/scott.py --verbose --plotdir ./eht-met-plots/ --datadir $DATA 120 &

python scripts/lindy.py --vex $VEX --emphasize $EMPHASIZE --start $START --end $END --datadir $DATA &

wait
date -u

