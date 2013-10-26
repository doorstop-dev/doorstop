#!/usr/bin/env python

"""
Integration tests for the doorstop.cli package.
"""

import unittest
from unittest.mock import patch, Mock

import os
import tempfile
from distutils import dir_util  # TODO: pylint: disable=E0611

from scripttest import TestFileEnvironment

from doorstop.cli.main import main

ROOT = os.path.join(os.path.dirname(__file__), '..', '..', '..')

ENV = 'TEST_INTEGRATION'  # environment variable to enable integration tests
REASON = "'{0}' variable not set".format(ENV)


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestCLI(unittest.TestCase):  # pylint: disable=R0904
    """Integration tests for the Doorstop CLI."""

    def test_main(self):
        """Verify the main CLI logic can be called."""
        self.assertIs(None, main([]))

    def test_main_help(self):
        """Verify the main CLI help text can be requested."""
        self.assertRaises(SystemExit, main, ['--help'])

    def test_main_new(self):
        """Verify the 'new' command can be called."""
        self.assertRaises(NotImplementedError, main, ['new'])

    def test_main_add(self):
        """Verify the 'add' command can be called."""
        self.assertRaises(NotImplementedError, main, ['add'])

    def test_main_remove(self):
        """Verify the 'remove' command can be called."""
        self.assertRaises(NotImplementedError, main, ['remove'])

    def test_main_import(self):
        """Verify the 'import' command can be called."""
        self.assertRaises(NotImplementedError, main, ['import', 'PATH'])

    def test_main_export(self):
        """Verify the 'export' command can be called."""
        self.assertRaises(NotImplementedError, main, ['export', 'PATH'])

    def test_main_report(self):
        """Verify the 'report' command can be called."""
        self.assertRaises(NotImplementedError, main, ['report', 'PATH'])

    @patch('doorstop.cli.main._run', Mock(return_value=False))
    def test_exit(self):
        """Verify an error code is returned on errors."""
        self.assertRaises(SystemExit, main, [])

    @patch('doorstop.cli.main._run', Mock(side_effect=KeyboardInterrupt))
    def test_interrupt(self):
        """Verify an error code is returned on interrupts."""
        self.assertRaises(SystemExit, main, [])


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestExecutable(unittest.TestCase):  # pylint: disable=R0904
    """Integration tests for the Doorstop CLI executable."""

    @classmethod
    def setUpClass(cls):
        if os.getenv(ENV):
            cls.TEMP = tempfile.mkdtemp()
            cls.ENV = TestFileEnvironment(os.path.join(cls.TEMP, '.scripttest'))
            if os.name == 'nt':
                cls.BIN = os.path.join(ROOT, 'env', 'Scripts', 'doorstop.exe')
            else:
                cls.BIN = os.path.join(ROOT, 'env', 'bin', 'doorstop')

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
        self.assertIn("doorstop", result.stderr)

    def test_doorstop_new(self):
        """Verify 'doorstop new' can be called."""
        result = self.cli('new', expect_error=True)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("doorstop new", result.stderr)

    def test_doorstop_add(self):
        """Verify 'doorstop add --item' can be called."""
        result = self.cli('add', '--item', expect_error=True)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("doorstop add", result.stderr)

    def test_doorstop_remove(self):
        """Verify 'doorstop remove --item <?>' can be called."""
        result = self.cli('remove', '--item', 'R1', expect_error=True)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("doorstop remove", result.stderr)

    def test_doorstop_import(self):
        """Verify 'doorstop import <?>' can be called."""
        result = self.cli('import', 'PATH', expect_error=True)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("doorstop import", result.stderr)

    def test_doorstop_export(self):
        """Verify 'doorstop export <?>' can be called."""
        result = self.cli('export', 'PATH', expect_error=True)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("doorstop export", result.stderr)

    def test_doorstop_report(self):
        """Verify 'doorstop report <?>' can be called."""
        result = self.cli('report', 'PATH', expect_error=True)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("doorstop report", result.stderr)


@patch('doorstop.cli.main._run', Mock(return_value=True))  # pylint: disable=R0904
class TestLogging(unittest.TestCase):  # pylint: disable=R0904
    """Integration tests for the Doorstop CLI logging."""

    def test_verbose_1(self):
        """Verify verbose level 1 can be set."""
        self.assertIs(None, main(['-v']))

    def test_verbose_2(self):
        """Verify verbose level 2 can be set."""
        self.assertIs(None, main(['-v', '-v']))

    def test_verbose_3(self):
        """Verify verbose level 1 can be set."""
        self.assertIs(None, main(['-v', '-v', '-v']))
