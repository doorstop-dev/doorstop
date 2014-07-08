"""Integration tests for the doorstop.cli package."""

import unittest
from unittest.mock import patch, Mock

import os
import tempfile
import shutil

from doorstop.cli.main import main
from doorstop import common
from doorstop.core.builder import _clear_tree
from doorstop import settings

from doorstop.cli.test import ENV, REASON, ROOT, FILES, REQS, TUTORIAL


class TempTestCase(unittest.TestCase):  # pylint: disable=R0904

    """Base test case class with a temporary directory."""  # pylint: disable=C0103

    def setUp(self):
        self.cwd = os.getcwd()
        self.temp = tempfile.mkdtemp()

    def tearDown(self):
        os.chdir(self.cwd)
        if os.path.exists(self.temp):
            shutil.rmtree(self.temp)


class MockTestCase(TempTestCase):  # pylint: disable=R0904

    """Base test case class for a temporary mock working copy."""  # pylint: disable=C0103

    def setUp(self):
        super().setUp()
        os.chdir(self.temp)
        open('.mockvcs', 'w').close()
        _clear_tree()


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestMain(unittest.TestCase):  # pylint: disable=R0904

    """Integration tests for the 'doorstop' command."""

    def setUp(self):
        self.cwd = os.getcwd()
        self.temp = tempfile.mkdtemp()
        self.backup = (settings.REFORMAT,
                       settings.CHECK_REF,
                       settings.CHECK_CHILD_LINKS,
                       settings.REORDER,
                       settings.CHECK_LEVELS)

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.temp)
        (settings.REFORMAT,
         settings.CHECK_REF,
         settings.CHECK_CHILD_LINKS,
         settings.REORDER,
         settings.CHECK_LEVELS) = self.backup

    def test_main(self):
        """Verify 'doorstop' can be called."""
        self.assertIs(None, main([]))

    def test_main_error(self):
        """Verify 'doorstop' returns an error in an empty directory."""
        os.chdir(self.temp)
        self.assertRaises(SystemExit, main, [])

    def test_main_custom_root(self):
        """Verify 'doorstop' can be provided a custom root path."""
        os.chdir(self.temp)
        self.assertIs(None, main(['--project', '.']))

    def test_empty(self):
        """Verify 'doorstop' can be run in a working copy with no docs."""
        os.mkdir(os.path.join(self.temp, '.mockvcs'))
        os.chdir(self.temp)
        self.assertIs(None, main([]))
        self.assertTrue(settings.REFORMAT)
        self.assertTrue(settings.CHECK_REF)
        self.assertTrue(settings.CHECK_CHILD_LINKS)
        self.assertFalse(settings.REORDER)
        self.assertTrue(settings.CHECK_LEVELS)

    def test_options(self):
        """Verify 'doorstop' can be run with options."""
        os.mkdir(os.path.join(self.temp, '.mockvcs'))
        os.chdir(self.temp)
        self.assertIs(None, main(['--no-reformat',
                                  '--no-ref-check',
                                  '--no-child-check',
                                  '--reorder',
                                  '--no-level-check']))
        self.assertFalse(settings.REFORMAT)
        self.assertFalse(settings.CHECK_REF)
        self.assertFalse(settings.CHECK_CHILD_LINKS)
        self.assertTrue(settings.REORDER)
        self.assertFalse(settings.CHECK_LEVELS)


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestCreate(TempTestCase):  # pylint: disable=R0904

    """Integration tests for the 'doorstop create' command."""  # pylint: disable=C0103

    def test_create(self):
        """Verify 'doorstop create' can be called."""
        self.assertIs(None, main(['create', '_TEMP', self.temp, '-p', 'REQ']))

    def test_create_error_unknwon_parent(self):
        """Verify 'doorstop create' returns an error with an unknown parent."""
        self.assertRaises(SystemExit, main,
                          ['create', '_TEMP', self.temp, '-p', 'UNKNOWN'])

    def test_create_error_reserved_prefix(self):
        """Verify 'doorstop create' returns an error with a reserved prefix."""
        self.assertRaises(SystemExit, main,
                          ['create', 'ALL', self.temp, '-p', 'REQ'])


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestDelete(MockTestCase):  # pylint: disable=R0904

    """Integration tests for the 'doorstop delete' command."""

    def test_delete(self):
        """Verify 'doorstop delete' can be called."""
        main(['create', 'PREFIX', 'prefix'])
        self.assertIs(None, main(['delete', 'PREFIX']))

    def test_delete_error(self):
        """Verify 'doorstop delete' returns an error on unknown document."""
        self.assertRaises(SystemExit, main, ['delete', 'UNKNOWN'])


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

    def test_add_specific_level(self):
        """Verify 'doorstop add' can be called with a specific level."""
        self.assertIs(None, main(['add', 'TUT', '--level', '1.42']))
        self.assertTrue(os.path.isfile(self.path))

    def test_add_error(self):
        """Verify 'doorstop add' returns an error with an unknown prefix."""
        self.assertRaises(SystemExit, main, ['add', 'UNKNOWN'])


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestRemove(unittest.TestCase):  # pylint: disable=R0904

    """Integration tests for the 'doorstop remove' command."""

    ITEM = os.path.join(TUTORIAL, 'TUT003.yml')

    def setUp(self):
        with open(self.ITEM, 'r') as item:
            self.backup = item.read()

    def tearDown(self):
        with open(self.ITEM, 'w') as item:
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
        with open(self.ITEM, 'r') as item:
            self.backup = item.read()

    def tearDown(self):
        with open(self.ITEM, 'w') as item:
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
        with open(self.ITEM, 'r') as item:
            self.backup = item.read()
        main(['link', 'tut3', 'req2'])  # create a temporary link

    def tearDown(self):
        with open(self.ITEM, 'w') as item:
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

    @patch('doorstop.core.editor.launch')
    def test_edit_item(self, mock_launch):
        """Verify 'doorstop edit' can be called with an item."""
        self.assertIs(None, main(['edit', 'tut2']))
        path = os.path.join(TUTORIAL, 'TUT002.yml')
        mock_launch.assert_called_once_with(os.path.normpath(path), tool=None)

    def test_edit_item_unknown(self):
        """Verify 'doorstop edit' returns an error on an unknown item."""
        self.assertRaises(SystemExit, main, ['edit', '--item', 'FAKE001'])

    @patch('time.time', Mock(return_value=123))
    @patch('doorstop.core.editor.launch')
    @patch('builtins.input', Mock(return_value='yes'))
    def test_edit_document_yes_yes(self, mock_launch):
        """Verify 'doorstop edit' can be called with a document (yes, yes)."""
        path = "TUT-123.yml"
        self.assertIs(None, main(['edit', 'tut']))
        mock_launch.assert_called_once_with(os.path.normpath(path), tool=None)

    @patch('time.time', Mock(return_value=456))
    @patch('doorstop.core.editor.launch')
    @patch('builtins.input', Mock(return_value='no'))
    def test_edit_document_no_no(self, mock_launch):
        """Verify 'doorstop edit' can be called with a document (no, no)."""
        path = "TUT-456.yml"
        self.assertIs(None, main(['edit', 'tut']))
        os.remove(path)
        mock_launch.assert_called_once_with(os.path.normpath(path), tool=None)

    @patch('time.time', Mock(return_value=789))
    @patch('doorstop.core.editor.launch')
    @patch('builtins.input', Mock(side_effect=['no', 'yes']))
    def test_edit_document_no_yes(self, mock_launch):
        """Verify 'doorstop edit' can be called with a document (no, yes)."""
        path = "TUT-789.yml"
        self.assertIs(None, main(['edit', 'tut']))
        mock_launch.assert_called_once_with(os.path.normpath(path), tool=None)

    def test_edit_document_unknown(self):
        """Verify 'doorstop edit' returns an error on an unknown document."""
        self.assertRaises(SystemExit, main, ['edit', '--document', 'FAKE'])

    def test_edit_error(self):
        """Verify 'doorstop edit' returns an error with an unknown ID."""
        self.assertRaises(SystemExit, main, ['edit', 'req9999'])


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestImport(unittest.TestCase):  # pylint: disable=R0904

    """Integration tests for the 'doorstop import' command."""  # pylint: disable=C0103

    def tearDown(self):
        try:
            shutil.rmtree(os.path.join(ROOT, 'tmp'))
        except IOError:
            pass
        try:
            os.remove(os.path.join(REQS, 'REQ099.yml'))
        except IOError:
            pass

    def test_import_document(self):
        """Verify 'doorstop import' can import a document."""
        self.assertRaises(SystemExit,
                          main, ['import', '--document', 'TMP', 'tmp'])

    def test_import_document_with_parent(self):
        """Verify 'doorstop import' can import a document with a parent."""
        self.assertIs(None, main(['import', '--document', 'TMP', 'tmp',
                                  '--parent', 'REQ']))

    def test_import_item(self):
        """Verify 'doorstop import' can import an item.."""
        self.assertIs(None, main(['import', '--item', 'REQ', 'REQ099']))

    def test_import_item_with_attrs(self):
        """Verify 'doorstop import' can import an item with attributes."""
        self.assertIs(None, main(['import', '--item', 'REQ', 'REQ099',
                                  '--attrs', "{'text': 'The item text.'}"]))

    def test_import_error(self):
        """Verify 'doorstop import' requires a document or item."""
        self.assertRaises(SystemExit, main, ['import', '--attr', "{}"])


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestImportFile(MockTestCase):  # pylint: disable=R0904

    """Integration tests for the 'doorstop import' command."""  # pylint: disable=C0103

    def test_import_file_missing_prefix(self):
        """Verify 'doorstop import' returns an error with a missing prefix."""
        path = os.path.join(FILES, 'exported.xlsx')
        self.assertRaises(SystemExit, main, ['import', path])

    def test_import_file_extra_flags(self):
        """Verify 'doorstop import' returns an error with extra flags."""
        path = os.path.join(FILES, 'exported.xlsx')
        self.assertRaises(SystemExit,
                          main, ['import', path, 'PREFIX', '-d', '_', '_'])
        self.assertRaises(SystemExit,
                          main, ['import', path, 'PREFIX', '-i', '_', '_'])

    def test_import_file_to_document_unknown(self):
        """Verify 'doorstop import' returns an error for unknown documents."""
        path = os.path.join(FILES, 'exported.xlsx')
        self.assertRaises(SystemExit, main, ['import', path, 'PREFIX'])

    def test_import_file_with_map(self):
        """Verify 'doorstop import' can import a file using a custom map."""
        path = os.path.join(FILES, 'exported-map.csv')
        dirpath = os.path.join(self.temp, 'imported', 'prefix')
        main(['create', 'PREFIX', dirpath])
        # Act
        self.assertIs(None, main(['import', path, 'PREFIX',
                                  '--map', "{'mylevel': 'level'}"]))
        # Assert
        path = os.path.join(dirpath, 'REQ001.yml')
        self.assertTrue(os.path.isfile(path))
        with open(path, 'r') as stream:
            text = stream.read()
        self.assertIn('\nlevel: 1.2.3', text)

    def test_import_file_with_map_invalid(self):
        """Verify 'doorstop import' returns an error with an invalid map."""
        path = os.path.join(FILES, 'exported.csv')
        self.assertRaises(SystemExit,
                          main, ['import', path, 'PREFIX', '--map', "{'my"])

    def test_import_csv_to_document_existing(self):
        """Verify 'doorstop import' can import CSV to an existing document."""
        path = os.path.join(FILES, 'exported.csv')
        dirpath = os.path.join(self.temp, 'imported', 'prefix')
        main(['create', 'PREFIX', dirpath])
        # Act
        self.assertIs(None, main(['import', path, 'PREFIX']))
        # Assert
        path = os.path.join(dirpath, 'REQ001.yml')
        self.assertTrue(os.path.isfile(path))

    def test_import_tsv_to_document_existing(self):
        """Verify 'doorstop import' can import TSV to an existing document."""
        path = os.path.join(FILES, 'exported.tsv')
        dirpath = os.path.join(self.temp, 'imported', 'prefix')
        main(['create', 'PREFIX', dirpath])
        # Act
        self.assertIs(None, main(['import', path, 'PREFIX']))
        # Assert
        path = os.path.join(dirpath, 'REQ001.yml')
        self.assertTrue(os.path.isfile(path))

    def test_import_xlsx_to_document_existing(self):
        """Verify 'doorstop import' can import XLSX to an existing document."""
        path = os.path.join(FILES, 'exported.xlsx')
        dirpath = os.path.join(self.temp, 'imported', 'prefix')
        main(['create', 'PREFIX', dirpath])
        # Act
        self.assertIs(None, main(['import', path, 'PREFIX']))
        # Assert
        path = os.path.join(dirpath, 'REQ001.yml')
        self.assertTrue(os.path.isfile(path))


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestExport(TempTestCase):  # pylint: disable=R0904

    """Integration tests for the 'doorstop export' command."""  # pylint: disable=C0103

    def test_export_document_error_unknown(self):
        """Verify 'doorstop export' returns an error for an unknown format."""
        self.assertRaises(SystemExit, main, ['export', 'req', 'req.fake'])

    def test_export_document_error_directory(self):
        """Verify 'doorstop publish' returns an error with a directory."""
        self.assertRaises(SystemExit, main, ['export', 'req', self.temp])

    def test_export_document_error_no_extension(self):
        """Verify 'doorstop publish' returns an error with no extension."""
        path = os.path.join(self.temp, 'req')
        self.assertRaises(SystemExit, main, ['export', 'req', path])

    def test_export_document_stdout(self):
        """Verify 'doorstop export' can create output."""
        self.assertIs(None, main(['export', 'tut']))

    def test_export_document_stdout_width(self):
        """Verify 'doorstop export' can create output."""
        self.assertIs(None, main(['export', 'tut', '--width', '72']))

    def test_export_document_yaml(self):
        """Verify 'doorstop export' can create a YAML file."""
        path = os.path.join(self.temp, 'tut.yml')
        self.assertIs(None, main(['export', 'tut', path]))
        self.assertTrue(os.path.isfile(path))

    def test_export_document_xlsx(self):
        """Verify 'doorstop export' can create an XLSX file."""
        path = os.path.join(self.temp, 'tut.xlsx')
        self.assertIs(None, main(['export', 'tut', path]))
        self.assertTrue(os.path.isfile(path))

    def test_export_tree_xlsx(self):
        """Verify 'doorstop export' can create an XLSX directory."""
        path = os.path.join(self.temp, 'all')
        self.assertIs(None, main(['export', 'all', path, '--xlsx']))
        self.assertTrue(os.path.isdir(path))

    def test_export_tree_no_path(self):
        """Verify 'doorstop export' returns an error with no path."""
        self.assertRaises(SystemExit, main, ['export', 'all'])


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestPublish(TempTestCase):  # pylint: disable=R0904

    """Integration tests for the 'doorstop publish' command."""  # pylint: disable=C0103

    def setUp(self):
        super().setUp()
        self.backup = (settings.PUBLISH_CHILD_LINKS,)

    def tearDown(self):
        super().tearDown()
        (settings.PUBLISH_CHILD_LINKS,) = self.backup

    def test_publish_unknown(self):
        """Verify 'doorstop publish' returns an error for an unknown format."""
        self.assertRaises(SystemExit, main, ['publish', 'req', 'req.fake'])

    def test_publish_document(self):
        """Verify 'doorstop publish' can create output."""
        self.assertIs(None, main(['publish', 'tut']))
        self.assertTrue(settings.PUBLISH_CHILD_LINKS)

    def test_publish_document_with_child_links(self):
        """Verify 'doorstop publish' can create output with child links."""
        self.assertIs(None, main(['publish', 'tut']))
        self.assertTrue(settings.PUBLISH_CHILD_LINKS)

    def test_publish_document_without_child_links(self):
        """Verify 'doorstop publish' can create output without child links."""
        self.assertIs(None, main(['publish', 'tut', '--no-child-links']))
        self.assertFalse(settings.PUBLISH_CHILD_LINKS)

    def test_publish_document_error_empty(self):
        """Verify 'doorstop publish' returns an error in an empty folder."""
        os.chdir(self.temp)
        self.assertRaises(SystemExit, main, ['publish', 'req'])

    def test_publish_document_error_directory(self):
        """Verify 'doorstop publish' returns an error with a directory."""
        self.assertRaises(SystemExit, main, ['publish', 'req', self.temp])

    def test_publish_document_error_no_extension(self):
        """Verify 'doorstop publish' returns an error with no extension."""
        path = os.path.join(self.temp, 'req')
        self.assertRaises(SystemExit, main, ['publish', 'req', path])

    def test_publish_document_text(self):
        """Verify 'doorstop publish' can create text output."""
        self.assertIs(None, main(['publish', 'tut', '--width', '75']))

    def test_publish_document_text_file(self):
        """Verify 'doorstop publish' can create a text file."""
        path = os.path.join(self.temp, 'req.txt')
        self.assertIs(None, main(['publish', 'req', path]))
        self.assertTrue(os.path.isfile(path))

    def test_publish_document_markdown(self):
        """Verify 'doorstop publish' can create Markdown output."""
        self.assertIs(None, main(['publish', 'req', '--markdown']))

    def test_publish_document_markdown_file(self):
        """Verify 'doorstop publish' can create a Markdown file."""
        path = os.path.join(self.temp, 'req.md')
        self.assertIs(None, main(['publish', 'req', path]))
        self.assertTrue(os.path.isfile(path))

    def test_publish_document_html(self):
        """Verify 'doorstop publish' can create HTML output."""
        self.assertIs(None, main(['publish', 'hlt', '--html']))

    def test_publish_document_html_file(self):
        """Verify 'doorstop publish' can create an HTML file."""
        path = os.path.join(self.temp, 'req.html')
        self.assertIs(None, main(['publish', 'req', path]))
        self.assertTrue(os.path.isfile(path))

    def test_publish_tree_html(self):
        """Verify 'doorstop publish' can create an HTML directory."""
        path = os.path.join(self.temp, 'all')
        self.assertIs(None, main(['publish', 'all', path]))
        self.assertTrue(os.path.isdir(path))
        self.assertTrue(os.path.isfile(os.path.join(path, 'index.html')))

    def test_publish_tree_text(self):
        """Verify 'doorstop publish' can create a text directory."""
        path = os.path.join(self.temp, 'all')
        self.assertIs(None, main(['publish', 'all', path, '--text']))
        self.assertTrue(os.path.isdir(path))
        self.assertFalse(os.path.isfile(os.path.join(path, 'index.html')))

    def test_publish_tree_no_path(self):
        """Verify 'doorstop publish' returns an error with no path."""
        self.assertRaises(SystemExit, main, ['publish', 'all'])


@patch('doorstop.cli.commands.run', Mock(return_value=True))  # pylint: disable=R0904
class TestLogging(unittest.TestCase):  # pylint: disable=R0904

    """Integration tests for the Doorstop CLI logging."""

    def test_verbose_0(self):
        """Verify verbose level 0 can be set."""
        self.assertIs(None, main([]))

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
        """Verify verbose level 5 cannot be set."""
        self.assertIs(None, main(['-vvvvv']))
        self.assertEqual(4, common.VERBOSITY)
