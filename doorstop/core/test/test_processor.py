#!/usr/bin/env python

"""
Unit tests for the doorstop.core.processor module.
"""

import unittest
from unittest.mock import patch, Mock

import os
import tempfile
import operator
import logging

from doorstop.common import DoorstopError
from doorstop.core import processor
from doorstop.core.processor import Node
from doorstop.core.document import Document

from doorstop.core.test import FILES, EMPTY


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
class TestNodeStrings(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for the Node class using strings."""  # pylint: disable=C0103

    @classmethod
    def setUpClass(cls):
        a = Node('a')
        b1 = Node('b1', parent=a)
        b2 = Node('b2', parent=a)
        c1 = Node('c1', parent=b2)
        c2 = Node('c2', parent=b2)
        a.children = [b1, b2]
        b2.children = [c1, c2]
        cls.tree = a

    def test_repr(self):
        """Verify trees can be represented."""
        text = "<Node a <- [ b1, b2 <- [ c1, c2 ] ]>"
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
        tree = Node.from_list(docs)
        self.assertEqual(3, len(tree))
        tree.check()

    def test_from_list_no_root(self):
        """Verify an error occurs when the tree has no root."""
        a = MockDocument(EMPTY, _prefix='A', _parent='B')
        b = MockDocument(EMPTY, _prefix='B', _parent='A')
        docs = [a, b]
        self.assertRaises(DoorstopError, Node.from_list, docs)

    def test_from_list_missing_parent(self):
        """Verify an error occurs when a node has a missing parent."""

        a = MockDocument(EMPTY, _prefix='A')
        b = MockDocument(EMPTY, _prefix='B', _parent='A')
        c = MockDocument(EMPTY, _prefix='C', _parent='?')
        docs = [a, b, c]
        self.assertRaises(DoorstopError, Node.from_list, docs)


@patch('doorstop.core.document.Document', MockDocument)  # pylint: disable=R0904
@patch('doorstop.core.processor.Document', MockDocument)  # pylint: disable=R0904
class TestNode(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for the Node class."""  # pylint: disable=C0103

    def setUp(self):
        self.tree = Node(MockDocument(FILES))

    def test_check(self):
        """Verify document trees can be checked."""
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

    @patch('doorstop.core.document.Document.add')
    def test_add(self, mock_add):
        """Verify an item can be added to a document."""
        self.tree.add('REQ')
        mock_add.assert_called_once_with()

    def test_add_unknown_prefix(self):
        """Verify an exception is raised for an unknown prefix (item)."""
        self.assertRaises(DoorstopError, self.tree.add, 'UNKNOWN')

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

    @patch('doorstop.core.processor._open')
    def test_edit(self, mock_open):
        """Verify an item can be edited in a tree."""
        self.tree.edit('req2', launch=True)
        mock_open.assert_called_once_with(os.path.join(FILES, 'REQ002.yml'))

    def test_edit_unknown_prefix(self):
        """Verify an exception is rasied for an unknown prefix (document)."""
        self.assertRaises(DoorstopError, self.tree.edit, 'unknown1')

    def test_edit_unknown_number(self):
        """Verify an exception is rasied for an unknown number."""
        self.assertRaises(DoorstopError, self.tree.edit, 'req9999')


class TestModule(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for the doorstop.core.processor module."""  # pylint: disable=C0103

    @patch('doorstop.core.vcs.find_root', Mock(return_value=EMPTY))
    def test_run_empty(self):
        """Verify an empty directory is an invalid hiearchy."""
        self.assertRaises(DoorstopError, processor.build, EMPTY)

    @patch('doorstop.core.processor.build', Mock())
    def test_run(self):
        """Verify a valid tree passes the processor."""
        tree = processor.build(FILES)
        self.assertTrue(tree.check())

    @patch('doorstop.core.document.Document', MockDocumentNoSkip)
    @patch('doorstop.core.vcs.find_root', Mock(return_value=FILES))
    def test_build(self):
        """Verify a tree can be built."""
        tree = processor.build(FILES)
        self.assertEqual(2, len(tree))

    @patch('doorstop.core.document.Document', MockDocument)
    @patch('doorstop.core.vcs.find_root', Mock(return_value=FILES))
    def test_build_with_skips(self):
        """Verify documents can be skipped while building a tree."""
        self.assertRaises(DoorstopError, processor.build, FILES)


if __name__ == '__main__':
    unittest.main()
