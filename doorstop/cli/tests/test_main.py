# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.cli.main module."""

import importlib.util
import sys
from os import sep
from unittest.mock import Mock, patch

from doorstop import settings
from doorstop.cli import main
from doorstop.cli.tests import SettingsTestCase


class TestMain(SettingsTestCase):
    """Unit tests for the `main` function."""

    @patch("doorstop.cli.commands.get")
    def test_run(self, mock_get):
        """Verify the main CLI function can be called."""
        main.main(args=[])
        mock_get.assert_called_once_with(None)

    @patch("doorstop.cli.commands.run", Mock(side_effect=KeyboardInterrupt))
    def test_interrupt(self):
        """Verify the CLI can be interrupted."""
        self.assertRaises(SystemExit, main.main, [])

    @patch("doorstop.cli.commands.run", Mock())
    def test_empty(self):
        """Verify 'doorstop' can be run in a working copy with no docs."""
        self.assertIs(None, main.main([]))
        self.assertTrue(settings.REFORMAT)
        self.assertTrue(settings.CHECK_REF)
        self.assertTrue(settings.CHECK_CHILD_LINKS)
        self.assertFalse(settings.REORDER)
        self.assertTrue(settings.CHECK_LEVELS)
        self.assertTrue(settings.CHECK_SUSPECT_LINKS)
        self.assertTrue(settings.CHECK_REVIEW_STATUS)
        self.assertTrue(settings.CACHE_DOCUMENTS)
        self.assertTrue(settings.CACHE_ITEMS)
        self.assertTrue(settings.CACHE_PATHS)
        self.assertFalse(settings.WARN_ALL)
        self.assertFalse(settings.ERROR_ALL)

    @patch("doorstop.cli.commands.run", Mock())
    def test_options(self):
        """Verify 'doorstop' can be run with options."""
        self.assertIs(
            None,
            main.main(
                [
                    "--no-reformat",
                    "--no-ref-check",
                    "--no-child-check",
                    "--reorder",
                    "--no-level-check",
                    "--no-suspect-check",
                    "--no-review-check",
                    "--no-cache",
                    "--warn-all",
                    "--error-all",
                ]
            ),
        )
        self.assertFalse(settings.REFORMAT)
        self.assertFalse(settings.CHECK_REF)
        self.assertFalse(settings.CHECK_CHILD_LINKS)
        self.assertTrue(settings.REORDER)
        self.assertFalse(settings.CHECK_LEVELS)
        self.assertFalse(settings.CHECK_SUSPECT_LINKS)
        self.assertFalse(settings.CHECK_REVIEW_STATUS)
        self.assertFalse(settings.CACHE_DOCUMENTS)
        self.assertFalse(settings.CACHE_ITEMS)
        self.assertFalse(settings.CACHE_PATHS)
        self.assertTrue(settings.WARN_ALL)
        self.assertTrue(settings.ERROR_ALL)

    def test_main(self):
        testargs = [sep.join(["doorstop", "cli", "main.py"])]
        with patch.object(sys, "argv", testargs):
            spec = importlib.util.spec_from_file_location("__main__", testargs[0])
            runpy = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(runpy)
            # Assert
            self.assertIsNotNone(runpy)
