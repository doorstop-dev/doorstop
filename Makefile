# Project settings
PROJECT := Doorstop
PACKAGE := doorstop

# Project paths
PACKAGES := $(PACKAGE)
CONFIG := $(wildcard *.py)
MODULES := $(wildcard $(PACKAGE)/*.py)

# Virtual environment paths
VIRTUAL_ENV ?= .venv

# MAIN TASKS ##################################################################

.PHONY: all
all: doctor format check test mkdocs demo ## Run all tasks that determine CI status

.PHONY: dev
dev: install .clean-test ## Continuously run all CI tasks when files chanage
	poetry run sniffer

.PHONY: dev-install
dev-install: install
	poetry build
	pip install --force dist/doorstop*.whl

.PHONY: run ## Start the program
run: install
	poetry run python $(PACKAGE)/gui/main.py

.PHONY: demo
demo: install
	poetry run python $(PACKAGE)/cli/tests/tutorial.py

# SYSTEM DEPENDENCIES #########################################################

.PHONY: doctor
doctor:  ## Confirm system dependencies are available
	bin/verchew

# PROJECT DEPENDENCIES ########################################################

DEPENDENCIES := $(VIRTUAL_ENV)/.poetry-$(shell bin/checksum pyproject.toml poetry.lock)

.PHONY: install
install: $(DEPENDENCIES) .cache

$(DEPENDENCIES): poetry.lock
	@ rm -rf ~/Library/Preferences/pypoetry
	@ poetry config virtualenvs.in-project true
	poetry install
	@ touch $@

ifndef CI
poetry.lock: pyproject.toml
	poetry lock --no-update
	@ touch $@
endif

.cache:
	@ mkdir -p .cache

# CHECKS ######################################################################

.PHONY: format
format: install
	poetry run isort $(PACKAGES)
	poetry run black $(PACKAGES)
	@ echo

.PHONY: check
check: install format  ## Run formaters, linters, and static analysis
ifdef CI
	git diff --exit-code -- '***.py'
endif
	poetry run mypy $(PACKAGES) --config-file=.mypy.ini
	poetry run pylint $(PACKAGES) --rcfile=.pylint.ini
	poetry run pydocstyle $(PACKAGES) $(CONFIG)

# TESTS #######################################################################

RANDOM_SEED ?= $(shell date +%s)

PYTEST_OPTIONS := --doctest-modules
ifndef DISABLE_COVERAGE
PYTEST_OPTIONS += --cov=$(PACKAGE) --cov-report=html --cov-report=term-missing
endif
ifdef CI
PYTEST_OPTIONS += --cov-report=xml
endif

.PHONY: test
test: test-all ## Run unit and integration tests

.PHONY: test-unit
test-unit: install
	poetry run pytest $(PACKAGE) $(PYTEST_OPTIONS)
ifndef DISABLE_COVERAGE
	@ echo
	poetry run coveragespace update unit
endif

.PHONY: test-int
test-int: test-all

.PHONY: test-all
test-all: install
	TEST_INTEGRATION=true poetry run pytest $(PACKAGES) $(PYTEST_OPTIONS)
ifndef DISABLE_COVERAGE
	@ echo
	poetry run coveragespace update overall
endif

.PHONY: test-cover
test-cover: install
# Run first to generate coverage data current code.
	TEST_INTEGRATION=true poetry run pytest doorstop --doctest-modules --cov=doorstop --cov-report=xml --cov-report=term-missing
# Run second to generate coverage data for the code in the develop branch.
	TEST_INTEGRATION=true diff-cover ./coverage.xml --compare-branch=$(shell git for-each-ref --sort=-committerdate refs/heads/develop | cut -f 1 -d ' ')

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

docs/requirements.txt: poetry.lock
	@ poetry run pip list --format=freeze | grep mkdocs > $@
	@ poetry run pip list --format=freeze | grep Pygments >> $@

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
reqs: doorstop reqs-html reqs-latex reqs-md reqs-pdf reqs-txt

.PHONY: reqs-html
reqs-html: install docs/gen/*.html
docs/gen/*.html: $(YAML)
	$(DOORSTOP) publish all docs/gen --html

.PHONY: reqs-latex
reqs-latex: install docs/gen/*.tex
docs/gen/*.tex: $(YAML)
	$(DOORSTOP) publish all docs/gen --latex

.PHONY: reqs-md
reqs-md: install docs/gen/*.md
docs/gen/*.md: $(YAML)
	$(DOORSTOP) publish all docs/gen --markdown

.PHONY: reqs-pdf
reqs-pdf: reqs-latex
	cd docs/gen && ./compile.sh

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
	poetry run pyinstaller doorstop.spec        --noconfirm --clean
	poetry run pyinstaller doorstop-gui.spec    --noconfirm --clean
	poetry run pyinstaller doorstop-server.spec --noconfirm --clean

$(PROJECT).spec:
	@# The modules mdx_outline and mdx_math are not used in doorstop through import statements,
	@# instead they are imported as markdown extensions. So these are explicitly referenced
	@# here as "hidden-imports" so that pyinstaller will pick them up.
	poetry run pyi-makespec doorstop/cli/main.py    --onefile --windowed --name=doorstop --hidden-import=mdx_outline --hidden-import=mdx_math
	@# To include additional data files in the doorstop executable built by pyinstaller
	@# they can be added to pyi-makespec using "--add-data", but that seems to become
	@# platform dependent according to the pyi-makespec documentation, so a sed command
	@# is used here to directly insert the data file names into the spec file.
	sed 's/datas=\[/datas=\[("doorstop\/views", "doorstop\/views"), ("doorstop\/core\/files", "doorstop\/core\/files")/' --in-place doorstop.spec
	poetry run pyi-makespec doorstop/gui/main.py    --onefile --windowed --name=doorstop-gui
	poetry run pyi-makespec doorstop/server/main.py --onefile --windowed --name=doorstop-server

# RELEASE #####################################################################

.PHONY: upload
upload: dist ## Upload the current version to PyPI
	git diff --name-only --exit-code
	poetry publish
	bin/open https://pypi.org/project/$(PROJECT)

# CLEANUP #####################################################################

.PHONY: clean
clean: .clean-dev-install .clean-build .clean-docs .clean-test .clean-install ## Delete all generated and temporary files

.PHONY: clean-all
clean-all: clean
	rm -rf $(VIRTUAL_ENV)

.PHONY: .clean-install
.clean-install:
	find $(PACKAGES) -name '__pycache__' | xargs rm -rf
	rm -rf *.egg-info

.PHONY: .clean-dev-install
.clean-dev-install:
	- pip uninstall --yes dist/doorstop*.whl

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
help: install
	@ grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
