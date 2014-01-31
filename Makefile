PROJECT := Doorstop
PACKAGE := doorstop
SOURCES := Makefile setup.py

VIRTUALENV := env
DEPENDS := $(VIRTUALENV)/.depends
EGG_INFO := $(subst -,_,$(PROJECT)).egg-info

ifeq ($(OS),Windows_NT)
	VERSION := C:\\Python33\\python.exe
	BIN := $(VIRTUALENV)/Scripts
	EXE := .exe
	OPEN := cmd /c start
	# https://bugs.launchpad.net/virtualenv/+bug/449537
	export TCL_LIBRARY=C:\\Python33\\tcl\\tcl8.5
else
	VERSION := python3
	BIN := $(VIRTUALENV)/bin
	OPEN := open
endif
MAN := man
SHARE := share

PYTHON := $(BIN)/python$(EXE)
PIP := $(BIN)/pip$(EXE)
RST2HTML := $(BIN)/rst2html.py
PDOC := $(BIN)/pdoc
PEP8 := $(BIN)/pep8$(EXE)
PYLINT := $(BIN)/pylint$(EXE)
NOSE := $(BIN)/nosetests$(EXE)

# Installation ###############################################################

.PHONY: all
all: env

.PHONY: env
env: .virtualenv $(EGG_INFO)
$(EGG_INFO): $(SOURCES)
	$(PYTHON) setup.py develop
	touch $(EGG_INFO)  # flag to indicate package is installed

.PHONY: .virtualenv
.virtualenv: $(PIP)
$(PIP):
	virtualenv --python $(VERSION) $(VIRTUALENV)

.PHONY: depends
depends: .virtualenv $(DEPENDS) Makefile
$(DEPENDS):
	$(PIP) install docutils pdoc pep8 pylint nose coverage wheel
	touch $(DEPENDS)  # flag to indicate dependencies are installed

# Documentation ##############################################################

.PHONY: doc
doc: readme apidocs req

.PHONY: readme
readme: depends docs/README.html
docs/README.html: README.rst
	$(PYTHON) $(RST2HTML) README.rst docs/README.html

.PHONY: apidocs
apidocs: depends apidocs/$(PACKAGE)/index.html
apidocs/$(PACKAGE)/index.html: $(SOURCES)
	$(PYTHON) $(PDOC) --html --overwrite $(PACKAGE) --html-dir apidocs

.PHONY: req
req: env docs/gen/*.gen.*
docs/gen/*.gen.*: */*/*.yml */*/*/*.yml */*/*/*/*.yml
	$(BIN)/doorstop
	$(BIN)/doorstop publish REQ docs/gen/Requirements.gen.txt
	$(BIN)/doorstop publish TUT docs/gen/Tutorials.gen.txt
	$(BIN)/doorstop publish HLT docs/gen/HighLevelTests.gen.txt
	$(BIN)/doorstop publish LLT docs/gen/LowLevelTests.gen.txt
	$(BIN)/doorstop publish REQ docs/gen/Requirements.gen.html
	$(BIN)/doorstop publish TUT docs/gen/Tutorials.gen.html
	$(BIN)/doorstop publish HLT docs/gen/HighLevelTests.gen.html
	$(BIN)/doorstop publish LLT docs/gen/LowLevelTests.gen.html

.PHONY: read
read: doc
	$(OPEN) docs/gen/LowLevelTests.gen.html
	$(OPEN) docs/gen/HighLevelTests.gen.html
	$(OPEN) docs/gen/Tutorials.gen.html
	$(OPEN) docs/gen/Requirements.gen.html
	$(OPEN) apidocs/$(PACKAGE)/index.html
	$(OPEN) docs/README.html

# Static Analysis ############################################################

.PHONY: pep8
pep8: depends
	$(PEP8) $(PACKAGE) --ignore=E501 

.PHONY: pylint
pylint: depends
	$(PYLINT) $(PACKAGE) --reports no \
	                     --msg-template="{msg_id}:{line:3d},{column}:{msg}" \
	                     --max-line-length=79 \
	                     --disable=I0011,W0142,W0511,R0801

.PHONY: check
check: depends
	$(MAKE) pep8
	$(MAKE) pylint

# Testing ####################################################################

.PHONY: test
test: env depends
	$(NOSE)

.PHONY: tests
tests: env depends
	TEST_INTEGRATION=1 $(NOSE) --verbose --stop --cover-package=$(PACKAGE)

.PHONY: tutorial
tutorial: env
	$(PYTHON) $(PACKAGE)/cli/test/test_tutorial.py

# Cleanup ####################################################################

.PHONY: clean
clean: .clean-dist .clean-test .clean-doc .clean-build

.PHONY: clean-all
clean-all: clean .clean-env 

.PHONY: .clean-env
.clean-env:
	rm -rf $(VIRTUALENV)

.PHONY: .clean-build
.clean-build:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete
	rm -rf *.egg-info

.PHONY: .clean-doc
.clean-doc:
	rm -rf apidocs docs/README*.html

.PHONY: .clean-test
.clean-test:
	rm -rf .coverage

.PHONY: .clean-dist
.clean-dist:
	rm -rf dist build

# Release ####################################################################

.PHONY: dist
dist: env depends check test tests doc
	$(PYTHON) setup.py sdist
	$(PYTHON) setup.py bdist_wheel
	$(MAKE) read
 
.PHONY: upload
upload: env depends doc
	$(PYTHON) setup.py register sdist upload
	$(PYTHON) setup.py bdist_wheel upload
	$(MAKE) dev  # restore the development environemnt

.PHONY: dev
dev:
	python setup.py develop
	
# Execution ##################################################################

.PHONY: gui
gui: env
	$(BIN)/$(PACKAGE)-gui$(EXE)
