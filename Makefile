PROJECT := $(patsubst ./%.sublime-project,%, $(shell find . -type f -name '*.sublime-p*'))
PACKAGE := $(patsubst ./%/__init__.py,%, $(shell find . -maxdepth 2 -name '__init__.py'))
SOURCES := Makefile setup.py $(shell find $(PACKAGE) -name '*.py')

ENV := env
DEPENDS_CI := $(ENV)/.depends.ci
DEPENDS_DEV := $(ENV)/.depends.dev
EGG_INFO := $(subst -,_,$(PROJECT)).egg-info

PLATFORM := $(shell python -c 'import sys; print(sys.platform)')

ifneq ($(findstring win32, $(PLATFORM)), )
	SYS_PYTHON := C:\\Python33\\python.exe
	SYS_VIRTUALENV := C:\\Python33\\Scripts\\virtualenv.exe
	BIN := $(ENV)/Scripts
	EXE := .exe
	OPEN := cmd /c start
	# https://bugs.launchpad.net/virtualenv/+bug/449537
	export TCL_LIBRARY=C:\\Python33\\tcl\\tcl8.5
else
	SYS_PYTHON := python3
	SYS_VIRTUALENV := virtualenv
	BIN := $(ENV)/bin
	ifneq ($(findstring cygwin, $(PLATFORM)), )
		OPEN := cygstart
	else
		OPEN := open
	endif
endif

MAN := man
SHARE := share

PYTHON := $(BIN)/python$(EXE)
PIP := $(BIN)/pip$(EXE)
RST2HTML := $(BIN)/rst2html.py
PDOC := $(BIN)/pdoc
PEP8 := $(BIN)/pep8$(EXE)
PEP257 := $(BIN)/pep257
PYLINT := $(BIN)/pylint$(EXE)
NOSE := $(BIN)/nosetests$(EXE)

# Installation ###############################################################

.PHONY: all
all: env

.PHONY: env
env: .virtualenv $(EGG_INFO)
$(EGG_INFO): Makefile setup.py
	$(PYTHON) setup.py develop
	touch $(EGG_INFO)  # flag to indicate package is installed

.PHONY: .virtualenv
.virtualenv: $(PIP)
$(PIP):
	$(SYS_VIRTUALENV) --python $(SYS_PYTHON) $(ENV)

.PHONY: depends
depends: .depends-ci .depends-dev

.PHONY: .depends-ci
.depends-ci: .virtualenv Makefile $(DEPENDS_CI)
$(DEPENDS_CI): Makefile
	$(PIP) install pep8 pep257 nose coverage
	touch $(DEPENDS_CI)  # flag to indicate dependencies are installed

.PHONY: .depends-dev
.depends-dev: .virtualenv Makefile $(DEPENDS_DEV)
$(DEPENDS_DEV): Makefile
	$(PIP) install docutils pdoc pylint wheel
	touch $(DEPENDS_DEV)  # flag to indicate dependencies are installed

# Documentation ##############################################################

.PHONY: doc
doc: readme apidocs req

.PHONY: readme
readme: .depends-ci docs/README-github.html docs/README-pypi.html
docs/README-github.html: README.md
	pandoc -f markdown_github -t html -o docs/README-github.html README.md
docs/README-pypi.html: README.rst
	$(PYTHON) $(RST2HTML) README.rst docs/README-pypi.html
README.rst: README.md
	pandoc -f markdown_github -t rst -o README.rst README.md

.PHONY: apidocs
apidocs: .depends-ci apidocs/$(PACKAGE)/index.html
apidocs/$(PACKAGE)/index.html: $(SOURCES)
	$(PYTHON) $(PDOC) --html --overwrite $(PACKAGE) --html-dir apidocs

.PHONY: req
req: env docs/gen/*.gen.*
docs/gen/*.gen.*: */*/*.yml */*/*/*.yml */*/*/*/*.yml
	$(BIN)/doorstop
	- mkdir docs/gen
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
	$(OPEN) docs/README-pypi.html
	$(OPEN) docs/README-github.html

# Static Analysis ############################################################

.PHONY: pep8
pep8: env .depends-ci
	$(PEP8) $(PACKAGE) --ignore=E501

.PHONY: pep257
pep257: env .depends-ci
	$(PEP257) $(PACKAGE) --ignore=E501,D102

.PHONY: pylint
pylint: env .depends-dev
	$(PYLINT) $(PACKAGE) --reports no \
	                     --msg-template="{msg_id}:{line:3d},{column}:{msg}" \
	                     --max-line-length=79 \
	                     --disable=I0011,W0142,W0511,R0801

.PHONY: check
check: pep8 pep257 pylint

# Testing ####################################################################

.PHONY: test
test: env .depends-ci
	$(NOSE)

.PHONY: tests
tests: env .depends-ci
	TEST_INTEGRATION=1 $(NOSE) --verbose --stop --cover-package=$(PACKAGE)

.PHONY: tutorial
tutorial: env
	$(PYTHON) $(PACKAGE)/cli/test/test_tutorial.py

.PHONY: ci
ci: req pep8 test tests

# Cleanup ####################################################################

.PHONY: clean
clean: .clean-dist .clean-test .clean-doc .clean-build

.PHONY: clean-all
clean-all: clean .clean-env

.PHONY: .clean-env
.clean-env:
	rm -rf $(ENV)

.PHONY: .clean-build
.clean-build:
	find $(PACKAGE) -name '*.pyc' -delete
	find $(PACKAGE) -name '__pycache__' -delete
	rm -rf *.egg-info

.PHONY: .clean-doc
.clean-doc:
	rm -rf apidocs docs/README*.html README.rst

.PHONY: .clean-test
.clean-test:
	rm -rf .coverage

.PHONY: .clean-dist
.clean-dist:
	rm -rf dist build

# Release ####################################################################

.PHONY: .git-no-changes
.git-no-changes:
	@if git diff --name-only --exit-code;         \
	then                                          \
		echo Git working copy is clean...;        \
	else                                          \
		echo ERROR: Git working copy is dirty!;   \
		echo Commit your changes and try again.;  \
		exit -1;                                  \
	fi;

.PHONY: dist
dist: .git-no-changes env depends check test tests doc
	$(PYTHON) setup.py sdist
	$(PYTHON) setup.py bdist_wheel
	$(MAKE) read

.PHONY: upload
upload: .git-no-changes env depends doc
	$(PYTHON) setup.py register sdist upload
	$(PYTHON) setup.py bdist_wheel upload
	$(MAKE) dev  # restore the development environment

.PHONY: dev
dev:
	python setup.py develop

# Execution ##################################################################

.PHONY: gui
gui: env
	$(BIN)/$(PACKAGE)-gui$(EXE)
