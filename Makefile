PROJECT := Doorstop
PACKAGE := doorstop
VERSION := 3.3

EGG_INFO := $(subst -,_,$(PROJECT)).egg-info
CACHE := .cache
DEPENDS := .depends

ifeq ($(OS),Windows_NT)
BIN := Scripts
INCLUDE := Include
LIB := Lib
MAN := man
EXE := .exe
else
BIN := bin
INCLUDE := include
LIB := lib
MAN := man
endif

WD := $(shell pwd)
PYTHON := $(WD)/$(BIN)/python$(EXE)
PIP := $(WD)/$(BIN)/pip$(EXE)
RST2HTML := $(WD)/$(BIN)/rst2html.py
EPYDOC := $(WD)/$(BIN)/epydoc$(EXE)
PEP8 := $(WD)/$(BIN)/pep8$(EXE)
PYLINT := $(WD)/$(BIN)/pylint$(EXE)
NOSE := $(WD)/$(BIN)/nosetests$(EXE)

# Installation ###############################################################

.PHONY: all
all: develop

.PHONY: develop
develop: .env $(EGG_INFO)
$(EGG_INFO):
	$(PYTHON) setup.py develop

.PHONY: .env
.env: $(PYTHON)
$(PYTHON):
	virtualenv --python=python$(VERSION) .

.PHONY: depends
depends: .env $(DEPENDS)
$(DEPENDS):
	$(PIP) install docutils epydoc nose pep8 pylint --download-cache=$(CACHE)
	$(MAKE) .coverage
	touch $(DEPENDS)  # flag to indicate dependencies are installed

# issue: coverage results are incorrect in Linux
# tracker: https://bitbucket.org/ned/coveragepy/issue/164
# workaround: install the latest code from bitbucket.org until "coverage>3.6"
.PHONY: .coverage
ifeq ($(shell uname),Linux)
.coverage: .env $(CACHE)/coveragepy
	cd $(CACHE)/coveragepy ;\
	$(PIP) install --requirement requirements.txt --download-cache=$(CACHE) ;\
	$(PYTHON) setup.py install
$(CACHE)/coveragepy:
	cd $(CACHE) ;\
	hg clone https://bitbucket.org/ned/coveragepy
else
.coverage: .env
	$(PIP) install coverage --download-cache=$(CACHE)
endif

# Documentation ##############################################################

.PHONY: doc
# issue: epydoc does not install a working CLI on Windows
# tracker: http://sourceforge.net/p/epydoc/bugs/345
# workaround: skip epydoc on Windows
ifeq ($(OS),Windows_NT)
doc: depends
	$(BIN)/rst2html.py README.rst docs/README.html
	@echo WARNING: epydoc cannot be run on Windows
else
doc: depends
	$(RST2HTML) README.rst docs/README.html
	$(EPYDOC) --config setup.cfg
endif

.PHONY: doc-open
doc-open: doc
	open $(WD)/docs/README.html
	open $(WD)/apidocs/index.html

# Static Analysis ############################################################

.PHONY: pep8
pep8: depends
	$(PEP8) $(PACKAGE)

.PHONY: pylint
pylint: depends
	$(PYLINT) $(PACKAGE) --reports no \
	                     --disable I0011,W0511,W0142 --max-line-length=99

.PHONY: check
check: depends
	$(MAKE) doc
	$(PEP8) --ignore=E501 $(PACKAGE)
	$(PYLINT) $(PACKAGE) --reports no --disable W0142,W0511,I0011,R,C

# Testing ####################################################################

.PHONY: nose
nose: all depends
	$(NOSE)

.PHONY: test
test: nose

.PHONY: tests
tests: TEST_INTEGRATION=1
tests: nose

# Cleanup ####################################################################

.PHONY: .clean-env
.clean-env:
	rm -rf .Python $(BIN) $(INCLUDE) $(LIB) $(MAN) $(DEPENDS) $(CACHE)

.PHONY: .clean-dist
.clean-dist:
	rm -rf dist build *.egg-info 

.PHONY: clean
clean: .clean-env .clean-dist
	rm -rf */*.pyc */*/*.pyc apidocs docs/README.html .coverage
	
# Release ####################################################################

.PHONY: dist
dist: .clean-dist
	$(PYTHON) setup.py sdist

.PHONY: upload
upload: .clean-dist
	$(PYTHON) setup.py register sdist upload
