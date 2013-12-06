"""
Package for the doorstop.core tests.
"""

import unittest
from unittest.mock import patch

import os


ROOT = os.path.join(os.path.dirname(__file__), '..', '..', '..')

FILES = os.path.join(os.path.dirname(__file__), 'files')
SYS = os.path.join(FILES, 'sys')
EMPTY = os.path.join(FILES, 'empty')  # an empty directory
EXTERNAL = os.path.join(FILES, 'external')  # external files to reference
NEW = os.path.join(FILES, 'new')  # new document with no items

ENV = 'TEST_INTEGRATION'  # environment variable to enable integration tests
REASON = "'{0}' variable not set".format(ENV)
