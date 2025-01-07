.PHONY: am11 am12 am12.2 am13 am 14 check_slack test test_coverage

am11:
	curl 'https://zenodo.org/record/3406483/files/am-11.0.tgz?download=1' > am-11.0.tgz
	tar xf am-11.0.tgz
	cd am-11.0/src && make serial && ./am -v

am12:
	curl 'https://zenodo.org/record/5794524/files/am-12.0.tgz?download=1' > am-12.0.tgz
	tar xf am-12.0.tgz
	cd am-12.0/src && make serial && ./am -v

am12.2:
	curl 'https://zenodo.org/record/6774378/files/am-12.2.tgz?download=1' > am-12.2.tgz
	tar xf am-12.2.tgz
	cd am-12.2/src && make serial && ./am -v

am13:
	curl 'https://zenodo.org/records/8161261/files/am-13.0.tgz?download=1' > am-13.0.tgz
	tar xf am-13.0.tgz
	cd am-13.0/src && make serial && ./am -v

am14:
	curl 'https://zenodo.org/records/13748403/files/am-14.0.tgz?download=1' > am-14.0.tgz
	tar xf am-14.0.tgz
	cd am-14.0/src && make serial && ./am -v

check_slack:
	jq . ~/.slack-secrets

eht_met_forecast/data/stations.json: scripts/stations-to-geodetic.py
	python scripts/stations-to-geodetic.py > eht_met_forecast/data/stations.json

test:
	AM=am-14.0/src/am PYTHONPATH=. pytest -v -v tests/

test_coverage:
	AM=am-14.0/src/am PYTHONPATH=. pytest --cov=eht_met_forecast -v -v tests/
