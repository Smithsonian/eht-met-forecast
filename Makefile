.PHONY: test test_coverage

am:
	curl 'https://zenodo.org/record/3406483/files/am-11.0.tgz?download=1' > am-11.0.tgz
	#curl 'https://zenodo.org/record/5794524/files/am-12.0.tgz?download=1' > am-12.0.tgz

test:
	AM=am-11.0/src/am PYTHONPATH=. pytest -v -v

test_coverage:
	AM=am-11.0/src/am PYTHONPATH=. pytest --cov-report=xml --cov=eht_met_forecast -v -v
