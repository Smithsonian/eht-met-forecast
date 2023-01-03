.PHONY: test test_coverage

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

test:
	AM=am-12.0/src/am PYTHONPATH=. pytest -v -v

test_coverage:
	AM=am-12.0/src/am PYTHONPATH=. pytest --cov-report=xml --cov=eht_met_forecast -v -v
