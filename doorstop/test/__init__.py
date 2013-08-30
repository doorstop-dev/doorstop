"""
Unit tests for the doorstop package.
"""

import unittest

import os

ENV = 'TEST_INTEGRATION'  # environment variable to enable integration tests


@unittest.skipUnless(os.getenv(ENV), "'{0}' variable not set".format(ENV))  # pylint: disable=R0904
class Integration(unittest.TestCase):  # pylint: disable=R0904
    """Base class for integration tests."""


class TestAPI(Integration):  # pylint: disable=R0904
    """Integration tests for the Doorstop API."""


class TestCLI(Integration):  # pylint: disable=R0904
    """Integration tests for the Doorstop CLI."""
