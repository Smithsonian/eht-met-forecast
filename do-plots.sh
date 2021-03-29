python scripts/scott.py --verbose --outputdir ./eht-met-plots/ 384
python scripts/scott.py --verbose --outputdir ./eht-met-plots/ 120
python scripts/lindy.py --vex e21n24.vex --emphasize Nq:Pv:Gl:Kp:Mg

python scripts/make-jumbo-webpage.py

rm -f eht-met-plots/latest
(cd eht-met-plots/ && ln -s `ls | tail -n 1` latest)

rsync -av eht-met-plots/ glindahl@35.199.60.65:public_html/eht-met-plots/

# hint: https://wiki.ehtcc.org/~glindahl/eht-met-plots/latest
