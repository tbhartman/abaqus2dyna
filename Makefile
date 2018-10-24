test:
	pytest
	behave src/abaqus2dyna/test/features/

coverage:
	pytest --cov=abaqus2dyna --cov-report html --cov-config=.coveragerc
	mv coverage/.coverage coverage/.coverage.pytest
	coverage run -m behave src/abaqus2dyna/test/features -k --tags=unit
	mv coverage/.coverage coverage/.coverage.behave
	coverage combine coverage
	coverage report

.PHONY: test coverage
