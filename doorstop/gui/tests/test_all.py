# SPDX-License-Identifier: LGPL-3.0-only

"""Integration tests for the doorstop.cli package."""

import imp
import sys
import unittest
from unittest.mock import Mock, patch

from doorstop.gui import main as gui
from doorstop.gui.main import main  # type: ignore


class TestMain(unittest.TestCase):
    """Integration tests for the 'doorstop-gui' command."""

    @patch('doorstop.gui.main.run', Mock(return_value=True))
    def test_gui(self):
        """Verify 'doorstop-gui' launches the GUI."""
        self.assertIs(0, main([]))

    @patch('doorstop.gui.main.run', Mock(return_value=False))
    def test_exit(self):
        """Verify 'doorstop-gui' treats False as an error ."""
        self.assertIs(1, main([]))

    @patch('doorstop.gui.main.run', Mock(side_effect=KeyboardInterrupt))
    def test_interrupt(self):
        """Verify 'doorstop-gui' treats KeyboardInterrupt as an error."""
        self.assertIs(1, main([]))


class TestImport(unittest.TestCase):
    """Integration tests for importing the GUI module."""

    def test_import(self):
        """Verify tkinter import errors are handled."""
        sys.modules['tkinter'] = Mock(side_effect=ImportError)
        imp.reload(gui)
        self.assertFalse(gui.run(None, None, lambda x: False))  # pylint: disable=W0212
        self.assertIsInstance(gui.tk, Mock)


@patch('doorstop.gui.main.run', Mock(return_value=True))
class TestLogging(unittest.TestCase):
    """Integration tests for the Doorstop GUI logging."""

    def test_verbose_1(self):
        """Verify verbose level 1 can be set."""
        self.assertIs(0, main(['-v']))

    def test_verbose_2(self):
        """Verify verbose level 2 can be set."""
        self.assertIs(0, main(['-v', '-v']))

    def test_verbose_3(self):
        """Verify verbose level 1 can be set."""
        self.assertIs(0, main(['-v', '-v', '-v']))
