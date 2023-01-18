# also change in do-plots.sh
#EHT2021="Nn:Pv:Gl:Ax:Aa:Kt:Mg:Sw:Mm:Sz"
#EHT2022DR="Nn:Pv:Gl:Ax:Aa:Kt:Mg:Sw:Mm:Sz:Lm"
#EHT2022="Nn:Pv:Gl:Ax:Aa:Kt:Mg:Sw:Mm:Sz:Lm"
EHT2023DR="Nn:Gl:Aa:Sw:Mm:Lm"
EHT2023="Nn:Gl:Ax:Aa:Kt:Mg:Sw:Mm:Sz:Lm"

python scripts/make-jumbo-webpage.py --emphasize $EHT2023DR

rm -f eht-met-plots/latest
LATEST_TIME=`cd eht-met-plots/ && ls -d 202* | tail -n 1`
(cd eht-met-plots/ && ln -s $LATEST_TIME latest)
rm -f eht-met-plots/latest/lindy_00.png
(cd eht-met-plots/latest/ && ln -s lindy_00_$LATEST_TIME.png lindy_00.png)
rm -f eht-met-plots/latest/lindy_00e.png
(cd eht-met-plots/latest/ && ln -s lindy_00e_$LATEST_TIME.png lindy_00e.png)
rm -f eht-met-plots/latest/lindy_00w.png
(cd eht-met-plots/latest/ && ln -s lindy_00w_$LATEST_TIME.png lindy_00w.png)
rm -f eht-met-plots/latest/lindy_00wg.png
(cd eht-met-plots/latest/ && ln -s lindy_00wg_$LATEST_TIME.png lindy_00wg.png)
rm -f eht-met-plots/latest/lindy_00p.png
(cd eht-met-plots/latest/ && ln -s lindy_00p_$LATEST_TIME.png lindy_00p.png)

# this is eht-work ... the homedirs are mounted using NFS so this rsync can be
# done to any eht cloud server
rsync -av eht-met-plots/ glindahl@35.199.60.65:public_html/eht-met-plots/

# Lindy sometimes wants to access this data, so keep it up-to-date
ssh glindahl@35.199.60.65 "cd eht-met-data && git pull"

# hint: https://wiki.ehtcc.org/~glindahl/eht-met-plots/latest
