# Project settings
PROJECT := Doorstop
PACKAGE := doorstop
REPOSITORY := jacebrowning/doorstop

# Project paths
PACKAGES := $(PACKAGE)
CONFIG := $(wildcard *.py)
MODULES := $(wildcard $(PACKAGE)/*.py)

# Virtual environment paths
VIRTUAL_ENV ?= .venv

# MAIN TASKS ##################################################################

.PHONY: all
all: install

.PHONY: ci
ci: format check test mkdocs demo ## Run all tasks that determine CI status

.PHONY: watch
watch: install .clean-test ## Continuously run all CI tasks when files chanage
	poetry run sniffer

.PHONY: run ## Start the program
run: install
	poetry run python $(PACKAGE)/gui/main.py

.PHONY: demo
demo: install
	poetry run python $(PACKAGE)/cli/tests/test_tutorial.py

# SYSTEM DEPENDENCIES #########################################################

.PHONY: doctor
doctor:  ## Confirm system dependencies are available
	bin/verchew

# PROJECT DEPENDENCIES ########################################################

DEPENDENCIES := $(VIRTUAL_ENV)/.poetry-$(shell bin/checksum pyproject.toml poetry.lock)

.PHONY: install
install: $(DEPENDENCIES) .cache

$(DEPENDENCIES): poetry.lock
	@ poetry config settings.virtualenvs.in-project true
	poetry install
	@ touch $@

poetry.lock: pyproject.toml
	poetry lock
	@ touch $@

.cache:
	@ mkdir -p .cache

# CHECKS ######################################################################

.PHONY: format
format: install
	poetry run isort $(PACKAGES) --recursive --apply
	# TODO: Format code using black after dropping Python 3.5 support
	# poetry run black $(PACKAGES)
	@ echo

.PHONY: check
check: install format  ## Run formaters, linters, and static analysis
ifdef CI
	git diff --exit-code
endif
	# TODO: Enable mypy for type checking
	# poetry run mypy $(PACKAGES) --config-file=.mypy.ini
	poetry run pylint $(PACKAGES) --rcfile=.pylint.ini
	poetry run pycodestyle $(PACKAGES) $(CONFIG) --config=.pycodestyle.ini
	poetry run pydocstyle $(PACKAGES) $(CONFIG)

# TESTS #######################################################################

RANDOM_SEED ?= $(shell date +%s)

NOSE_OPTIONS := --with-doctest
ifndef DISABLE_COVERAGE
NOSE_OPTIONS += --with-cov --cov=$(PACKAGE) --cov-report=html --cov-report=term-missing
endif

.PHONY: test
test: test-all ## Run unit and integration tests

.PHONY: test-unit
test-unit: install
	poetry run nosetests $(PACKAGE) $(NOSE_OPTIONS)
	poetry run coveragespace $(REPOSITORY) unit

.PHONY: test-int
test-int: test-all

.PHONY: test-all
test-all: install
	TEST_INTEGRATION=true poetry run nosetests $(PACKAGES) $(NOSE_OPTIONS) --show-skipped
	poetry run coveragespace $(REPOSITORY) overall

.PHONY: read-coverage
read-coverage:
	bin/open htmlcov/index.html

# DOCUMENTATION ###############################################################

MKDOCS_INDEX := site/index.html

.PHONY: docs
docs: mkdocs uml ## Generate documentation and UML

.PHONY: mkdocs
mkdocs: install $(MKDOCS_INDEX)
$(MKDOCS_INDEX): docs/requirements.txt mkdocs.yml docs/*.md
	@ mkdir -p docs/about
	@ cd docs && ln -sf ../README.md index.md
	@ cd docs/about && ln -sf ../../CHANGELOG.md changelog.md
	@ cd docs/about && ln -sf ../../CONTRIBUTING.md contributing.md
	@ cd docs/about && ln -sf ../../LICENSE.md license.md
	poetry run mkdocs build --clean --strict

# Workaround: https://github.com/rtfd/readthedocs.org/issues/5090
docs/requirements.txt: poetry.lock
	@ poetry run pip freeze -qqq | grep mkdocs > $@

.PHONY: uml
uml: install docs/*.png
docs/*.png: $(MODULES)
	poetry run pyreverse $(PACKAGE) -p $(PACKAGE) -a 1 -f ALL -o png --ignore tests
	- mv -f classes_$(PACKAGE).png docs/classes.png
	- mv -f packages_$(PACKAGE).png docs/packages.png

.PHONY: mkdocs-serve
mkdocs-serve: mkdocs
	eval "sleep 3; bin/open http://127.0.0.1:8000" &
	poetry run mkdocs serve

# REQUIREMENTS ################################################################

DOORSTOP := poetry run doorstop

YAML := $(wildcard */*.yml */*/*.yml */*/*/*/*.yml)

.PHONY: reqs
reqs: doorstop reqs-html reqs-md reqs-txt

.PHONY: reqs-html
reqs-html: install docs/gen/*.html
docs/gen/*.html: $(YAML)
	$(DOORSTOP) publish all docs/gen --html

.PHONY: reqs-md
reqs-md: install docs/gen/*.md
docs/gen/*.md: $(YAML)
	$(DOORSTOP) publish all docs/gen --markdown

.PHONY: reqs-txt
reqs-txt: install docs/gen/*.txt
docs/gen/*.txt: $(YAML)
	$(DOORSTOP) publish all docs/gen --text

# BUILD #######################################################################

DIST_FILES := dist/*.tar.gz dist/*.whl
EXE_FILES := dist/$(PROJECT).*

.PHONY: dist
dist: install $(DIST_FILES)
$(DIST_FILES): $(MODULES) pyproject.toml
	rm -f $(DIST_FILES)
	poetry build

.PHONY: exe
exe: install $(EXE_FILES)
$(EXE_FILES): $(MODULES) $(PROJECT).spec
	# For framework/shared support: https://github.com/yyuu/pyenv/wiki
	poetry run pyinstaller $(PROJECT).spec --noconfirm --clean

$(PROJECT).spec:
	poetry run pyi-makespec $(PACKAGE)/__main__.py --onefile --windowed --name=$(PROJECT)

# RELEASE #####################################################################

.PHONY: upload
upload: dist ## Upload the current version to PyPI
	git diff --name-only --exit-code
	poetry publish
	bin/open https://pypi.org/project/$(PROJECT)

# CLEANUP #####################################################################

.PHONY: clean
clean: .clean-build .clean-docs .clean-test .clean-install ## Delete all generated and temporary files

.PHONY: clean-all
clean-all: clean
	rm -rf $(VIRTUAL_ENV)

.PHONY: .clean-install
.clean-install:
	find $(PACKAGES) -name '__pycache__' -delete
	rm -rf *.egg-info

.PHONY: .clean-test
.clean-test:
	rm -rf .cache .pytest .coverage htmlcov

.PHONY: .clean-docs
.clean-docs:
	rm -rf docs/*.png site

.PHONY: .clean-build
.clean-build:
	rm -rf *.spec dist build

# HELP ########################################################################

.PHONY: help
help: all
	@ grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
