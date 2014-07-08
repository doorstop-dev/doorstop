"""Unit tests for the doorstop.cli.utilities module."""

import unittest
from unittest.mock import patch, Mock

from doorstop.cli import utilities
from doorstop import common
from doorstop import settings


class TestCapture(unittest.TestCase):  # pylint: disable=R0904

    """Unit tests for the `Capture` class."""  # pylint: disable=C0103

    def test_success(self):
        """Verify a success can be captured."""
        with utilities.capture() as success:
            pass
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


class TestConfigureSettings(unittest.TestCase):  # pylint: disable=R0904

    """Unit tests for the `configure_settings` function."""  # pylint: disable=C0103

    def setUp(self):
        self.backup = (settings.REFORMAT,
                       settings.CHECK_REF,
                       settings.CHECK_CHILD_LINKS,
                       settings.REORDER,
                       settings.CHECK_LEVELS,
                       settings.PUBLISH_CHILD_LINKS)

    def tearDown(self):
        (settings.REFORMAT,
         settings.CHECK_REF,
         settings.CHECK_CHILD_LINKS,
         settings.REORDER,
         settings.CHECK_LEVELS,
         settings.PUBLISH_CHILD_LINKS) = self.backup

    def test_configure_settings(self):
        """Verify settings are parsed correctly."""
        args = Mock()
        args.reorder = False
        utilities.configure_settings(args)
        self.assertFalse(settings.REFORMAT)
        self.assertFalse(settings.REORDER)
        self.assertFalse(settings.CHECK_LEVELS)
        self.assertFalse(settings.CHECK_REF)
        self.assertFalse(settings.CHECK_CHILD_LINKS)
        self.assertFalse(settings.PUBLISH_CHILD_LINKS)


class TestLiteralEval(unittest.TestCase):  # pylint: disable=R0904

    """Unit tests for the `literal_eval` function."""  # pylint: disable=C0103

    def test_literal_eval(self):
        """Verify a string can be evaluated as a Python literal."""
        self.assertEqual(42.0, utilities.literal_eval("42.0"))

    def test_literal_eval_invalid_err(self):
        """Verify an invalid literal calls the error function."""
        err = Mock()
        utilities.literal_eval("1/", err=err)
        self.assertEqual(1, err.call_count)

    @patch('logging.critical')
    def test_literal_eval_invalid_log(self, mock_log):
        """Verify an invalid literal logs an error."""
        utilities.literal_eval("1/")
        self.assertEqual(1, mock_log.call_count)


class TestGetExt(unittest.TestCase):  # pylint: disable=R0904

    """Unit tests for the `get_ext` function."""  # pylint: disable=C0103

    def test_get_ext_stdout_document(self):
        """Verify a default output extension can be selected."""
        args = Mock(spec=[])
        err = Mock()
        # Act
        ext = utilities.get_ext(args, '.out', '.file', False, err)
        # Assert
        self.assertEqual(0, err.call_count)
        self.assertEqual('.out', ext)

    def test_get_ext_stdout_document_override(self):
        """Verify a default output extension can be overridden."""
        args = Mock(spec=['html'])
        args.html = True
        err = Mock()
        # Act
        ext = utilities.get_ext(args, '.out', '.file', False, err)
        # Assert
        self.assertEqual(0, err.call_count)
        self.assertEqual('.html', ext)

    @patch('os.path.isdir', Mock(return_value=True))
    def test_get_ext_file_document_to_directory(self):
        """Verify a path is required for a single document."""
        args = Mock(spec=['path'])
        args.path = 'path/to/directory'
        err = Mock()
        # Act
        utilities.get_ext(args, '.out', '.file', False, err)
        # Assert
        self.assertNotEqual(0, err.call_count)

    def test_get_ext_file_document(self):
        """Verify a specified file extension can be selected."""
        args = Mock(spec=['path'])
        args.path = 'path/to/file.cust'
        err = Mock()
        # Act
        ext = utilities.get_ext(args, '.out', '.file', False, err)
        # Assert
        self.assertEqual(0, err.call_count)
        self.assertEqual('.cust', ext)

    def test_get_ext_file_tree(self):
        """Verify a specified file extension can be selected."""
        args = Mock(spec=['path'])
        args.path = 'path/to/directory'
        err = Mock()
        # Act
        ext = utilities.get_ext(args, '.out', '.file', True, err)
        # Assert
        self.assertEqual(0, err.call_count)
        self.assertEqual('.file', ext)

    def test_get_ext_file_document_no_extension(self):
        """Verify an extension is required on single file paths."""
        args = Mock(spec=['path'])
        args.path = 'path/to/file'
        err = Mock()
        # Act
        utilities.get_ext(args, '.out', '.file', False, err)
        # Assert
        self.assertNotEqual(0, err.call_count)


class TestAsk(unittest.TestCase):  # pylint: disable=R0904

    """Unit tests for the `ask` function."""  # pylint: disable=C0103

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
