"""
Integration tests for the doorstop.core package.
"""

import unittest

import os

from scripttest import TestFileEnvironment

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

ENV = 'TEST_INTEGRATION'  # environment variable to enable integration tests
REASON = "'{0}' variable not set".format(ENV)


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestAPI(unittest.TestCase):  # pylint: disable=R0904
    """Integration tests for the Doorstop API."""

    pass
