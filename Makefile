# Variables
SOURCE = xzar

deps:
	pip3 install -U pip
	pip3 install .[dev]

format:
	@echo Formatting source code
	ruff format $(SOURCE)
	@echo
