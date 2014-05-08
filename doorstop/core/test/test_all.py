"""Tests for the doorstop.core package."""

import unittest
from unittest.mock import patch

import os
import tempfile
import shutil
import logging

from doorstop import core
from doorstop import common
from doorstop.common import DoorstopWarning, DoorstopError

from doorstop.core.test import ENV, REASON, ROOT, FILES, EMPTY, SYS


class DocumentNoSkip(core.Document):  # pylint: disable=R0904

    """Document class that is never skipped."""

    SKIP = '__disabled__'  # never skip test Documents


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestItem(unittest.TestCase):  # pylint: disable=R0904

    """Integration tests for the Item class."""  # pylint: disable=C0103

    def setUp(self):
        self.path = os.path.join(FILES, 'REQ001.yml')
        with open(self.path, 'r') as item:
            self.backup = item.read()
        self.item = core.Item(self.path)

    def tearDown(self):
        with open(self.path, 'w') as item:
            item.write(self.backup)

    def test_save_load(self):
        """Verify an item can be saved and loaded from a file."""
        self.item.level = '1.2.3'
        self.item.text = "Hello, world!"
        self.item.links = ['SYS001', 'SYS002']
        item2 = core.Item(os.path.join(FILES, 'REQ001.yml'))
        self.assertEqual((1, 2, 3), item2.level)
        self.assertEqual("Hello, world!", item2.text)
        self.assertEqual(['SYS001', 'SYS002'], item2.links)

    def test_find_ref(self):
        """Verify an item's external reference can be found."""
        item = core.Item(os.path.join(FILES, 'REQ003.yml'))
        path, line = item.find_ref()
        relpath = os.path.relpath(os.path.join(FILES, 'external', 'text.txt'),
                                  ROOT)
        self.assertEqual(relpath, path)
        self.assertEqual(3, line)

    def test_find_ref_error(self):
        """Verify an error occurs when no external reference found."""
        self.item.ref = "not found".replace(' ', '')  # avoids self match
        self.assertRaises(DoorstopError, self.item.find_ref)


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestDocument(unittest.TestCase):  # pylint: disable=R0904

    """Integration tests for the Document class."""  # pylint: disable=C0103

    def setUp(self):
        self.document = core.Document(FILES, root=ROOT)

    def tearDown(self):
        """Clean up temporary files."""
        for filename in os.listdir(EMPTY):
            path = os.path.join(EMPTY, filename)
            os.remove(path)

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
    def test_validate(self):
        """Verify a document can be validated."""
        self.assertTrue(self.document.validate())

    @patch('doorstop.settings.REORDER', False)
    def test_issues_count(self):
        """Verify a number of issues are found in a document."""
        issues = self.document.issues
        for issue in self.document.issues:
            logging.info(repr(issue))
        self.assertEqual(8, len(issues))

    @patch('doorstop.settings.REORDER', False)
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
    def test_issues_skipped_level(self):
        """Verify skipped item levels are detected."""
        expect = DoorstopWarning("skipped level: 1.4 (REQ003), 1.6 (REQ004)")
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
        item_3_0 = document.add_item()  # will get displaced
        item_2_0 = document.add_item(level='2.0')
        self.assertEqual((1, 0), item_1_0.level)
        self.assertEqual((2, 0), item_2_0.level)
        self.assertEqual((3, 0), item_3_0.level)

    def test_remove_item_with_reordering(self):
        """Verify an item can be removed fraom a document."""
        document = core.Document.new(None,
                                     EMPTY, FILES,
                                     prefix='TMP')
        item_1_0 = document.add_item()
        item_3_0 = document.add_item()  # to be removed
        item_2_0 = document.add_item()  # will get relocated
        document.remove_item(item_3_0)
        self.assertEqual((1, 0), item_1_0.level)
        self.assertEqual((2, 0), item_2_0.level)

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
        actual = [item.level for item in document.items]
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


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestTree(unittest.TestCase):  # pylint: disable=R0904

    """Integration tests for the core.Tree class."""

    def setUp(self):
        self.path = os.path.join(FILES, 'REQ001.yml')
        with open(self.path, 'r') as item:
            self.backup = item.read()
        self.item = core.Item(self.path)
        self.tree = core.Tree(core.Document(SYS))
        self.tree._place(core.Document(FILES))  # pylint: disable=W0212

    def tearDown(self):
        with open(self.path, 'w') as item:
            item.write(self.backup)

    @patch('doorstop.settings.REORDER', False)
    @patch('doorstop.core.document.Document', DocumentNoSkip)
    def test_validate_invalid_link(self):
        """Verify a tree is invalid with a bad link."""
        self.item.link('SYS003')
        tree = core.build(FILES, root=FILES)
        self.assertIsInstance(tree, core.Tree)
        self.assertFalse(tree.validate())

    @patch('doorstop.settings.REORDER', False)
    def test_validate_long(self):
        """Verify trees can be checked."""
        logging.info("tree: {}".format(self.tree))
        self.assertTrue(self.tree.validate())


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestImporter(unittest.TestCase):  # pylint: disable=R0904

    """Integrations tests for the importer module."""  # pylint: disable=C0103

    def setUp(self):
        # Create a temporary mock working copy
        self.cwd = os.getcwd()
        self.temp = tempfile.mkdtemp()
        os.chdir(self.temp)
        open(".mockvcs", 'w').close()
        # Create default document attributes
        self.prefix = 'PREFIX'
        self.root = self.temp
        self.path = os.path.join(self.root, 'DIRECTORY')
        self.parent = 'PARENT_PREFIX'
        # Create default item attributes
        self.identifier = 'PREFIX-00042'
        # Ensure the tree is reloaded
        common._tree = None  # pylint: disable=W0212

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.temp)

    def test_create_document(self):
        """Verify a new document can be created to import items."""
        document = core.importer.new_document(self.prefix, self.path)
        self.assertEqual(self.prefix, document.prefix)
        self.assertEqual(self.path, document.path)

    def test_create_document_with_unknown_parent(self):
        """Verify a new document can be created with an unknown parent."""
        # Verify the document does not already exist
        self.assertRaises(DoorstopError, core.find_document, self.prefix)
        # Import a document
        document = core.importer.new_document(self.prefix, self.path,
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
        core.importer.new_document(self.prefix, self.path)
        # Attempt to create the same document
        self.assertRaises(DoorstopError,
                          core.importer.new_document, self.prefix, self.path)

    def test_add_item(self):
        """Verify an item can be imported into a document."""
        # Create a document
        core.importer.new_document(self.prefix, self.path)
        # Verify the item does not already exist
        self.assertRaises(DoorstopError, core.find_item, self.identifier)
        # Import an item
        item = core.importer.add_item(self.prefix, self.identifier)
        # Verify the item's attributes are correct
        self.assertEqual(self.identifier, item.id)
        # Verify the item can be found
        item2 = core.find_item(self.identifier)
        self.assertIs(item, item2)
        # Verify the item is contained in the document
        document = core.find_document(self.prefix)
        self.assertIn(item, document.items)

    def test_add_item_with_attrs(self):
        """Verify an item with attributes can be imported into a document."""
        # Create a document
        core.importer.new_document(self.prefix, self.path)
        # Import an item
        attrs = {'text': "Item text", 'ext1': "Extended 1"}
        item = core.importer.add_item(self.prefix, self.identifier,
                                      attrs=attrs)
        # Verify the item is correct
        self.assertEqual(self.identifier, item.id)
        self.assertEqual(attrs['text'], item.text)
        self.assertEqual(attrs['ext1'], item.get('ext1'))


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestModule(unittest.TestCase):  # pylint: disable=R0904

    """Integration tests for the doorstop.core module."""  # pylint: disable=C0103

    def setUp(self):
        """Reset the internal tree."""
        common._tree = None  # pylint: disable=W0212

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
