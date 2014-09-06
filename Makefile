# Project settings (detected automatically from files/directories)
PROJECT := $(patsubst ./%.sublime-project,%, $(shell find . -type f -name '*.sublime-p*'))
PACKAGE := $(patsubst ./%/__init__.py,%, $(shell find . -maxdepth 2 -name '__init__.py'))
SOURCES := Makefile setup.py $(shell find $(PACKAGE) -name '*.py')
EGG_INFO := $(subst -,_,$(PROJECT)).egg-info

# virtualenv settings
ENV := env

# Flags for PHONY targets
DEPENDS_CI := $(ENV)/.depends-ci
DEPENDS_DEV := $(ENV)/.depends-dev
ALL := $(ENV)/.all

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
		SUDO := sudo
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
PYREVERSE := $(BIN)/pyreverse
NOSE := $(BIN)/nosetests

# Main Targets ###############################################################

.PHONY: all
all: $(ALL)
$(ALL): $(SOURCES)
	$(MAKE) doc pep8 pep257
	touch $(ALL)  # flag to indicate all setup steps were successful

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
	$(PIP) install --upgrade pep8 pep257 nose coverage
	touch $(DEPENDS_CI)  # flag to indicate dependencies are installed

.PHONY: .depends-dev
.depends-dev: env Makefile $(DEPENDS_DEV)
$(DEPENDS_DEV): Makefile
	$(PIP) install --upgrade docutils pdoc pylint wheel sphinx
	touch $(DEPENDS_DEV)  # flag to indicate dependencies are installed

# Development Usage ##########################################################

.PHONY: doorstop
doorstop: env
	$(BIN)/doorstop --warn-all --error-all --quiet

.PHONY: gui
gui: env
	$(BIN)/doorstop-gui

.PHONY: serve
serve: env
	$(SUDO) $(BIN)/doorstop-server --debug --launch --port 80

# Documentation ##############################################################

.PHONY: doc
doc: readme reqs uml apidocs sphinx

.PHONY: pages
pages: reqs-html sphinx
	cp -r docs/gen/ pages/reqs/
	cp -r docs/sphinx/_build pages/docs/

.PHONY: readme
readme: .depends-dev docs/README-github.html docs/README-pypi.html
docs/README-github.html: README.md
	pandoc -f markdown_github -t html -o docs/README-github.html README.md
docs/README-pypi.html: README.rst
	$(PYTHON) $(RST2HTML) README.rst docs/README-pypi.html
README.rst: README.md
	pandoc -f markdown_github -t rst -o README.rst README.md

.PHONY: reqs
reqs: doorstop reqs-html reqs-md reqs-txt

.PHONY: reqs-html
reqs-html: env docs/gen/*.html
docs/gen/*.html: $(shell find . -name '*.yml' -not -path '*/test/files/*')
	$(BIN)/doorstop publish all docs/gen --html

.PHONY: reqs-md
reqs-md: env docs/gen/*.md
docs/gen/*.md: $(shell find . -name '*.yml' -not -path '*/test/files/*')
	$(BIN)/doorstop publish all docs/gen --markdown

.PHONY: reqs-txt
reqs-txt: env docs/gen/*.txt
docs/gen/*.txt: $(shell find . -name '*.yml' -not -path '*/test/files/*')
	$(BIN)/doorstop publish all docs/gen --text

.PHONY: uml
uml: .depends-dev docs/*.png $(SOURCES)
docs/*.png:
	$(PYREVERSE) $(PACKAGE) -p $(PACKAGE) -f ALL -o png --ignore test
	- mv -f classes_$(PACKAGE).png docs/classes.png
	- mv -f packages_$(PACKAGE).png docs/packages.png

.PHONY: apidocs
apidocs: .depends-ci apidocs/$(PACKAGE)/index.html
apidocs/$(PACKAGE)/index.html: $(SOURCES)
	$(PYTHON) $(PDOC) --html --overwrite $(PACKAGE) --html-dir apidocs

.PHONY: sphinx
sphinx: .depends-dev docs/sphinx/_build
docs/sphinx/_build: $(SOURCES)
	$(BIN)/sphinx-apidoc -o docs/sphinx/ doorstop
	$(BIN)/sphinx-build -b html docs/sphinx docs/sphinx/_build
	touch docs/sphinx/_build  # flag to indicate sphinx docs generated

.PHONY: read
read: doc
	$(OPEN) docs/gen/index.html
	$(OPEN) apidocs/$(PACKAGE)/index.html
	$(OPEN) docs/sphinx/_build/index.html
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
	$(PEP257) $(PACKAGE) --ignore=D102

.PHONY: pylint
pylint: .depends-dev
	$(PYLINT) $(PACKAGE) --rcfile=.pylintrc

# Testing ####################################################################

.PHONY: test
test: .depends-ci
	$(NOSE) --config=.noserc

.PHONY: tests
tests: .depends-ci
	TEST_INTEGRATION=1 $(NOSE) --config=.noserc --cover-package=$(PACKAGE) -xv

.PHONY: tutorial
tutorial: env
	$(PYTHON) $(PACKAGE)/cli/test/test_tutorial.py

# Cleanup ####################################################################

.PHONY: clean
clean: .clean-dist .clean-test .clean-doc .clean-build
	rm -rf $(ALL)

.PHONY: clean-all
clean-all: clean .clean-env

.PHONY: .clean-env
.clean-env:
	rm -rf $(ENV)

.PHONY: .clean-build
.clean-build:
	find . -name '*.pyc' -not -path "*/env/*" -delete
	find . -name '__pycache__' -not -path "*/env/*" -delete
	rm -rf *.egg-info

.PHONY: .clean-doc
.clean-doc:
	rm -rf apidocs docs/README*.html README.rst docs/*.png docs/gen
	rm -rf docs/sphinx/doorstop*.rst docs/sphinx/_build
	rm -rf pages/docs/ pages/reqs/

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
	python3 setup.py develop

.PHONY: install
install:
	python3 setup.py install

.PHONY: download
download:
	pip install $(PROJECT)
