"""Integration tests for the doorstop.cli package."""

import unittest
from unittest.mock import patch, Mock

import sys
import imp

from doorstop.gui.main import main
from doorstop.gui import main as gui


class TestMain(unittest.TestCase):  # pylint: disable=R0904

    """Integration tests for the 'doorstop-gui' command."""

    @patch('doorstop.gui.main._run', Mock(return_value=True))
    def test_gui(self):
        """Verify 'doorstop-gui' launches the GUI."""
        self.assertIs(None, main([]))

    @patch('doorstop.gui.main._run', Mock(return_value=False))
    def test_exit(self):
        """Verify 'doorstop-gui' treats False as an error ."""
        self.assertRaises(SystemExit, main, [])

    @patch('doorstop.gui.main._run', Mock(side_effect=KeyboardInterrupt))
    def test_interrupt(self):
        """Verify 'doorstop-gui' treats KeyboardInterrupt as an error."""
        self.assertRaises(SystemExit, main, [])


class TestImport(unittest.TestCase):  # pylint: disable=R0904

    """Integration tests for importing the GUI module."""

    def test_import(self):
        """Verify tkinter import errors are handled."""
        sys.modules['tkinter'] = Mock(side_effect=ImportError)
        imp.reload(gui)
        self.assertFalse(gui._run(None, None, lambda x: False))  # pylint: disable=W0212
        self.assertIsInstance(gui.tk, Mock)


@patch('doorstop.gui.main._run', Mock(return_value=True))  # pylint: disable=R0904
class TestLogging(unittest.TestCase):  # pylint: disable=R0904

    """Integration tests for the Doorstop GUI logging."""

    def test_verbose_1(self):
        """Verify verbose level 1 can be set."""
        self.assertIs(None, main(['-v']))

    def test_verbose_2(self):
        """Verify verbose level 2 can be set."""
        self.assertIs(None, main(['-v', '-v']))

    def test_verbose_3(self):
        """Verify verbose level 1 can be set."""
        self.assertIs(None, main(['-v', '-v', '-v']))
