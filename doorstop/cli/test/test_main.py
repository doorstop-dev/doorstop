"""Unit tests for the doorstop.cli.main module."""

from unittest.mock import patch, Mock

from doorstop.cli import main
from doorstop import settings

from doorstop.cli.test import SettingsTestCase


class TestMain(SettingsTestCase):

    """Unit tests for the `main` function."""  # pylint: disable=R0201

    @patch('doorstop.cli.commands.get')
    def test_run(self, mock_get):
        """Verify the main CLI function can be called."""
        main.main(args=[])
        mock_get.assert_called_once_with(None)

    @patch('doorstop.cli.commands.run', Mock(side_effect=KeyboardInterrupt))
    def test_interrupt(self):
        """Verify the CLI can be interrupted."""
        self.assertRaises(SystemExit, main.main, [])

    @patch('doorstop.cli.commands.run', Mock())
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

    @patch('doorstop.cli.commands.run', Mock())
    def test_options(self):
        """Verify 'doorstop' can be run with options."""
        self.assertIs(None, main.main(['--no-reformat',
                                       '--no-ref-check',
                                       '--no-child-check',
                                       '--reorder',
                                       '--no-level-check',
                                       '--no-suspect-check',
                                       '--no-review-check',
                                       '--no-cache']))
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
