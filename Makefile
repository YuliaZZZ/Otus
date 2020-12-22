activate:
	source ./venv/bin/activate

test:
	python3 -m unittest tests.py

start:
	python3 ./log_analyzer.py



.PHONY : activate test start