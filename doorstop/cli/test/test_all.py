#!/usr/bin/env python

"""
Integration tests for the doorstop.cli package.
"""

import unittest
from unittest.mock import patch, Mock

import os
import tempfile
import shutil

from doorstop.cli.main import main
from doorstop import common

from doorstop.cli.test import ENV, REASON, TUTORIAL


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestMain(unittest.TestCase):  # pylint: disable=R0904
    """Integration tests for the 'doorstop' command."""

    def setUp(self):
        self.cwd = os.getcwd()
        self.temp = tempfile.mkdtemp()

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.temp)

    def test_main(self):
        """Verify 'doorstop' can be called."""
        self.assertIs(None, main([]))

    def test_main_help(self):
        """Verify 'doorstop --help' can be requested."""
        self.assertRaises(SystemExit, main, ['--help'])

    def test_main_error(self):
        """Verify 'doorstop' returns an error in an empty directory."""
        os.chdir(self.temp)
        self.assertRaises(SystemExit, main, [])

    def test_main_custom_root(self):
        """Verify 'doorstop' can be provided a custom root path."""
        os.chdir(self.temp)
        self.assertIs(None, main(['--project', '.']))

    @patch('doorstop.cli.main._run', Mock(return_value=False))
    def test_exit(self):
        """Verify 'doorstop' treats False as an error ."""
        self.assertRaises(SystemExit, main, [])

    @patch('doorstop.cli.main._run', Mock(side_effect=KeyboardInterrupt))
    def test_interrupt(self):
        """Verify 'doorstop' treats KeyboardInterrupt as an error."""
        self.assertRaises(SystemExit, main, [])

    def test_empty(self):
        """Verify 'doorstop' can be run in a working copy with no docs."""
        os.mkdir(os.path.join(self.temp, '.mockvcs'))
        os.chdir(self.temp)
        self.assertIs(None, main([]))

    @patch('doorstop.cli.main.gui', Mock(return_value=True))
    def test_gui(self):
        """Verify 'doorstop --gui' launches the GUI."""
        self.assertIs(None, main(['--gui']))


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestNew(unittest.TestCase):  # pylint: disable=R0904
    """Integration tests for the 'doorstop new' command."""

    def setUp(self):
        self.cwd = os.getcwd()
        self.temp = tempfile.mkdtemp()

    def tearDown(self):
        os.chdir(self.cwd)
        if os.path.exists(self.temp):
            shutil.rmtree(self.temp)

    def test_new(self):
        """Verify 'doorstop new' can be called."""
        self.assertIs(None, main(['new', '_TEMP', self.temp, '-p', 'REQ']))

    def test_new_error(self):
        """Verify 'doorstop new' returns an error with an unknown parent."""
        self.assertRaises(SystemExit, main,
                          ['new', '_TEMP', self.temp, '-p', 'UNKNOWN'])


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestAdd(unittest.TestCase):  # pylint: disable=R0904
    """Integration tests for the 'doorstop add' command."""

    @classmethod
    def setUpClass(cls):
        last = sorted(os.listdir(TUTORIAL))[-1]
        number = int(last.replace('TUT', '').replace('.yml', '')) + 1
        filename = "TUT{}.yml".format(str(number).zfill(3))
        cls.path = os.path.join(TUTORIAL, filename)

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def test_add(self):
        """Verify 'doorstop add' can be called."""
        self.assertIs(None, main(['add', 'TUT']))
        self.assertTrue(os.path.isfile(self.path))

    def test_add_error(self):
        """Verify 'doorstop add' returns an error with an unknown prefix."""
        self.assertRaises(SystemExit, main, ['add', 'UNKNOWN'])


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestRemove(unittest.TestCase):  # pylint: disable=R0904
    """Integration tests for the 'doorstop remove' command."""

    ITEM = os.path.join(TUTORIAL, 'TUT003.yml')

    def setUp(self):
        with open(self.ITEM, 'rb') as item:
            self.backup = item.read()

    def tearDown(self):
        with open(self.ITEM, 'wb') as item:
            item.write(self.backup)

    def test_remove(self):
        """Verify 'doorstop remove' can be called."""
        self.assertIs(None, main(['remove', 'tut3']))
        self.assertFalse(os.path.exists(self.ITEM))

    def test_remove_error(self):
        """Verify 'doorstop remove' returns an error on unknown item IDs."""
        self.assertRaises(SystemExit, main, ['remove', 'tut9999'])


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestLink(unittest.TestCase):  # pylint: disable=R0904
    """Integration tests for the 'doorstop link' command."""

    ITEM = os.path.join(TUTORIAL, 'TUT003.yml')

    def setUp(self):
        with open(self.ITEM, 'rb') as item:
            self.backup = item.read()

    def tearDown(self):
        with open(self.ITEM, 'wb') as item:
            item.write(self.backup)

    def test_link(self):
        """Verify 'doorstop link' can be called."""
        self.assertIs(None, main(['link', 'tut3', 'req2']))

    def test_link_unknown_child(self):
        """Verify 'doorstop link' returns an error with an unknown child."""
        self.assertRaises(SystemExit, main, ['link', 'unknown3', 'req2'])
        self.assertRaises(SystemExit, main, ['link', 'tut9999', 'req2'])

    def test_link_unknown_parent(self):
        """Verify 'doorstop link' returns an error with an unknown parent."""
        self.assertRaises(SystemExit, main, ['link', 'tut3', 'unknown2'])
        self.assertRaises(SystemExit, main, ['link', 'tut3', 'req9999'])


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestUnlink(unittest.TestCase):  # pylint: disable=R0904
    """Integration tests for the 'doorstop unlink' command."""

    ITEM = os.path.join(TUTORIAL, 'TUT003.yml')

    def setUp(self):
        with open(self.ITEM, 'rb') as item:
            self.backup = item.read()
        main(['link', 'tut3', 'req2'])  # create a temporary link

    def tearDown(self):
        with open(self.ITEM, 'wb') as item:
            item.write(self.backup)

    def test_unlink(self):
        """Verify 'doorstop unlink' can be called."""
        self.assertIs(None, main(['unlink', 'tut3', 'req2']))

    def test_unlink_unknown_child(self):
        """Verify 'doorstop unlink' returns an error with an unknown child."""
        self.assertRaises(SystemExit, main, ['unlink', 'unknown3', 'req2'])
        self.assertRaises(SystemExit, main, ['link', 'tut9999', 'req2'])

    def test_unlink_unknown_parent(self):
        """Verify 'doorstop unlink' returns an error with an unknown parent."""
        self.assertRaises(SystemExit, main, ['unlink', 'tut3', 'unknown2'])
        self.assertRaises(SystemExit, main, ['unlink', 'tut3', 'req9999'])


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestEdit(unittest.TestCase):  # pylint: disable=R0904
    """Integration tests for the 'doorstop edit' command."""

    @patch('doorstop.core.tree._open')
    def test_edit(self, mock_open):
        """Verify 'doorstop edit' can be called."""
        self.assertIs(None, main(['edit', 'tut2']))
        path = os.path.join(TUTORIAL, 'TUT002.yml')
        mock_open.assert_called_once_with(os.path.normpath(path), tool=None)

    def test_edit_error(self):
        """Verify 'doorstop edit' returns an error with an unknown ID."""
        self.assertRaises(SystemExit, main, ['edit', 'req9999'])


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestPublish(unittest.TestCase):  # pylint: disable=R0904
    """Integration tests for the 'doorstop publish' command."""

    def setUp(self):
        self.cwd = os.getcwd()
        self.temp = tempfile.mkdtemp()

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.temp)

    def test_publish_text(self):
        """Verify 'doorstop publish' can create text output."""
        self.assertIs(None, main(['publish', 'tut', '--width', '75']))

    def test_publish_text_file(self):
        """Verify 'doorstop publish' can create a text file."""
        path = os.path.join(self.temp, 'req.txt')
        self.assertIs(None, main(['publish', 'req', path]))
        self.assertTrue(os.path.isfile(path))

    def test_publish_markdown(self):
        """Verify 'doorstop publish' can create Markdown output."""
        self.assertIs(None, main(['publish', 'req', '--markdown']))

    def test_publish_markdown_file(self):
        """Verify 'doorstop publish' can create a Markdown file."""
        path = os.path.join(self.temp, 'req.md')
        self.assertIs(None, main(['publish', 'req', path]))
        self.assertTrue(os.path.isfile(path))

    def test_publish_html(self):
        """Verify 'doorstop publish' can create HTML output."""
        self.assertIs(None, main(['publish', 'hlt', '--html']))

    def test_publish_html_file(self):
        """Verify 'doorstop publish' can create an HTML file."""
        path = os.path.join(self.temp, 'req.html')
        self.assertIs(None, main(['publish', 'req', path]))
        self.assertTrue(os.path.isfile(path))

    def test_report_error(self):
        """Verify 'doorstop publish' returns an error in an empty folder."""
        os.chdir(self.temp)
        self.assertRaises(SystemExit, main, ['publish', 'req'])


@patch('doorstop.cli.main._run', Mock(return_value=True))  # pylint: disable=R0904
class TestLogging(unittest.TestCase):  # pylint: disable=R0904
    """Integration tests for the Doorstop CLI logging."""

    def test_verbose_1(self):
        """Verify verbose level 1 can be set."""
        self.assertIs(None, main(['-v']))

    def test_verbose_2(self):
        """Verify verbose level 2 can be set."""
        self.assertIs(None, main(['-vv']))

    def test_verbose_3(self):
        """Verify verbose level 3 can be set."""
        self.assertIs(None, main(['-vvv']))

    def test_verbose_4(self):
        """Verify verbose level 4 can be set."""
        self.assertIs(None, main(['-vvvv']))

    def test_verbose_5(self):
        """Verify verbose level 5 can be set."""
        self.assertIs(None, main(['-vvvvv']))
        self.assertEqual(5, common.VERBOSITY)

    def test_verbose_6(self):
        """Verify verbose level 6 cannot be set."""
        self.assertIs(None, main(['-vvvvvv']))
        self.assertEqual(5, common.VERBOSITY)
