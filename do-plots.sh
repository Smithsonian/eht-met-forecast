python scripts/scott.py --verbose --plotdir ./eht-met-plots/ 384 &
python scripts/scott.py --verbose --plotdir ./eht-met-plots/ 120 &

EHT2021="Nn:Pv:Gl:Ax:Aa:Kt:Mg:Sw:Mm:Sz"

rm -f tau225.txt
wget https://vlbimon1.science.ru.nl/img/plots/tau225.txt

python scripts/lindy.py --vex e21[abcde]*.vex e2_[f].vex --emphasize $EHT2021 --start 2021:04:09 --end 2021:04:20 &

wait

python scripts/make-jumbo-webpage.py --emphasize $EHT2021

rm -f eht-met-plots/latest
LATEST_TIME=`cd eht-met-plots/ && ls -d 202* | tail -n 1`
(cd eht-met-plots/ && ln -s $LATEST_TIME latest)
rm -f eht-met-plots/latest/lindy_00.png
(cd eht-met-plots/latest/ && ln -s lindy_00_$LATEST_TIME.png lindy_00.png)

rsync -av eht-met-plots/ glindahl@35.199.60.65:public_html/eht-met-plots/

ssh glindahl@35.199.60.65 "cd eht-met-data && git pull"

# hint: https://wiki.ehtcc.org/~glindahl/eht-met-plots/latest
