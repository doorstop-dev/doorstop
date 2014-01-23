#!/usr/bin/env python

"""
Unit tests for the doorstop.core.tree module.
"""

import unittest
from unittest.mock import patch, Mock

import os
import tempfile
import operator
import logging

from doorstop.common import DoorstopError
from doorstop.core.tree import Tree, build
from doorstop.core.document import Document

from doorstop.core.test import ENV, REASON, FILES, SYS, EMPTY


class MockDocument(Document):
    """Mock Document class that does not touch the file system."""

    @patch('os.path.isfile', Mock(return_value=True))
    def __init__(self, *args, **kwargs):
        self._file = ""  # file system mock
        self._read = Mock(side_effect=self._mock_read)
        self._write = Mock(side_effect=self._mock_write)
        super().__init__(*args, **kwargs)

    def _mock_read(self):
        """Mock read function."""
        text = self._file
        logging.debug("mock read: {0}".format(repr(text)))
        return text

    def _mock_write(self, text):
        """Mock write function"""
        logging.debug("mock write: {0}".format(repr(text)))
        self._file = text

    _new = Mock()


class MockDocumentNoSkip(MockDocument):
    """Mock Document class that does not touch the file system."""

    SKIP = '__disabled__'  # never skip mock Documents


@patch('doorstop.core.document.Document', MockDocument)  # pylint: disable=R0904
class TestTreeStrings(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for the Tree class using strings."""  # pylint: disable=C0103

    @classmethod
    def setUpClass(cls):
        a = Tree('a', root='.')
        b1 = Tree('b1', parent=a, root='.')
        b2 = Tree('b2', parent=a, root='.')
        c1 = Tree('c1', parent=b2, root='.')
        c2 = Tree('c2', parent=b2, root='.')
        a.children = [b1, b2]
        b2.children = [c1, c2]
        cls.tree = a

    def test_repr(self):
        """Verify trees can be represented."""
        text = "<Tree a <- [ b1, b2 <- [ c1, c2 ] ]>"
        self.assertEqual(text, repr(self.tree))

    def test_str(self):
        """Verify trees can be converted to strings."""
        text = "a <- [ b1, b2 <- [ c1, c2 ] ]"
        self.assertEqual(text, str(self.tree))

    def test_len(self):
        """Verify a tree lengths are correct."""
        self.assertEqual(5, len(self.tree))

    def test_getitem(self):
        """Verify item access is not allowed on trees."""
        self.assertRaises(IndexError, operator.getitem, self.tree, 0)

    def test_iter(self):
        """Verify a tree can be iterated over."""
        items = [d for d in self.tree]
        self.assertListEqual(['a', 'b1', 'b2', 'c1', 'c2'], items)

    def test_contains(self):
        """Verify a tree can be checked for contents."""
        child = self.tree.children[1].children[0]
        self.assertIn(child.document, self.tree)

    def test_from_list(self):
        """Verify a tree can be created from a list."""
        a = MockDocument(EMPTY, _prefix='A')
        b = MockDocument(EMPTY, _prefix='B', _parent='A')
        c = MockDocument(EMPTY, _prefix='C', _parent='B')
        docs = [a, b, c]
        tree = Tree.from_list(docs)
        self.assertEqual(3, len(tree))
        tree.check()

    def test_from_list_no_root(self):
        """Verify an error occurs when the tree has no root."""
        a = MockDocument(EMPTY, _prefix='A', _parent='B')
        b = MockDocument(EMPTY, _prefix='B', _parent='A')
        docs = [a, b]
        self.assertRaises(DoorstopError, Tree.from_list, docs)

    def test_from_list_missing_parent(self):
        """Verify an error occurs when a node has a missing parent."""

        a = MockDocument(EMPTY, _prefix='A')
        b = MockDocument(EMPTY, _prefix='B', _parent='A')
        c = MockDocument(EMPTY, _prefix='C', _parent='?')
        docs = [a, b, c]
        self.assertRaises(DoorstopError, Tree.from_list, docs)


@patch('doorstop.core.document.Document', MockDocument)  # pylint: disable=R0904
@patch('doorstop.core.tree.Document', MockDocument)  # pylint: disable=R0904
class TestTree(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for the Tree class."""  # pylint: disable=C0103

    def setUp(self):
        self.tree = Tree(Document(SYS))
        self.tree._place(Document(FILES))  # pylint: disable=W0212

    @patch('doorstop.core.vcs.find_root', Mock(return_value=EMPTY))
    def test_palce_empty(self):
        """Verify a document can be placed in an empty tree."""
        tree = build(EMPTY)
        doc = MockDocument.new(os.path.join(EMPTY, 'temp'), EMPTY, 'TEMP')
        tree._place(doc)  # pylint: disable=W0212
        self.assertEqual(1, len(tree))

    @patch('doorstop.core.vcs.find_root', Mock(return_value=EMPTY))
    def test_palce_empty_no_parent(self):
        """Verify a document with parent cannot be placed in an empty tree."""
        tree = build(EMPTY)
        doc = MockDocument.new(os.path.join(EMPTY, 'temp'), EMPTY, 'TEMP',
                               parent='REQ')
        self.assertRaises(DoorstopError, tree._place, doc)  # pylint: disable=W0212

    @patch('doorstop.core.document.Document.check')
    def test_check(self, mock_check):
        """Verify trees can be checked."""
        logging.info("tree: {}".format(self.tree))
        self.tree.check()
        self.assertEqual(2, mock_check.call_count)

    @unittest.skipUnless(os.getenv(ENV), REASON)
    def test_check_long(self):
        """Verify trees can be checked (long)."""
        logging.info("tree: {}".format(self.tree))
        self.tree.check()

    def test_new(self):
        """Verify a new document can be created on a tree."""
        self.tree.new(EMPTY, '_TEST', parent='REQ')

    def test_new_unknown_parent(self):
        """Verify an exception is raised for an unknown parent."""
        temp = tempfile.mkdtemp()
        self.assertRaises(DoorstopError, self.tree.new,
                          temp, '_TEST', parent='UNKNOWN')
        self.assertFalse(os.path.exists(temp))

    @patch('doorstop.core.vcs.veracity.WorkingCopy.lock')
    @patch('doorstop.core.document.Document.add')
    def test_add(self, mock_add, mock_lock):
        """Verify an item can be added to a document."""
        self.tree.add('REQ')
        mock_add.assert_called_once_with()
        path = os.path.join(FILES, '.doorstop.yml')
        mock_lock.assert_called_once_with(path)

    def test_add_unknown_prefix(self):
        """Verify an exception is raised for an unknown prefix (item)."""
        self.assertRaises(DoorstopError, self.tree.add, 'UNKNOWN')

    @patch('doorstop.core.item.Item.delete')
    def test_remove(self, mock_delete):
        """Verify an item can be removed from a document."""
        self.tree.remove('req1')
        mock_delete.assert_called_once_with()

    def test_remove_unknown_item(self):
        """Verify an exception is raised removing an unknown item."""
        self.assertRaises(DoorstopError, self.tree.remove, 'req9999')

    @patch('doorstop.core.item.Item.add_link')
    def test_link(self, mock_add_link):
        """Verify two items can be linked."""
        self.tree.link('req1', 'req2')
        mock_add_link.assert_called_once_with('REQ002')

    def test_link_unknown_child_prefix(self):
        """Verify an exception is raised with an unknown child prefix."""
        self.assertRaises(DoorstopError, self.tree.link, 'unknown1', 'req2')

    def test_link_unknown_child_number(self):
        """Verify an exception is raised with an unknown child number."""
        self.assertRaises(DoorstopError, self.tree.link, 'req9999', 'req2')

    def test_link_unknown_parent_prefix(self):
        """Verify an exception is raised with an unknown parent prefix."""
        self.assertRaises(DoorstopError, self.tree.link, 'req1', 'unknown1')

    def test_link_unknown_parent_number(self):
        """Verify an exception is raised with an unknown parent prefix."""
        self.assertRaises(DoorstopError, self.tree.link, 'req1', 'req9999')

    @patch('doorstop.core.item.Item.remove_link')
    def test_unlink(self, mock_add_link):
        """Verify two items can be unlinked."""
        self.tree.unlink('req3', 'req1')
        mock_add_link.assert_called_once_with('REQ001')

    def test_unlink_unknown_child_prefix(self):
        """Verify an exception is raised with an unknown child prefix."""
        self.assertRaises(DoorstopError, self.tree.unlink, 'unknown1', 'req1')

    def test_unlink_unknown_child_number(self):
        """Verify an exception is raised with an unknown child number."""
        self.assertRaises(DoorstopError, self.tree.unlink, 'req9999', 'req1')

    def test_unlink_unknown_parent_prefix(self):
        """Verify an exception is raised with an unknown parent prefix."""
        self.assertRaises(DoorstopError, self.tree.unlink, 'req3', 'unknown1')

    def test_unlink_unknown_parent_number(self):
        """Verify an exception is raised with an unknown parent prefix."""
        self.assertRaises(DoorstopError, self.tree.unlink, 'req3', 'req9999')

    @patch('doorstop.core.vcs.veracity.WorkingCopy.lock')
    @patch('doorstop.core.tree._open')
    def test_edit(self, mock_open, mock_lock):
        """Verify an item can be edited in a tree."""
        self.tree.edit('req2', launch=True)
        path = os.path.join(FILES, 'REQ002.yml')
        mock_open.assert_called_once_with(path, tool=None)
        mock_lock.assert_called_once_with(path)

    def test_edit_unknown_prefix(self):
        """Verify an exception is raised for an unknown prefix (document)."""
        self.assertRaises(DoorstopError, self.tree.edit, 'unknown1')

    def test_edit_unknown_number(self):
        """Verify an exception is raised for an unknown number."""
        self.assertRaises(DoorstopError, self.tree.edit, 'req9999')

    def test_find_item(self):
        """Verify an item can be found by exact ID."""
        item = self.tree.find_item('req2-001')
        self.assertIsNot(None, item)


class TestModule(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for the doorstop.core.tree module."""  # pylint: disable=C0103

    @patch('doorstop.core.vcs.find_root', Mock(return_value=EMPTY))
    def test_run_empty(self):
        """Verify an empty directory is an empty hiearchy."""
        tree = build(EMPTY)
        self.assertEqual(0, len(tree))

    @patch('doorstop.core.document.Document', MockDocumentNoSkip)
    @patch('doorstop.core.vcs.find_root', Mock(return_value=FILES))
    def test_build(self):
        """Verify a tree can be built."""
        tree = build(FILES)
        self.assertEqual(3, len(tree))

    @patch('doorstop.core.document.Document', MockDocument)
    @patch('doorstop.core.vcs.find_root', Mock(return_value=FILES))
    def test_build_with_skips(self):
        """Verify documents can be skipped while building a tree."""
        tree = build(FILES)
        self.assertEqual(0, len(tree))


if __name__ == '__main__':
    unittest.main()
