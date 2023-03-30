date -u

# this data directory should be the checked in data, with no partial files
DATA=~/github/eht-met-data-prod

(cd $DATA && git pull)

python scripts/scott.py --verbose --plotdir ./eht-met-plots/ --datadir $DATA 384 &
python scripts/scott.py --verbose --plotdir ./eht-met-plots/ --datadir $DATA 120 &

# also change in do-deploy.sh
#EHT2021="Nn:Pv:Gl:Ax:Aa:Kt:Mg:Sw:Mm:Sz"
#EHT2022="Nn:Pv:Gl:Ax:Aa:Kt:Mg:Sw:Mm:Sz:Lm"
#EHT2023DR="Nn:Gl:Aa:Sw:Mm:Lm"
#EHT2023="Nn:Gl:Ax:Aa:Kt:Mg:Sw:Mm:Sz:Lm"
#START=2022:03:17  # in UT. It's the 16th in EDT.
#START=2022:03:11  # in UT. It's the 10th in EDT. Special weather for Alma fringe test.
#END=2022:03:28
#START=2023:01:16  # in UT.
#END=2023:01:19
#VEX=dr2023-schedules/*.vex
# eht wiki url https://eht-wiki.haystack.mit.edu/
# https://eht-wiki.haystack.mit.edu/Event_Horizon_Telescope_Home/Observing/2023_Dress_Rehearsal

python scripts/lindy.py --vex $VEX --emphasize $EMPHASIZE --start $START --end $END --datadir $DATA &

wait
date -u

