"""Unit tests for the doorstop.cli.main module."""

import unittest
from unittest.mock import patch, Mock

from doorstop.cli import main


class TestMain(unittest.TestCase):  # pylint: disable=R0904

    """Unit tests for the `main` function."""  # pylint: disable=C0103,R0201

    @patch('doorstop.cli.commands.get')
    def test_run(self, mock_get):
        """Verify the main CLI function can be called."""
        main.main(args=[])
        mock_get.assert_called_once_with(None)

    @patch('doorstop.cli.main.gui')
    def test_gui(self, mock_gui):
        """Verify the main GUI function can be called."""
        main.main(args=['--gui'])
        mock_gui.assert_called_once()

    @patch('doorstop.cli.commands.run', Mock(side_effect=KeyboardInterrupt))
    def test_interrupt(self):
        """Verify the CLI can be interrupted."""
        self.assertRaises(SystemExit, main.main, [])
