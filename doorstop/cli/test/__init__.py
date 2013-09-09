#!/usr/bin/env python

"""
Integration tests for the doorstop.cli package.
"""

import unittest

import os
import tempfile
from distutils import dir_util

from scripttest import TestFileEnvironment

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

ENV = 'TEST_INTEGRATION'  # environment variable to enable integration tests
REASON = "'{0}' variable not set".format(ENV)


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestCLI(unittest.TestCase):  # pylint: disable=R0904
    """Integration tests for the Doorstop CLI."""

    @classmethod
    def setUpClass(cls):
        if os.getenv(ENV):
            cls.TEMP = tempfile.mkdtemp()
            dir_util.copy_tree(ROOT, cls.TEMP)
            cls.ENV = TestFileEnvironment(os.path.join(cls.TEMP, '.scripttest'))
            if os.name == 'nt':
                cls.BIN = os.path.join(ROOT, 'Scripts', 'doorstop.exe')
            else:
                cls.BIN = os.path.join(ROOT, 'bin', 'doorstop')

    @classmethod
    def tearDownClass(cls):
        if os.getenv(ENV):
            dir_util.remove_tree(cls.TEMP)

    def cli(self, *args, **kwargs):
        """Call the CLI with arguments."""
        return self.ENV.run(self.BIN, *args, **kwargs)

    def test_main(self):
        """Verify the main CLI can be called."""
        result = self.cli(expect_error=True)
        self.assertNotEqual(0, result.returncode)  # TODO: fix the CLI
