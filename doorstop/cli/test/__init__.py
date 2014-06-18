"""Package for the doorstop.cli tests."""

import os

from doorstop.cli.main import main

ROOT = os.path.join(os.path.dirname(__file__), '..', '..', '..')
REQS = os.path.join(ROOT, 'docs', 'reqs')
TUTORIAL = os.path.join(REQS, 'tutorial')
FILES = os.path.join(os.path.dirname(__file__), 'files')

ENV = 'TEST_INTEGRATION'  # environment variable to enable integration tests
REASON = "'{0}' variable not set".format(ENV)
