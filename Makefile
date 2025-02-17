# Variables
SOURCE = xzar

all: lint unit

deps:
	pip3 install -U pip
	pip3 install .[dev]

lint:
	@echo Linting source code...
	ruff check $(SOURCE) test
	@echo

format:
	@echo Formatting source code
	ruff format $(SOURCE) test
	@echo

unit:
	@echo Running unit tests...
	pytest -svvv
	@echo
