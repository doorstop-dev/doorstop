PROJECT := Doorstop
PACKAGE := doorstop
SOURCES := Makefile setup.py

CACHE := .cache
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
all: develop

.PHONY: develop
develop: .env $(EGG_INFO)
$(EGG_INFO): $(SOURCES)
	$(PYTHON) setup.py develop
	touch $(EGG_INFO)  # flag to indicate package is installed

.PHONY: .env
.env: $(PIP)
$(PIP):
	virtualenv --python $(VERSION) $(VIRTUALENV)

.PHONY: depends
depends: .env $(DEPENDS) $(SOURCES)
$(DEPENDS):
	$(PIP) install docutils pdoc pep8 pylint nose coverage wheel \
	       --use-mirrors --download-cache=$(CACHE)
	touch $(DEPENDS)  # flag to indicate dependencies are installed

# Documentation ##############################################################

.PHONY: req
req: develop
	$(BIN)/doorstop
	$(BIN)/doorstop publish REQ docs/gen/Requirements.gen.txt
	$(BIN)/doorstop publish TUT docs/gen/Tutorials.gen.txt
	$(BIN)/doorstop publish HLT docs/gen/HighLevelTests.gen.txt
	$(BIN)/doorstop publish LLT docs/gen/LowLevelTests.gen.txt
	$(BIN)/doorstop publish REQ docs/gen/Requirements.gen.html
	$(BIN)/doorstop publish TUT docs/gen/Tutorials.gen.html
	$(BIN)/doorstop publish HLT docs/gen/HighLevelTests.gen.html
	$(BIN)/doorstop publish LLT docs/gen/LowLevelTests.gen.html

.PHONY: doc
doc: depends
	$(PYTHON) $(RST2HTML) README.rst docs/README.html
	$(PYTHON) $(PDOC) --html --overwrite $(PACKAGE) --html-dir apidocs
	$(MAKE) req

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
	$(MAKE) doc
	$(MAKE) pep8
	$(MAKE) pylint

# Testing ####################################################################

.PHONY: test
test: develop depends
	$(NOSE)

.PHONY: tests
tests: develop depends
	TEST_INTEGRATION=1 $(NOSE) --verbose --stop --cover-package=$(PACKAGE)

.PHONY: tutorial
tutorial: develop
	$(PYTHON) $(PACKAGE)/cli/test/test_tutorial.py

# Cleanup ####################################################################

.PHONY: .clean-env
.clean-env:
	rm -rf $(VIRTUALENV)

.PHONY: .clean-dist
.clean-dist:
	rm -rf dist build *.egg-info 

.PHONY: clean
clean: .clean-env .clean-dist
	rm -rf */*.pyc */*/*.pyc */*/*/*.pyc */*/*/*/*.pyc
	rm -rf */__pycache__ */*/__pycache__ */*/*/__pycache__ */*/*/*/__pycache__
	rm -rf apidocs docs/README.html docs/gen/* .coverage

.PHONY: clean-all
clean-all: clean
	rm -rf $(CACHE)

# Release ####################################################################

.PHONY: dist
dist: develop depends
	$(PYTHON) setup.py sdist
	$(PYTHON) setup.py bdist_wheel

.PHONY: upload
upload: develop depends
	$(PYTHON) setup.py register sdist upload
	$(PYTHON) setup.py bdist_wheel upload	

# Execution ##################################################################

.PHONY: gui
gui: develop
	$(BIN)/$(PACKAGE)-gui$(EXE)
