date -u

# this data directory should be the checked in data, with no partial files
DATA=~/github/eht-met-data-prod

(cd $DATA && git pull)

python scripts/scott.py --verbose --plotdir ./eht-met-plots/ --datadir $DATA 384 &
python scripts/scott.py --verbose --plotdir ./eht-met-plots/ --datadir $DATA 120 &

# also change in do-deploy.sh
#EHT2021="Nn:Pv:Gl:Ax:Aa:Kt:Mg:Sw:Mm:Sz"
EHT2022="Nn:Pv:Gl:Ax:Aa:Kt:Mg:Sw:Mm:Sz:Lm"
START=2022:03:17  # in UT. It's the 16th in EDT.
#START=2022:03:11  # in UT. It's the 10th in EDT. Special weather for Alma fringe test.
END=2022:03:28
VEX=2022-schedules/trak?.vex

# XXX look at the first line to rename this file by date
rm -f tau225.txt
wget https://vlbimon1.science.ru.nl/img/plots/tau225.txt
# wget will prevent overwrites, giving us a history
#wget https://vlbimon1.science.ru.nl/img/plots/tau225.txt.archive

python scripts/lindy.py --vex $VEX --emphasize $EHT2022 --start $START --end $END --datadir $DATA &

wait
date -u

