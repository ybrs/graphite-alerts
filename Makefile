#
# Basic makefile for general targets
#

PYTHON = python3.15
PIP = $(PYTHON) -m pip

.PHONY: test
test: unit-test integration-test acceptance-test

.PHONY: unit-test
unit-test:
	$(PYTHON) -m pytest tests/unit

.PHONY: integration-test
integration-test:
	$(PYTHON) -m pytest tests/integration

.PHONY: acceptance-test
acceptance-test:
	$(PYTHON) -m pytest tests/acceptance -v

.PHONY: tdd
tdd:
	$(PYTHON) -m pytest tests/unit -x

.PHONY: docs
docs:
	bin/sphinx-build -b html -d docs/build/doctrees docs/source docs/html

.PHONY: foreman
foreman:
	$(DEV_ENV) foreman start -f Procfile

.PHONY: develop
develop:
	$(PIP) install -e .

.PHONY: clean
clean:
	-find . -type f -name '*.pyc' -o -name '*.tar.gz' -delete
	-rm -rf build dist *.egg-info

.PHONY: dist
dist: clean
	$(PYTHON) -m build

.PHONY: upload
upload:
	$(PYTHON) -m twine upload dist/*

.PHONY: requirements
requirements:
	$(PIP) install -r local_requirements.txt

.PHONY: osx_requirements
osx_requirements:

.PHONY: virtualenv
virtualenv:
	$(PYTHON) -m venv .venv

