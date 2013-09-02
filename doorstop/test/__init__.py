"""
Unit tests for the doorstop package.
"""

import unittest

import os
import tempfile
import shutil

from scripttest import TestFileEnvironment

ENV = 'TEST_INTEGRATION'  # environment variable to enable integration tests
REASON = "'{0}' variable not set".format(ENV)


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestAPI(Integration):  # pylint: disable=R0904
    """Integration tests for the Doorstop API."""


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestCLI(Integration):  # pylint: disable=R0904
    """Integration tests for the Doorstop CLI."""

    @classmethod
    def setUpClass(cls):
        cls.TEMP = tempfile.mkdtemp()
        os.rmdir(cls.TEMP)
        shutil.copytree('..', cls.TEMP)
        cls.ENV = TestFileEnvironment(os.path.join(cls.TEMP, '.scripttest'))
        cls.BIN = (os.path.join('..', 'Scripts', 'doorstop.exe') if os.name == 'nt' else
                   os.path.join(',,', 'bin', 'doorstop'))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.TEMP)

    def cli(self, *args):
        """Call the CLI with arguments."""
        return self.ENV.run(self.BIN, *args)

    def test_main(self):
        """Verify the main CLI can be called."""
        result = self.cli()
        self.assertNotEqual(0, result.returncode)  # TODO: fix the CLI
