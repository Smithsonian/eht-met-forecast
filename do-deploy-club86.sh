# also change in do-plots.sh
#EHT2021="Nn:Pv:Gl:Ax:Aa:Kt:Mg:Sw:Mm:Sz"
#EHT2022DR="Nn:Pv:Gl:Ax:Aa:Kt:Mg:Sw:Mm:Sz:Lm"
#EHT2022="Nn:Pv:Gl:Ax:Aa:Kt:Mg:Sw:Mm:Sz:Lm"
#EHT2023DR="Nn:Gl:Aa:Sw:Mm:Lm"
#EHT2023="Nn:Gl:Ax:Aa:Kt:Mg:Sw:Mm:Sz:Lm"

python scripts/make-jumbo-webpage.py --emphasize $EMPHASIZE --plotdir $PLOTS --template index-club86.html.template

rm -f $PLOTS/latest
LATEST_TIME=`cd $PLOTS/ && ls -d 202* | tail -n 1`
(cd $PLOTS/ && ln -s $LATEST_TIME latest)
rm -f $PLOTS/latest/lindy_00.png
(cd $PLOTS/latest/ && ln -s lindy_00_$LATEST_TIME.png lindy_00.png)
rm -f $PLOTS/latest/lindy_00e.png
(cd $PLOTS/latest/ && ln -s lindy_00e_$LATEST_TIME.png lindy_00e.png)
rm -f $PLOTS/latest/lindy_00w.png
(cd $PLOTS/latest/ && ln -s lindy_00w_$LATEST_TIME.png lindy_00w.png)
rm -f $PLOTS/latest/lindy_00wg.png
(cd $PLOTS/latest/ && ln -s lindy_00wg_$LATEST_TIME.png lindy_00wg.png)
rm -f $PLOTS/latest/lindy_00p.png
(cd $PLOTS/latest/ && ln -s lindy_00p_$LATEST_TIME.png lindy_00p.png)

# this is eht-work ... the homedirs are mounted using NFS so this rsync can be
# done to any eht cloud server
rsync -av $PLOTS/ $UPLOAD:public_html/$PLOTS/

# Lindy sometimes wants to access this data, so keep it up-to-date
#ssh $UPLOAD "cd eht-met-data && git pull"

# hint: https://wiki.ehtcc.org/~glindahl/$PLOTS/latest
