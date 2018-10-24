test:
	pytest
	behave

coverage:
	pytest --cov=abaqus2dyna --cov-report html --cov-config=.coveragerc
	mv coverage/.coverage coverage/.coverage.pytest
	coverage run -m behave -k --tags=unit
	mv coverage/.coverage coverage/.coverage.behave
	coverage combine coverage
	coverage report

.PHONY: test coverage
