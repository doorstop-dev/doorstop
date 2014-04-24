"""Tests for the doorstop.core package."""

import unittest
from unittest.mock import patch

import os
import logging

from doorstop import core
from doorstop.common import DoorstopWarning, DoorstopError
from doorstop import settings

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


# TODO: uncomment following line and implement unit tests for coverage
# @unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
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
        document = core.Document.new(EMPTY, FILES, prefix='SYS', digits=4)
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
        document = core.Document.new(EMPTY, FILES, prefix='TMP')
        item_1_0 = document.add_item()
        item_1_2 = document.add_item()  # will get displaced
        item_1_1 = document.add_item(level='1.1')
        self.assertEqual((1, 0), item_1_0.level)
        self.assertEqual((1, 1), item_1_1.level)
        self.assertEqual((1, 2), item_1_2.level)

    def test_remove_item_with_reordering(self):
        """Verify an item can be removed fraom a document."""
        document = core.Document.new(EMPTY, FILES, prefix='TMP')
        item_1_0 = document.add_item()
        item_1_2 = document.add_item()  # to be removed
        item_1_1 = document.add_item()  # will get relocated
        document.remove_item(item_1_2)
        self.assertEqual((1, 0), item_1_0.level)
        self.assertEqual((1, 1), item_1_1.level)

    def test_reorder(self):
        """Verify a document's order can be corrected."""
        document = core.Document.new(EMPTY, FILES, prefix='TMP')
        document.add_item(level='2.0', reorder=False)
        document.add_item(level='2.1', reorder=False)
        document.add_item(level='2.1', reorder=False)
        document.add_item(level='2.5', reorder=False)
        document.add_item(level='4.5', reorder=False)
        document.add_item(level='4.7', reorder=False)
        document.reorder()
        expected = [(2, 0), (2, 1), (2, 2), (2, 3), (3, 0), (3, 1)]
        actual = [item.level for item in document.items]
        self.assertListEqual(expected, actual)

    def test_reorder_with_kept(self):
        """Verify a document's order can be corrected with a kept level."""
        document = core.Document.new(EMPTY, FILES, prefix='TMP')
        document.add_item(level='1.0', reorder=False)
        item = document.add_item(level='1.0', reorder=False)
        document.add_item(level='1.0', reorder=False)
        document.reorder(keep=item)
        expected = [(1, 0), (1, 1), (1, 2)]
        actual = [item.level for item in document.items]
        self.assertListEqual(expected, actual)
        self.assertEqual((1, 0), item.level)

    def test_reorder_with_start(self):
        """Verify a document's order can be corrected with a given start."""
        document = core.Document.new(EMPTY, FILES, prefix='TMP')
        document.add_item(level='2.0', reorder=False)
        document.add_item(level='2.1', reorder=False)
        document.add_item(level='2.1', reorder=False)
        document.add_item(level='2.5', reorder=False)
        document.add_item(level='4.5', reorder=False)
        document.add_item(level='4.7', reorder=False)
        document.reorder(start=(1, 1))
        expected = [(1, 1), (1, 2), (1, 3), (1, 4), (2, 0), (2, 1)]
        actual = [item.level for item in document.items]
        self.assertListEqual(expected, actual)

    def test_validate_with_reordering(self):
        """Verify a document's order is corrected during validation."""
        document = core.Document.new(EMPTY, FILES, prefix='TMP')
        document.add_item(level='1.0', reorder=False)
        document.add_item(level='1.1', reorder=False)
        document.add_item(level='1.2.3', reorder=False)
        document.add_item(level='1.2.5', reorder=False)
        document.add_item(level='3.2.1', reorder=False)
        document.add_item(level='3.3', reorder=False)
        self.assertTrue(document.validate())
        expected = [(1, 0), (1, 1), (1, 1, 0), (1, 1, 1), (2, 0), (2, 1)]
        actual = [item.level for item in document.items]
        self.assertListEqual(expected, actual)


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestTree(unittest.TestCase):  # pylint: disable=R0904

    """Integration tests for the Tree class."""

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
class TestModule(unittest.TestCase):  # pylint: disable=R0904

    """Integration tests for the doorstop.core module."""  # pylint: disable=C0103

    def setUp(self):
        """Reset the internal tree."""
        core.tree._TREE = None  # pylint: disable=W0212

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
