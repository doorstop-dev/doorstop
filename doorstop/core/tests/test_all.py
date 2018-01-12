"""Tests for the doorstop.core package."""

# pylint: disable=protected-access,unidiomatic-typecheck

import unittest
from unittest.mock import patch, Mock

import os
import csv
import tempfile
import shutil
import pprint
import logging
import warnings

import yaml
import openpyxl

from doorstop import common
from doorstop.common import DoorstopError, DoorstopWarning, DoorstopInfo
from doorstop import core
from doorstop.core.builder import _get_tree, _clear_tree
from doorstop.core.vcs import mockvcs

from doorstop.core.tests import ENV, REASON, ROOT, FILES, EMPTY, SYS, FILES_BETA
from doorstop.core.tests import DocumentNoSkip

# Whenever the export format is changed:
#  1. set CHECK_EXPORTED_CONTENT to False
#  2. re-run all tests
#  3. manually verify the newly exported content is correct
#  4. set CHECK_EXPORTED_CONTENT to True
CHECK_EXPORTED_CONTENT = True

# Whenever the publish format is changed:
#  1. set CHECK_PUBLISHED_CONTENT to False
#  2. re-run all tests
#  3. manually verify the newly published content is correct
#  4. set CHECK_PUBLISHED_CONTENT to True
CHECK_PUBLISHED_CONTENT = True


class TestItem(unittest.TestCase):
    """Integration tests for the Item class."""

    def setUp(self):
        self.path = os.path.join(FILES, 'REQ001.yml')
        self.backup = common.read_text(self.path)
        self.item = core.Item(self.path)
        self.item.tree = Mock()
        self.item.tree.vcs = mockvcs.WorkingCopy(EMPTY)

    def tearDown(self):
        common.write_text(self.backup, self.path)

    def test_save_load(self):
        """Verify an item can be saved and loaded from a file."""
        self.item.level = '1.2.3'
        self.item.text = "Hello, world!"
        self.item.links = ['SYS001', 'SYS002']
        item2 = core.Item(os.path.join(FILES, 'REQ001.yml'))
        self.assertEqual((1, 2, 3), item2.level)
        self.assertEqual("Hello, world!", item2.text)
        self.assertEqual(['SYS001', 'SYS002'], item2.links)

    @unittest.skipUnless(os.getenv(ENV), REASON)
    def test_find_ref(self):
        """Verify an item's external reference can be found."""
        item = core.Item(os.path.join(FILES, 'REQ003.yml'))
        item.tree = Mock()
        item.tree.vcs = mockvcs.WorkingCopy(ROOT)
        path, line = item.find_ref()
        relpath = os.path.relpath(os.path.join(FILES, 'external', 'text.txt'),
                                  ROOT)
        self.assertEqual(relpath, path)
        self.assertEqual(3, line)

    def test_find_ref_error(self):
        """Verify an error occurs when no external reference found."""
        self.item.ref = "not" "found"  # space avoids self match
        self.assertRaises(DoorstopError, self.item.find_ref)


class TestDocument(unittest.TestCase):
    """Integration tests for the Document class."""

    def setUp(self):
        self.document = core.Document(FILES, root=ROOT)

    def tearDown(self):
        """Clean up temporary files."""
        for filename in os.listdir(EMPTY):
            path = os.path.join(EMPTY, filename)
            common.delete(path)

    def test_load(self):
        """Verify a document can be loaded from a directory."""
        doc = core.Document(FILES)
        self.assertEqual('REQ', doc.prefix)
        self.assertEqual(2, doc.digits)
        self.assertEqual(5, len(doc.items))

    def test_new(self):
        """Verify a new document can be created."""
        document = core.Document.new(None,
                                     EMPTY, FILES,
                                     prefix='SYS', digits=4)
        self.assertEqual('SYS', document.prefix)
        self.assertEqual(4, document.digits)
        self.assertEqual(0, len(document.items))

    @patch('doorstop.settings.REORDER', False)
    @patch('doorstop.settings.REVIEW_NEW_ITEMS', False)
    def test_validate(self):
        """Verify a document can be validated."""
        self.assertTrue(self.document.validate())

    @patch('doorstop.settings.REORDER', False)
    @patch('doorstop.settings.REVIEW_NEW_ITEMS', False)
    def test_issues_count(self):
        """Verify a number of issues are found in a document."""
        issues = self.document.issues
        for issue in self.document.issues:
            logging.info(repr(issue))
        self.assertEqual(12, len(issues))

    @patch('doorstop.settings.REORDER', False)
    @patch('doorstop.settings.REVIEW_NEW_ITEMS', False)
    def test_issues_duplicate_level(self):
        """Verify duplicate item levels are detected."""
        expect = DoorstopWarning("duplicate level: 2.1 (REQ002, REQ2-001)")
        for issue in self.document.issues:
            logging.info(repr(issue))
            if type(issue) == type(expect) and issue.args == expect.args:
                break
        else:
            self.fail("issue not found: {}".format(expect))

    @patch('doorstop.settings.REORDER', False)
    @patch('doorstop.settings.REVIEW_NEW_ITEMS', False)
    def test_issues_skipped_level(self):
        """Verify skipped item levels are detected."""
        expect = DoorstopInfo("skipped level: 1.4 (REQ003), 1.6 (REQ004)")
        for issue in self.document.issues:
            logging.info(repr(issue))
            if type(issue) == type(expect) and issue.args == expect.args:
                break
        else:
            self.fail("issue not found: {}".format(expect))

    def test_add_item_with_reordering(self):
        """Verify an item can be inserted into a document."""
        document = core.Document.new(None,
                                     EMPTY, FILES,
                                     prefix='TMP')
        item_1_0 = document.add_item()
        item_1_2 = document.add_item()  # will get displaced
        item_1_1 = document.add_item(level='1.1')
        self.assertEqual((1, 0), item_1_0.level)
        self.assertEqual((1, 1), item_1_1.level)
        self.assertEqual((1, 2), item_1_2.level)

    def test_remove_item_with_reordering(self):
        """Verify an item can be removed from a document."""
        document = core.Document.new(None,
                                     EMPTY, FILES,
                                     prefix='TMP')
        item_1_0 = document.add_item()
        item_1_2 = document.add_item()  # to be removed
        item_1_1 = document.add_item(level='1.1')  # will get relocated
        document.remove_item(item_1_2)
        self.assertEqual((1, 0), item_1_0.level)
        self.assertEqual((1, 1), item_1_1.level)

    def test_reorder(self):
        """Verify a document's order can be corrected."""
        document = core.Document.new(None,
                                     EMPTY, FILES,
                                     prefix='TMP')
        document.add_item(level='2.0', reorder=False)
        document.add_item(level='2.1', reorder=False)
        document.add_item(level='2.1', reorder=False)
        document.add_item(level='2.5', reorder=False)
        document.add_item(level='4.5', reorder=False)
        document.add_item(level='4.7', reorder=False)
        document.reorder()
        expected = [(2, 0), (2, 1), (2, 2), (2, 3), (3, 1), (3, 2)]
        actual = [item.level for item in document.items]
        self.assertListEqual(expected, actual)

    def test_reorder_with_keep(self):
        """Verify a document's order can be corrected with a kept level."""
        document = core.Document.new(None,
                                     EMPTY, FILES,
                                     prefix='TMP')
        document.add_item(level='1.0', reorder=False)
        item = document.add_item(level='1.0', reorder=False)
        document.add_item(level='1.0', reorder=False)
        document.reorder(keep=item)
        expected = [(1, 0), (2, 0), (3, 0)]
        actual = [i.level for i in document.items]
        self.assertListEqual(expected, actual)
        self.assertEqual((1, 0), item.level)

    def test_reorder_with_start(self):
        """Verify a document's order can be corrected with a given start."""
        document = core.Document.new(None,
                                     EMPTY, FILES,
                                     prefix='TMP')
        document.add_item(level='2.0', reorder=False)
        document.add_item(level='2.1', reorder=False)
        document.add_item(level='2.1', reorder=False)
        document.add_item(level='2.5', reorder=False)
        document.add_item(level='4.0', reorder=False)
        document.add_item(level='4.7', reorder=False)
        document.reorder(start=(1, 0))
        expected = [(1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1)]
        actual = [item.level for item in document.items]
        self.assertListEqual(expected, actual)

    @patch('doorstop.settings.REORDER', True)
    @patch('doorstop.settings.REVIEW_NEW_ITEMS', False)
    def test_validate_with_reordering(self):
        """Verify a document's order is corrected during validation."""
        document = core.Document.new(None,
                                     EMPTY, FILES,
                                     prefix='TMP')
        document.add_item(level='1.0', reorder=False)
        document.add_item(level='1.1', reorder=False)
        document.add_item(level='1.2.0', reorder=False)
        document.add_item(level='1.2.5', reorder=False)
        document.add_item(level='3.2.1', reorder=False)
        document.add_item(level='3.3', reorder=False)
        self.assertTrue(document.validate())
        expected = [(1, 0), (1, 1), (1, 2, 0), (1, 2, 1), (2, 1, 1), (2, 2)]
        actual = [item.level for item in document.items]
        self.assertListEqual(expected, actual)


class TestTree(unittest.TestCase):
    """Integration tests for the core.Tree class."""

    def setUp(self):
        self.path = os.path.join(FILES, 'REQ001.yml')
        self.backup = common.read_text(self.path)
        self.item = core.Item(self.path)
        self.tree = core.Tree(core.Document(SYS))
        self.tree._place(core.Document(FILES))

    def tearDown(self):
        common.write_text(self.backup, self.path)

    @patch('doorstop.settings.REORDER', False)
    @patch('doorstop.settings.REVIEW_NEW_ITEMS', False)
    @patch('doorstop.settings.STAMP_NEW_LINKS', False)
    @patch('doorstop.settings.CHECK_REF', False)
    def test_issues_count(self):
        """Verify a number of issues are found in a tree."""
        issues = self.tree.issues
        for issue in self.tree.issues:
            logging.info(repr(issue))
        self.assertEqual(14, len(issues))

    @patch('doorstop.settings.REORDER', False)
    @patch('doorstop.settings.REVIEW_NEW_ITEMS', False)
    @patch('doorstop.settings.STAMP_NEW_LINKS', False)
    @patch('doorstop.settings.CHECK_REF', False)
    def test_issues_count_with_skips(self):
        """Verify a document can be skipped during validation."""
        issues = list(self.tree.get_issues(skip=['req']))
        for issue in self.tree.issues:
            logging.info(repr(issue))
        self.assertEqual(2, len(issues))

    @patch('doorstop.settings.REORDER', False)
    @patch('doorstop.settings.STAMP_NEW_LINKS', False)
    @patch('doorstop.settings.REVIEW_NEW_ITEMS', False)
    @patch('doorstop.core.document.Document', DocumentNoSkip)
    def test_validate_invalid_link(self):
        """Verify a tree is invalid with a bad link."""
        self.item.link('SYS003')
        tree = core.build(FILES, root=FILES)
        self.assertIsInstance(tree, core.Tree)
        self.assertFalse(tree.validate())

    @patch('doorstop.settings.REORDER', False)
    @patch('doorstop.settings.REVIEW_NEW_ITEMS', False)
    def test_validate_long(self):
        """Verify trees can be checked."""
        logging.info("tree: {}".format(self.tree))
        self.assertTrue(self.tree.validate())


@unittest.skipUnless(os.getenv(ENV), REASON)
class TestEditor(unittest.TestCase):
    """Integrations tests for the editor module."""


class TestImporter(unittest.TestCase):
    """Integrations tests for the importer module."""

    def setUp(self):
        # Create a temporary mock working copy
        self.cwd = os.getcwd()
        self.temp = tempfile.mkdtemp()
        os.chdir(self.temp)
        common.touch('.mockvcs')
        # Create default document attributes
        self.prefix = 'PREFIX'
        self.root = self.temp
        self.path = os.path.join(self.root, 'DIRECTORY')
        self.parent = 'PARENT_PREFIX'
        # Create default item attributes
        self.uid = 'PREFIX-00042'
        # Load an actual document
        self.document = core.Document(FILES, root=ROOT)
        # Ensure the tree is reloaded
        _clear_tree()

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.temp)

    def test_import_yml(self):
        """Verify items can be imported from a YAML file."""
        path = os.path.join(self.temp, 'exported.yml')
        core.exporter.export(self.document, path)
        _path = os.path.join(self.temp, 'imports', 'req')
        _tree = _get_tree()
        document = _tree.create_document(_path, 'REQ')
        # Act
        core.importer.import_file(path, document)
        # Assert
        expected = [item.data for item in self.document.items]
        actual = [item.data for item in document.items]
        log_data(expected, actual)
        self.assertListEqual(expected, actual)

    def test_import_csv(self):
        """Verify items can be imported from a CSV file."""
        path = os.path.join(self.temp, 'exported.csv')
        core.exporter.export(self.document, path)
        _path = os.path.join(self.temp, 'imports', 'req')
        _tree = _get_tree()
        document = _tree.create_document(_path, 'REQ')
        # Act
        core.importer.import_file(path, document)
        # Assert
        expected = [item.data for item in self.document.items]
        actual = [item.data for item in document.items]
        log_data(expected, actual)
        self.assertListEqual(expected, actual)

    def test_import_tsv(self):
        """Verify items can be imported from a TSV file."""
        path = os.path.join(self.temp, 'exported.tsv')
        core.exporter.export(self.document, path)
        _path = os.path.join(self.temp, 'imports', 'req')
        _tree = _get_tree()
        document = _tree.create_document(_path, 'REQ')
        # Act
        core.importer.import_file(path, document)
        # Assert
        expected = [item.data for item in self.document.items]
        actual = [item.data for item in document.items]
        log_data(expected, actual)
        self.assertListEqual(expected, actual)

    @unittest.skipUnless(os.getenv(ENV), REASON)
    def test_import_xlsx(self):
        """Verify items can be imported from an XLSX file."""
        path = os.path.join(self.temp, 'exported.xlsx')
        core.exporter.export(self.document, path)
        _path = os.path.join(self.temp, 'imports', 'req')
        _tree = _get_tree()
        document = _tree.create_document(_path, 'REQ')
        # Act
        core.importer.import_file(path, document)
        # Assert
        expected = [item.data for item in self.document.items]
        actual = [item.data for item in document.items]
        log_data(expected, actual)
        self.assertListEqual(expected, actual)

    # TODO: determine when this test should be run (if at all)
    # currently, 'TEST_LONG' isn't set under any condition
    @unittest.skipUnless(os.getenv(ENV), REASON)
    @unittest.skipUnless(os.getenv('TEST_LONG'), "this test takes too long")
    @unittest.skipIf(os.getenv('TRAVIS'), "this test takes too long")
    def test_import_xlsx_huge(self):
        """Verify huge XLSX files are handled."""
        path = os.path.join(FILES, 'exported-huge.xlsx')
        _path = os.path.join(self.temp, 'imports', 'req')
        _tree = _get_tree()
        document = _tree.create_document(_path, 'REQ')
        # Act
        with warnings.catch_warnings(record=True) as warns:
            core.importer.import_file(path, document)
            # Assert
        self.assertEqual(1, len(warns))
        self.assertIn("maximum number of rows", str(warns[-1].message))
        expected = []
        actual = [item.data for item in document.items]
        log_data(expected, actual)
        self.assertListEqual(expected, actual)

    def test_create_document(self):
        """Verify a new document can be created to import items."""
        document = core.importer.create_document(self.prefix, self.path)
        self.assertEqual(self.prefix, document.prefix)
        self.assertEqual(self.path, document.path)

    def test_create_document_with_unknown_parent(self):
        """Verify a new document can be created with an unknown parent."""
        # Verify the document does not already exist
        self.assertRaises(DoorstopError, core.find_document, self.prefix)
        # Import a document
        document = core.importer.create_document(self.prefix, self.path,
                                                 parent=self.parent)
        # Verify the imported document's attributes are correct
        self.assertEqual(self.prefix, document.prefix)
        self.assertEqual(self.path, document.path)
        self.assertEqual(self.parent, document.parent)
        # Verify the imported document can be found
        document2 = core.find_document(self.prefix)
        self.assertIs(document, document2)

    def test_create_document_already_exists(self):
        """Verify non-parent exceptions are re-raised."""
        # Create a document
        core.importer.create_document(self.prefix, self.path)
        # Attempt to create the same document
        self.assertRaises(DoorstopError, core.importer.create_document,
                          self.prefix, self.path)

    def test_add_item(self):
        """Verify an item can be imported into a document."""
        # Create a document
        core.importer.create_document(self.prefix, self.path)
        # Verify the item does not already exist
        self.assertRaises(DoorstopError, core.find_item, self.uid)
        # Import an item
        item = core.importer.add_item(self.prefix, self.uid)
        # Verify the item's attributes are correct
        self.assertEqual(self.uid, item.uid)
        # Verify the item can be found
        item2 = core.find_item(self.uid)
        self.assertIs(item, item2)
        # Verify the item is contained in the document
        document = core.find_document(self.prefix)
        self.assertIn(item, document.items)

    def test_add_item_with_attrs(self):
        """Verify an item with attributes can be imported into a document."""
        # Create a document
        core.importer.create_document(self.prefix, self.path)
        # Import an item
        attrs = {'text': "Item text", 'ext1': "Extended 1"}
        item = core.importer.add_item(self.prefix, self.uid,
                                      attrs=attrs)
        # Verify the item is correct
        self.assertEqual(self.uid, item.uid)
        self.assertEqual(attrs['text'], item.text)
        self.assertEqual(attrs['ext1'], item.get('ext1'))


class TestExporter(unittest.TestCase):
    """Integration tests for the doorstop.core.exporter module."""

    maxDiff = None

    def setUp(self):
        self.document = core.Document(FILES, root=ROOT)
        self.temp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp)

    def test_export_yml(self):
        """Verify a document can be exported as a YAML file."""
        path = os.path.join(FILES, 'exported.yml')
        temp = os.path.join(self.temp, 'exported.yml')
        expected = read_yml(path)
        # Act
        path2 = core.exporter.export(self.document, temp)
        # Assert
        self.assertIs(temp, path2)
        if CHECK_EXPORTED_CONTENT:
            actual = read_yml(temp)
            self.assertEqual(expected, actual)
        move_file(temp, path)

    def test_export_csv(self):
        """Verify a document can be exported as a CSV file."""
        path = os.path.join(FILES, 'exported.csv')
        temp = os.path.join(self.temp, 'exported.csv')
        expected = read_csv(path)
        # Act
        path2 = core.exporter.export(self.document, temp)
        # Assert
        self.assertIs(temp, path2)
        if CHECK_EXPORTED_CONTENT:
            actual = read_csv(temp)
            self.assertEqual(expected, actual)
        move_file(temp, path)

    @patch('doorstop.settings.REVIEW_NEW_ITEMS', False)
    def test_export_tsv(self):
        """Verify a document can be exported as a TSV file."""
        path = os.path.join(FILES, 'exported.tsv')
        temp = os.path.join(self.temp, 'exported.tsv')
        expected = read_csv(path, delimiter='\t')
        # Act
        path2 = core.exporter.export(self.document, temp)
        # Assert
        self.assertIs(temp, path2)
        if CHECK_EXPORTED_CONTENT:
            actual = read_csv(temp, delimiter='\t')
            self.assertEqual(expected, actual)
        move_file(temp, path)

    @unittest.skipUnless(os.getenv(ENV) or not CHECK_EXPORTED_CONTENT, REASON)
    def test_export_xlsx(self):
        """Verify a document can be exported as an XLSX file."""
        path = os.path.join(FILES, 'exported.xlsx')
        temp = os.path.join(self.temp, 'exported.xlsx')
        expected = read_xlsx(path)
        # Act
        path2 = core.exporter.export(self.document, temp)
        # Assert
        self.assertIs(temp, path2)
        if CHECK_EXPORTED_CONTENT:
            actual = read_xlsx(temp)
            self.assertEqual(expected, actual)
        else:  # binary file always changes, only copy when not checking
            move_file(temp, path)


class TestPublisher(unittest.TestCase):
    """Integration tests for the doorstop.core.publisher module."""

    maxDiff = None

    @patch('doorstop.core.document.Document', DocumentNoSkip)
    def setUp(self):
        self.tree = core.build(cwd=FILES, root=FILES)
        # self.document = core.Document(FILES, root=ROOT)
        self.document = self.tree.find_document('REQ')
        self.temp = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.temp):
            shutil.rmtree(self.temp)

    def test_publish_html(self):
        """Verify an HTML file can be created."""
        path = os.path.join(self.temp, 'published.html')
        # Act
        path2 = core.publisher.publish(self.document, path, '.html')
        # Assert
        self.assertIs(path, path2)
        self.assertTrue(os.path.isfile(path))

    def test_publish_bad_link(self):
        """Verify a tree can be published with bad links."""
        item = self.document.add_item()
        try:
            item.link('badlink')
            dirpath = os.path.join(self.temp, 'html')
            # Act
            dirpath2 = core.publisher.publish(self.tree, dirpath)
            # Assert
            self.assertIs(dirpath, dirpath2)
        finally:
            item.delete()

    def test_lines_text_document(self):
        """Verify text can be published from a document."""
        path = os.path.join(FILES, 'published.txt')
        expected = common.read_text(path)
        # Act
        lines = core.publisher.publish_lines(self.document, '.txt')
        text = ''.join(line + '\n' for line in lines)
        # Assert
        if CHECK_PUBLISHED_CONTENT:
            self.assertEqual(expected, text)
        common.write_text(text, path)

    @patch('doorstop.settings.PUBLISH_CHILD_LINKS', False)
    def test_lines_text_document_without_child_links(self):
        """Verify text can be published from a document w/o child links."""
        path = os.path.join(FILES, 'published2.txt')
        expected = common.read_text(path)
        # Act
        lines = core.publisher.publish_lines(self.document, '.txt')
        text = ''.join(line + '\n' for line in lines)
        # Assert
        if CHECK_PUBLISHED_CONTENT:
            self.assertEqual(expected, text)
        common.write_text(text, path)

    def test_lines_markdown_document(self):
        """Verify Markdown can be published from a document."""
        path = os.path.join(FILES, 'published.md')
        expected = common.read_text(path)
        # Act
        lines = core.publisher.publish_lines(self.document, '.md')
        text = ''.join(line + '\n' for line in lines)
        # Assert
        if CHECK_PUBLISHED_CONTENT:
            self.assertEqual(expected, text)
        common.write_text(text, path)

    @patch('doorstop.settings.PUBLISH_CHILD_LINKS', False)
    def test_lines_markdown_document_without_child_links(self):
        """Verify Markdown can be published from a document w/o child links."""
        path = os.path.join(FILES, 'published2.md')
        expected = common.read_text(path)
        # Act
        lines = core.publisher.publish_lines(self.document, '.md')
        text = ''.join(line + '\n' for line in lines)
        # Assert
        if CHECK_PUBLISHED_CONTENT:
            self.assertEqual(expected, text)
        common.write_text(text, path)

    def test_lines_html_document_linkify(self):
        """Verify HTML can be published from a document."""
        path = os.path.join(FILES, 'published.html')
        expected = common.read_text(path)
        # Act
        lines = core.publisher.publish_lines(self.document, '.html',
                                             linkify=True)
        text = ''.join(line + '\n' for line in lines)
        # Assert
        if CHECK_PUBLISHED_CONTENT:
            self.assertEqual(expected, text)
        common.write_text(text, path)

    @patch('doorstop.settings.PUBLISH_CHILD_LINKS', False)
    def test_lines_html_document_without_child_links(self):
        """Verify HTML can be published from a document w/o child links."""
        path = os.path.join(FILES, 'published2.html')
        expected = common.read_text(path)
        # Act
        lines = core.publisher.publish_lines(self.document, '.html')
        text = ''.join(line + '\n' for line in lines)
        # Assert
        if CHECK_PUBLISHED_CONTENT:
            self.assertEqual(expected, text)
        common.write_text(text, path)

    @patch('doorstop.core.document.Document', DocumentNoSkip)
    @patch('doorstop.settings.PUBLISH_CHILD_LINKS', True)
    @patch('doorstop.settings.ENABLE_HEADERS', True)
    def test_lines_html_document_with_header(self):
        """Verify HTML can be published from a document with headers and child links contain header"""
        path = os.path.join(FILES_BETA, 'published3.html')
        expected = common.read_text(path)
        beta_features_tree = core.build(cwd=FILES_BETA, root=FILES_BETA)
        document_with_header = beta_features_tree.find_document('REQHEADER')
        # Act
        lines = core.publisher.publish_lines(document_with_header, '.html',
                                             linkify=True)
        text = ''.join(line + '\n' for line in lines)
        # Assert
        if CHECK_PUBLISHED_CONTENT:
            self.assertEqual(expected, text)
        common.write_text(text, path)


class TestModule(unittest.TestCase):
    """Integration tests for the doorstop.core module."""

    def setUp(self):
        """Reset the internal tree."""
        _clear_tree()

    def test_find_document(self):
        """Verify documents can be found using a convenience function."""
        # Cache miss
        document = core.find_document('req')
        self.assertIsNot(None, document)
        # Cache hit
        document2 = core.find_document('req')
        self.assertIs(document2, document)

    def test_find_item(self):
        """Verify items can be found using a convenience function."""
        # Cache miss
        item = core.find_item('req1')
        self.assertIsNot(None, item)
        # Cache hit
        item2 = core.find_item('req1')
        self.assertIs(item2, item)


# helper functions ###########################################################


def log_data(expected, actual):
    """Log list values."""
    for index, (evalue, avalue) in enumerate(zip(expected, actual)):
        logging.debug("\n{i} expected:\n{e}\n{i} actual:\n{a}".format(
            i=index,
            e=pprint.pformat(evalue),
            a=pprint.pformat(avalue)))


def read_yml(path):
    """Return a dictionary of items from a YAML file."""
    text = common.read_text(path)
    data = yaml.load(text)
    return data


def read_csv(path, delimiter=','):
    """Return a list of rows from a CSV file."""
    rows = []
    try:
        with open(path, 'r', newline='', encoding='utf-8') as stream:
            reader = csv.reader(stream, delimiter=delimiter)
            for row in reader:
                rows.append(row)
    except FileNotFoundError:
        logging.warning("file not found: {}".format(path))
    return rows


def read_xlsx(path):
    """Return a list of workbook data from an XLSX file."""
    data = []

    try:
        workbook = openpyxl.load_workbook(path)
    except openpyxl.exceptions.InvalidFileException:
        logging.warning("file not found: {}".format(path))
    else:
        worksheet = workbook.active
        for row in worksheet.rows:
            for cell in row:
                values = (cell.value,
                          cell.style,
                          worksheet.column_dimensions[cell.column].width)
                data.append(values)
        data.append(worksheet.auto_filter.ref)

    return data


def move_file(src, dst):
    """Move a file from one path to another."""
    common.delete(dst)
    shutil.move(src, dst)
