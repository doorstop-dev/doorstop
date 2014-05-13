# Project settings (detected automatically from files/directories)
PROJECT := $(patsubst ./%.sublime-project,%, $(shell find . -type f -name '*.sublime-p*'))
PACKAGE := $(patsubst ./%/__init__.py,%, $(shell find . -maxdepth 2 -name '__init__.py'))
SOURCES := Makefile setup.py $(shell find $(PACKAGE) -name '*.py')
EGG_INFO := $(subst -,_,$(PROJECT)).egg-info

# virtualenv settings
ENV := env

# Common paths
DEPENDS_CI := $(ENV)/.depends.ci
DEPENDS_DEV := $(ENV)/.depends.dev
MAN := man
SHARE := share

# OS-specific paths (detected automatically from the system Python)
PLATFORM := $(shell python -c 'import sys; print(sys.platform)')
ifneq ($(findstring win32, $(PLATFORM)), )
	SYS_PYTHON := C:\\Python34\\python.exe
	SYS_VIRTUALENV := C:\\Python34\\Scripts\\virtualenv.exe
	BIN := $(ENV)/Scripts
	OPEN := cmd /c start
	BAT := .bat
	# https://bugs.launchpad.net/virtualenv/+bug/449537
	export TCL_LIBRARY=C:\\Python34\\tcl\\tcl8.5
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

# virtualenv executables
PYTHON := $(BIN)/python
PIP := $(BIN)/pip
RST2HTML := $(BIN)/rst2html.py
PDOC := $(BIN)/pdoc
PEP8 := $(BIN)/pep8
PEP257 := $(BIN)/pep257
PYLINT := $(BIN)/pylint
PYREVERSE := $(BIN)/pyreverse$(BAT)
NOSE := $(BIN)/nosetests

# Main Targets ###############################################################

.PHONY: all
all: doc check

.PHONY: ci
ci: doorstop pep8 pep257 test tests tutorial

# Development Installation ###################################################

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
.depends-ci: env Makefile $(DEPENDS_CI)
$(DEPENDS_CI): Makefile
	$(PIP) install pep8 pep257 nose coverage
	touch $(DEPENDS_CI)  # flag to indicate dependencies are installed

.PHONY: .depends-dev
.depends-dev: env Makefile $(DEPENDS_DEV)
$(DEPENDS_DEV): Makefile
	$(PIP) install docutils pdoc pylint wheel
	touch $(DEPENDS_DEV)  # flag to indicate dependencies are installed

# Development Usage ##########################################################

.PHONY: doorstop
doorstop: env
	$(BIN)/doorstop

.PHONY: gui
gui: env
	$(BIN)/doorstop-gui

# Documentation ##############################################################

.PHONY: doc
doc: readme apidocs uml html

.PHONY: readme
readme: .depends-dev docs/README-github.html docs/README-pypi.html
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

.PHONY: uml
uml: .depends-dev docs/*.png $(SOURCES)
docs/*.png:
	$(PYREVERSE) $(PACKAGE) -p $(PACKAGE) -f ALL -o png --ignore test
	- mv -f classes_$(PACKAGE).png docs/classes.png
	- mv -f packages_$(PACKAGE).png docs/packages.png

.PHONY: html
html: env docs/gen/*.html
docs/gen/*.html: $(shell find . -name '*.yml')
	- $(MAKE) doorstop
	$(BIN)/doorstop publish all docs/gen --text
	$(BIN)/doorstop publish all docs/gen --markdown
	$(BIN)/doorstop publish all docs/gen --html

.PHONY: read
read: doc
	$(OPEN) docs/gen/index.html
	$(OPEN) apidocs/$(PACKAGE)/index.html
	$(OPEN) docs/README-pypi.html
	$(OPEN) docs/README-github.html

# Static Analysis ############################################################

.PHONY: check
check: pep8 pep257 pylint

.PHONY: pep8
pep8: .depends-ci
	$(PEP8) $(PACKAGE) --ignore=E501

.PHONY: pep257
pep257: .depends-ci
	$(PEP257) $(PACKAGE) --ignore=E501,D102

.PHONY: pylint
pylint: .depends-dev
	$(PYLINT) $(PACKAGE) --reports no \
	                     --msg-template="{msg_id}:{line:3d},{column}:{msg}" \
	                     --max-line-length=79 \
	                     --disable=I0011,W0142,W0511,R0801

# Testing ####################################################################

.PHONY: test
test: .depends-ci
	$(NOSE)

.PHONY: tests
tests: .depends-ci
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
	rm -rf $(ENV)

.PHONY: .clean-build
.clean-build:
	find $(PACKAGE) -name '*.pyc' -delete
	find $(PACKAGE) -name '__pycache__' -delete
	rm -rf *.egg-info

.PHONY: .clean-doc
.clean-doc:
	rm -rf apidocs docs/README*.html README.rst docs/*.png

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
dist: check doc test tests
	$(PYTHON) setup.py sdist
	$(PYTHON) setup.py bdist_wheel
	$(MAKE) read

.PHONY: upload
upload: .git-no-changes doc
	$(PYTHON) setup.py register sdist upload
	$(PYTHON) setup.py bdist_wheel upload

# System Installation ########################################################

.PHONY: develop
develop:
	python setup.py develop

.PHONY: install
install:
	python setup.py install

.PHONY: download
download:
	pip install $(PROJECT)
