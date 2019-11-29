# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.cli.utilities module."""

import unittest
from argparse import ArgumentTypeError
from unittest.mock import Mock, patch
from warnings import catch_warnings

from doorstop import common, settings
from doorstop.cli import utilities
from doorstop.cli.tests import SettingsTestCase


class TestCapture(unittest.TestCase):
    """Unit tests for the `Capture` class."""

    def test_success(self):
        """Verify a success can be captured."""
        with utilities.capture() as success:
            pass  # no exception raised
        self.assertTrue(success)

    def test_failure(self):
        """Verify a failure can be captured."""
        with utilities.capture() as success:
            raise common.DoorstopError
        self.assertFalse(success)

    def test_failure_uncaught(self):
        """Verify a failure can be left uncaught."""
        try:
            with utilities.capture(catch=False) as success:
                raise common.DoorstopError
        except common.DoorstopError:
            self.assertFalse(success)
        else:
            self.fail("DoorstopError not raised")


class TestConfigureSettings(SettingsTestCase):
    """Unit tests for the `configure_settings` function."""

    def test_configure_settings(self):
        """Verify settings are parsed correctly."""
        args = Mock()
        args.reorder = False
        args.beta = None
        # Act
        with catch_warnings(record=True) as warnings:
            utilities.configure_settings(args)
            assert warnings, 'Expected one or more warnings'
        # Assert
        self.assertFalse(settings.REFORMAT)
        self.assertFalse(settings.REORDER)
        self.assertFalse(settings.CHECK_LEVELS)
        self.assertFalse(settings.CHECK_REF)
        self.assertFalse(settings.CHECK_CHILD_LINKS)
        self.assertFalse(settings.PUBLISH_CHILD_LINKS)
        self.assertFalse(settings.CHECK_SUSPECT_LINKS)
        self.assertFalse(settings.CHECK_REVIEW_STATUS)
        self.assertFalse(settings.PUBLISH_BODY_LEVELS)
        self.assertFalse(settings.WARN_ALL)
        self.assertFalse(settings.ERROR_ALL)
        self.assertTrue(settings.ENABLE_HEADERS)
        self.assertIn("--no-body-levels", str(warnings[-1].message))


class TestLiteralEval(unittest.TestCase):
    """Unit tests for the `literal_eval` function."""

    def test_literal_eval(self):
        """Verify a string can be evaluated as a Python literal."""
        self.assertEqual(42.0, utilities.literal_eval("42.0"))

    def test_literal_eval_invalid_err(self):
        """Verify an invalid literal calls the error function."""
        error = Mock()
        utilities.literal_eval("1/", error=error)
        self.assertEqual(1, error.call_count)

    @patch('doorstop.cli.utilities.log.critical')
    def test_literal_eval_invalid_log(self, mock_log):
        """Verify an invalid literal logs an error."""
        utilities.literal_eval("1/")
        self.assertEqual(1, mock_log.call_count)


class TestGetExt(unittest.TestCase):
    """Unit tests for the `get_ext` function."""

    def test_get_ext_stdout_document(self):
        """Verify a default output extension can be selected."""
        args = Mock(spec=[])
        error = Mock()
        # Act
        ext = utilities.get_ext(args, error, '.out', '.file')
        # Assert
        self.assertEqual(0, error.call_count)
        self.assertEqual('.out', ext)

    def test_get_ext_stdout_document_override(self):
        """Verify a default output extension can be overridden."""
        args = Mock(spec=['html'])
        args.html = True
        error = Mock()
        # Act
        ext = utilities.get_ext(args, error, '.out', '.file')
        # Assert
        self.assertEqual(0, error.call_count)
        self.assertEqual('.html', ext)

    @patch('os.path.isdir', Mock(return_value=True))
    def test_get_ext_file_document_to_directory(self):
        """Verify a path is required for a single document."""
        args = Mock(spec=['path'])
        args.path = 'path/to/directory'
        error = Mock()
        # Act
        utilities.get_ext(args, error, '.out', '.file')
        # Assert
        self.assertNotEqual(0, error.call_count)

    def test_get_ext_file_document(self):
        """Verify a specified file extension can be selected."""
        args = Mock(spec=['path'])
        args.path = 'path/to/file.cust'
        error = Mock()
        # Act
        ext = utilities.get_ext(args, error, '.out', '.file')
        # Assert
        self.assertEqual(0, error.call_count)
        self.assertEqual('.cust', ext)

    def test_get_ext_file_tree(self):
        """Verify a specified file extension can be selected."""
        args = Mock(spec=['path'])
        args.path = 'path/to/directory'
        error = Mock()
        # Act
        ext = utilities.get_ext(args, error, '.out', '.file', whole_tree=True)
        # Assert
        self.assertEqual(0, error.call_count)
        self.assertEqual('.file', ext)

    def test_get_ext_file_document_no_extension(self):
        """Verify an extension is required on single file paths."""
        args = Mock(spec=['path'])
        args.path = 'path/to/file'
        error = Mock()
        # Act
        utilities.get_ext(args, error, '.out', '.file')
        # Assert
        self.assertNotEqual(0, error.call_count)


class TestAsk(unittest.TestCase):
    """Unit tests for the `ask` function."""

    def test_ask_yes(self):
        """Verify 'yes' maps to True."""
        with patch('builtins.input', Mock(return_value='yes')):
            response = utilities.ask("?")
        self.assertTrue(response)

    def test_ask_no(self):
        """Verify 'no' maps to False."""
        with patch('builtins.input', Mock(return_value='no')):
            response = utilities.ask("?")
        self.assertFalse(response)

    def test_ask_interrupt(self):
        """Verify a prompt can be interrupted."""
        with patch('builtins.input', Mock(side_effect=KeyboardInterrupt)):
            self.assertRaises(KeyboardInterrupt, utilities.ask, "?")

    def test_ask_bad(self):
        """Verify a bad response re-prompts."""
        with patch('builtins.input', Mock(side_effect=['maybe', 'yes'])):
            response = utilities.ask("?")
        self.assertTrue(response)


class TestShow(unittest.TestCase):
    """Unit tests for the `show` function."""  # pylint: disable=no-self-use

    @patch('builtins.print')
    def test_show(self, mock_print):
        """Verify prints are enabled by default."""
        msg = "Hello, world!"
        utilities.show(msg)
        mock_print.assert_called_once_with(msg, flush=False)

    @patch('builtins.print')
    @patch('doorstop.common.verbosity', common.PRINT_VERBOSITY - 1)
    def test_show_hidden(self, mock_print):
        """Verify prints are hidden when verbosity is quiet."""
        utilities.show("This won't be printed.")
        self.assertEqual(0, mock_print.call_count)


class TestPositiveInt(unittest.TestCase):
    """Unit tests for the `positive_int` function."""

    def test_positive_int(self):
        """Verify a positive integer can be parsed."""
        self.assertEqual(utilities.positive_int('1'), 1)
        self.assertEqual(utilities.positive_int(1), 1)

    def test_non_positive_int(self):
        """Verify a non-positive integer is rejected."""
        self.assertRaises(ArgumentTypeError, utilities.positive_int, '-1')
        self.assertRaises(ArgumentTypeError, utilities.positive_int, -1)
        self.assertRaises(ArgumentTypeError, utilities.positive_int, 0)

    def test_non_int(self):
        """Verify a non-integer is rejected."""
        self.assertRaises(ArgumentTypeError, utilities.positive_int, 'abc')
