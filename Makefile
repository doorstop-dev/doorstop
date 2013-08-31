PROJECT := Doorstop
PACKAGE := doorstop

EGG_INFO := $(subst -,_,$(PROJECT)).egg-info
CACHE := .cache
DEPENDS := .depends

ifeq ($(OS),Windows_NT)
VERSION := C:\\Python27\\python.exe
BIN := Scripts
INCLUDE := Include
LIB := Lib
EXE := .exe
else
VERSION := python3.3
BIN := bin
INCLUDE := include
LIB := lib
endif
MAN := man
SHARE := share

WD := $(shell pwd)
PYTHON := $(WD)/$(BIN)/python$(EXE)
PIP := $(WD)/$(BIN)/pip$(EXE)
RST2HTML := $(WD)/$(BIN)/rst2html.py
PDOC := $(WD)/$(BIN)/pdoc$(EXE)
PEP8 := $(WD)/$(BIN)/pep8$(EXE)
PYLINT := $(WD)/$(BIN)/pylint$(EXE)
NOSE := $(WD)/$(BIN)/nosetests$(EXE)

# Installation ###############################################################

.PHONY: all
all: develop check test

.PHONY: develop
develop: .env $(EGG_INFO)
$(EGG_INFO):
	$(PYTHON) setup.py develop

.PHONY: .env
.env: $(PYTHON)
$(PYTHON):
	virtualenv --python $(VERSION) .

.PHONY: depends
depends: .env $(DEPENDS)
$(DEPENDS):
	$(PIP) install docutils pdoc Pygments \
	       nose pep8 pylint --download-cache=$(CACHE)
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


doc: depends
	$(RST2HTML) README.rst docs/README.html
	# hiding the return code: https://github.com/BurntSushi/pdoc/issues/1
	- $(PDOC) --html --overwrite $(PACKAGE) --html-dir apidocs

.PHONY: doc-open
doc-open: doc
	open $(WD)/docs/README.html
	open $(WD)/apidocs/doorstop/index.html

# Static Analysis ############################################################

.PHONY: pep8
pep8: depends
	$(PEP8) $(PACKAGE) --ignore=E501 

.PHONY: pylint
pylint: depends
	$(PYLINT) $(PACKAGE) --reports no \
	                     --msg-template="{msg_id}: {msg}: {obj} line:{line}" \
	                     --max-line-length=99 \
	                     --disable=I0011,W0142,W0511,R0801

.PHONY: check
check: depends
	$(MAKE) doc
	$(MAKE) pep8
	$(MAKE) pylint

# Testing ####################################################################

.PHONY: nose
nose: develop depends
	$(NOSE)

.PHONY: test
test: nose

.PHONY: tests
tests: TEST_INTEGRATION=1
tests: nose

# Cleanup ####################################################################

.PHONY: .clean-env
.clean-env:
	rm -rf .Python $(BIN) $(INCLUDE) $(LIB) $(MAN) $(SHARE) $(DEPENDS)

.PHONY: .clean-dist
.clean-dist:
	rm -rf dist build *.egg-info 

.PHONY: clean
clean: .clean-env .clean-dist
	rm -rf */*.pyc */*/*.pyc */__pycache__ */*/__pycache__ */*/*/__pycache__
	rm -rf apidocs docs/README.html .coverage

.PHONY: clean-all
clean-all: clean
	rm -rf $(CACHE)

# Release ####################################################################

.PHONY: dist
dist: .clean-dist
	$(PYTHON) setup.py sdist

.PHONY: upload
upload: .clean-dist
	$(PYTHON) setup.py register sdist upload
