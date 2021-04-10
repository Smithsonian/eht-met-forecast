python scripts/scott.py --verbose --plotdir ./eht-met-plots/ 384 &
python scripts/scott.py --verbose --plotdir ./eht-met-plots/ 120 &

# also change in do-deploy.sh
EHT2021="Nn:Pv:Gl:Ax:Aa:Kt:Mg:Sw:Mm:Sz"

rm -f tau225.txt
wget https://vlbimon1.science.ru.nl/img/plots/tau225.txt

python scripts/lindy.py --vex e21[abcde]*.vex e2_[f].vex --emphasize $EHT2021 --start 2021:04:09 --end 2021:04:20 &

wait

