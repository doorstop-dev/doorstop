#!/usr/bin/env python

"""
Integration tests for the doorstop.cli package.
"""

import unittest

import os
import tempfile
from distutils import dir_util  # TODO: pylint: disable=E0611

from scripttest import TestFileEnvironment

from doorstop.cli.main import main

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

ENV = 'TEST_INTEGRATION'  # environment variable to enable integration tests
REASON = "'{0}' variable not set".format(ENV)


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestCLI(unittest.TestCase):  # pylint: disable=R0904
    """Integration tests for the Doorstop CLI."""

    def test_main(self):
        """Verify the main CLI logic can be called."""
        self.assertRaises(NotImplementedError, main, [])

    def test_main_help(self):
        """Verify the main CLI help text can be requested."""
        self.assertRaises(SystemExit, main, ['--help'])

    def test_main_new(self):
        """Verify the new command can be called."""
        self.assertRaises(NotImplementedError, main, ['new'])


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestExecutable(unittest.TestCase):  # pylint: disable=R0904
    """Integration tests for the Doorstop CLI executable."""

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

    def test_doorstop(self):
        """Verify 'doorstop' can be called."""
        result = self.cli(expect_error=True)
        self.assertNotEqual(0, result.returncode)

    def test_doorstop_new(self):
        """Verify 'doorstop new' can be called."""
        result = self.cli('new', expect_error=True)
        self.assertNotEqual(0, result.returncode)

    def test_doorstop_add(self):
        """Verify 'doorstop add' can be called."""
        result = self.cli('add', expect_error=True)
        self.assertNotEqual(0, result.returncode)

    def test_doorstop_remove(self):
        """Verify 'doorstop remove' can be called."""
        result = self.cli('remove', expect_error=True)
        self.assertNotEqual(0, result.returncode)

    def test_doorstop_import(self):
        """Verify 'doorstop import' can be called."""
        result = self.cli('import', expect_error=True)
        self.assertNotEqual(0, result.returncode)

    def test_doorstop_export(self):
        """Verify 'doorstop export' can be called."""
        result = self.cli('import', expect_error=True)
        self.assertNotEqual(0, result.returncode)
