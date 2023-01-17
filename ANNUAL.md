# Annual Observation Stuff

## Before the Dress Rehearsal

* update ../eht-met-data/commit-finished.sh to this year
* check Scott Paine's AM software for new version -- if so be sure it passes "make test"
* check https://github.com/Smithsonian/sma-met-forecast for checkins / bugfixes -- none in 2022
* update list of stations and dates -- both DR and observation, in *.sh
* turn on plots and upload of plots
* turn on --wait
* reduce RETRY_DELAY from 60 to 5 in gfs.py
* reduce RATELIMIT_DELAY from 60 to 5 in gfs.py
* change cronjobs to PST for the DR and then PDT for the run
* (unless the cronjob has moved to a machine in UTC (sigh))
* Get the DR schedule from the eht-wiki

## Before the Annual Observation

* Double-check all *.sh
* Download the real schedule from eht-wiki, updating it again before the first go/no-go

## After the Annual Observation

* edit *.sh: turn off plots, turn off --wait, return RETRY_DELAY to 60
