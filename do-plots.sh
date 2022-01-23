date -u

# this data directory should be the checked in data, with no partial files
DATA=~/github/eht-met-data-prod

(cd $DATA && git pull)

python scripts/scott.py --verbose --plotdir ./eht-met-plots/ --datadir $DATA 384 &
python scripts/scott.py --verbose --plotdir ./eht-met-plots/ --datadir $DATA 120 &

# also change in do-deploy.sh
#EHT2021="Nn:Pv:Gl:Ax:Aa:Kt:Mg:Sw:Mm:Sz"
EHT2022DR="Nn:Pv:Gl:Ax:Aa:Kt:Mg:Sw:Mm:Sz:Lm"
START=2022:01:25  # in UT. in EST and PST the start is 24... looking forward to confusion!
END=2022:01:28
VEX=dr2022-schedules/e22*.vex

# XXX look at the first line to rename this file by date
rm -f tau225.txt
wget https://vlbimon1.science.ru.nl/img/plots/tau225.txt

python scripts/lindy.py --vex $VEX --emphasize $EHT2022DR --start $START --end $END --datadir $DATA &

wait
date -u

