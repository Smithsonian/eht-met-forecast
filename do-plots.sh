python scripts/scott.py --verbose --plotdir ./eht-met-plots/ 384
python scripts/scott.py --verbose --plotdir ./eht-met-plots/ 120

EHT2021="Nn:Pv:Gl:Ax:Aa:Kt:Mg:Sw:Mm:Sz"

python scripts/lindy.py --vex e21[abcd]*.vex --emphasize $EHT2021 --start 2021:04:09 --end 2021:04:20

python scripts/make-jumbo-webpage.py --emphasize $EHT2021

rm -f eht-met-plots/latest
(cd eht-met-plots/ && ln -s `ls | tail -n 1` latest)

rsync -av eht-met-plots/ glindahl@35.199.60.65:public_html/eht-met-plots/

ssh glindahl@35.199.60.65 "cd eht-met-data && git pull"

# hint: https://wiki.ehtcc.org/~glindahl/eht-met-plots/latest
