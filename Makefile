.PHONY: test test_coverage

test:
	AM=am-11.0/src/am PYTHONPATH=. pytest -v -v

test_coverage:
	AM=am-11.0/src/am PYTHONPATH=. pytest --cov-report=xml --cov=eht_met_forecast -v -v
