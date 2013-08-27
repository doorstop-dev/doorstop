"""
Unit tests for the doorstop package.
"""

import unittest

import os

ENV = 'TEST_INTEGRATION'  # environment variable to enable integration tests


@unittest.skipUnless(os.getenv(ENV), "'{0}' variable not set".format(ENV))  # pylint: disable=R0904
class Integration(unittest.TestCase):
    """Base class for integration tests."""


class TestAPI(Integration):
    """Integration tests for the Doorstop API."""


class TestCLI(Integration):
    """Integration tests for the Doorstop CLI."""
