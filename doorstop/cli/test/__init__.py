#!/usr/bin/env python

"""
Integration tests for the doorstop.cli package.
"""

import unittest
from unittest.mock import patch, Mock

import os
import shutil
import tempfile
from distutils import dir_util  # TODO: pylint: disable=E0611

from scripttest import TestFileEnvironment

from doorstop.cli.main import main

ROOT = os.path.join(os.path.dirname(__file__), '..', '..', '..')

ENV = 'TEST_INTEGRATION'  # environment variable to enable integration tests
REASON = "'{0}' variable not set".format(ENV)


# TODO: should each command have its own class?
@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestCLI(unittest.TestCase):  # pylint: disable=R0904
    """Integration tests for the Doorstop CLI."""

    def test_main(self):
        """Verify the main CLI logic can be called."""
        self.assertIs(None, main([]))

    def test_main_help(self):
        """Verify the main CLI help text can be requested."""
        self.assertRaises(SystemExit, main, ['--help'])

    def test_main_error(self):
        """Verify the main CLI logic returns an error in an empty directory."""
        cwd = os.getcwd()
        temp = tempfile.mkdtemp()
        os.chdir(temp)
        try:
            self.assertRaises(SystemExit, main, [])
        finally:
            os.chdir(cwd)
            shutil.rmtree(temp)

    def test_new(self):
        """Verify the 'new' command can be called."""
        temp = tempfile.mkdtemp()
        try:
            self.assertIs(None, main(['new', '_TEMP', temp, '-p', 'REQ']))
        finally:
            shutil.rmtree(temp)

    def test_new_error(self):
        """Verify the 'new' command returns an error with an unknown parent."""
        temp = tempfile.mkdtemp()
        try:
            self.assertRaises(SystemExit, main,
                              ['new', '_TEMP', temp, '-p', 'UNKNOWN'])
        finally:
            shutil.rmtree(temp)

    def test_add(self):  # TODO: implement test
        """Verify the 'add' command can be called."""
        self.assertRaises(NotImplementedError, main, ['add'])

    def test_remove(self):  # TODO: implement test
        """Verify the 'remove' command can be called."""
        self.assertRaises(NotImplementedError, main, ['remove'])

    @patch('doorstop.core.processor._open')
    def test_edit(self, mock_open):
        """Verify the 'edit' command can be called."""
        self.assertIs(None, main(['edit', 'tut2']))
        path = os.path.join(ROOT, 'reqs', 'tutorial', 'TUT002.yml')
        mock_open.assert_called_once_with(os.path.normpath(path))

    def test_edit_error(self):
        """Verify the 'edit' command returns an error with an unknown ID."""
        self.assertRaises(SystemExit, main, ['edit', 'req9999'])

    def test_import(self):  # TODO: implement test
        """Verify the 'import' command can be called."""
        self.assertRaises(NotImplementedError, main, ['import', 'PATH'])

    def test_export(self):  # TODO: implement test
        """Verify the 'export' command can be called."""
        self.assertRaises(NotImplementedError, main, ['export', 'PATH'])

    def test_report(self):  # TODO: implement test
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


# TODO: is this class needed?
@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestExecutable(unittest.TestCase):  # pylint: disable=R0904
    """Integration tests for the Doorstop CLI executable."""

    @classmethod
    def setUpClass(cls):
        if os.getenv(ENV):
            cls.TEMP = tempfile.mkdtemp()
            path = os.path.join(cls.TEMP, '.scripttest')
            cls.ENV = TestFileEnvironment(path)
            os.makedirs(os.path.join(path, '.sgdrawer'))
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
