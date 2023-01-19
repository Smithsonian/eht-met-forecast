# Annual Observation Stuff

## Before the Dress Rehearsal

* update glob in ../eht-met-data/commit-finished.sh to this year
* update glob in scripts/make-jumbo-webpage.py to this year
* check Scott Paine's AM software for new version -- if so be sure it passes "make test"
* check https://github.com/Smithsonian/sma-met-forecast for checkins / bugfixes -- none in 2022
* update list of stations and dates -- both DR and observation, in *.sh
* comment out the early exit in weatherwrapper.sh, so that plots and deploys are active
* edit gfs.py to reduce RETRY_DELAY from 60 to 5 and RATELIMIT_DELAY from 60 to 5
* change cronjobs to PST for the DR and then PDT for the run
* (unless the cronjob has moved to a machine in UTC (sigh))
* Get the DR schedule from the eht-wiki

## Before the Annual Observation

* Update list of stations and dates in *.sh
* Download the real schedule from eht-wiki, updating it again before the first go/no-go

## After the Annual Observation

* edit *.sh to restore the early "exit 0" to do only the download in the past
* restore gfs.py to the standard retry/ratelimit 60s

