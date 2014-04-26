"""Unit tests for the doorstop.core.tree module."""

import unittest
from unittest.mock import patch, Mock, MagicMock

import os
import tempfile
import operator
import logging

from doorstop.common import DoorstopError, DoorstopWarning, DoorstopInfo
from doorstop.core.tree import Tree, build, find_document, find_item
from doorstop.core.document import Document

from doorstop.core.test import FILES, SYS, EMPTY
from doorstop.core.test.test_document import MockDocument as _MockDocment


class MockDocument(_MockDocment):  # pylint: disable=W0223,R0902,R0904

    """Mock Document class that is always skipped in tree placement."""

    skip = True


class MockDocumentNoSkip(MockDocument):  # pylint: disable=W0223,R0902,R0904

    """Mock Document class that is never skipped in tree placement."""

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
        a = MockDocument(EMPTY)
        a.prefix = 'A'
        b = MockDocument(EMPTY)
        b.prefix = 'B'
        b.parent = 'A'
        c = MockDocument(EMPTY)
        c.prefix = 'C'
        c.parent = 'B'
        docs = [a, b, c]
        tree = Tree.from_list(docs)
        self.assertEqual(3, len(tree))
        self.assertTrue(tree.validate())

    def test_from_list_no_root(self):
        """Verify an error occurs when the tree has no root."""
        a = MockDocument(EMPTY)
        a.prefix = 'A'
        a.parent = 'B'
        b = MockDocument(EMPTY)
        b.prefix = 'B'
        b.parent = 'A'
        docs = [a, b]
        self.assertRaises(DoorstopError, Tree.from_list, docs)

    def test_from_list_multiple_roots(self):
        """Verify an error occurs when the tree has multiple roots."""
        a = MockDocument(EMPTY)
        a.prefix = 'A'
        b = MockDocument(EMPTY)
        b.prefix = 'B'
        docs = [a, b]
        self.assertRaises(DoorstopError, Tree.from_list, docs)

    def test_from_list_missing_parent(self):
        """Verify an error occurs when a node has a missing parent."""

        a = MockDocument(EMPTY)
        a.prefix = 'A'
        b = MockDocument(EMPTY)
        b.prefix = 'B'
        b.parent = 'A'
        c = MockDocument(EMPTY)
        c.prefix = 'C'
        c.parent = '?'
        docs = [a, b, c]
        self.assertRaises(DoorstopError, Tree.from_list, docs)

    def test_place_no_parent(self):
        """Verify an error occurs when a node is missing a parent."""

        a = MockDocument(EMPTY)
        a.prefix = 'A'
        b = MockDocument(EMPTY)
        b.prefix = 'B'
        tree = Tree(a)
        self.assertRaises(DoorstopError, tree._place, b)  # pylint: disable=W0212


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

    @patch('doorstop.core.document.Document.get_issues')
    def test_validate(self, mock_get_issues):
        """Verify trees can be checked."""
        logging.info("tree: {}".format(self.tree))
        self.assertTrue(self.tree.validate())
        self.assertEqual(2, mock_get_issues.call_count)

    def test_validate_no_documents(self):
        """Verify an empty tree can be checked."""
        tree = Tree(None, root='.')
        self.assertTrue(tree.validate())

    @patch('doorstop.core.item.Item.get_issues',
           Mock(return_value=[DoorstopError('error'),
                              DoorstopWarning('warning'),
                              DoorstopInfo('info')]))
    def test_validate_document(self):
        """Verify an document error fails the tree validation."""
        self.assertFalse(self.tree.validate())

    @patch('doorstop.core.document.Document.get_issues', Mock(return_value=[]))
    def test_validate_hook(self):
        """Verify a document hook can be called."""
        mock_hook = MagicMock()
        self.tree.validate(document_hook=mock_hook)
        self.assertEqual(2, mock_hook.call_count)

    @patch('doorstop.core.tree.Tree.get_issues', Mock(return_value=[]))
    def test_issues(self):
        """Verify an tree's issues convenience property can be accessed."""
        self.assertEqual(0, len(self.tree.issues))

    def test_new_document(self):
        """Verify a new document can be created on a tree."""
        self.tree.new_document(EMPTY, '_TEST', parent='REQ')

    def test_new_document_unknown_parent(self):
        """Verify an exception is raised for an unknown parent."""
        temp = tempfile.mkdtemp()
        self.assertRaises(DoorstopError, self.tree.new_document,
                          temp, '_TEST', parent='UNKNOWN')
        self.assertFalse(os.path.exists(temp))

    @patch('doorstop.core.vcs.git.WorkingCopy.lock')
    @patch('doorstop.core.document.Document.add_item')
    def test_add_item(self, mock_add_item, mock_lock):
        """Verify an item can be added to a document."""
        self.tree.add_item('REQ')
        mock_add_item.assert_called_once_with(level=None)
        path = os.path.join(FILES, '.doorstop.yml')
        mock_lock.assert_called_once_with(path)

    @patch('doorstop.core.vcs.git.WorkingCopy.lock')
    @patch('doorstop.core.document.Document.add_item')
    def test_add_item_level(self, mock_add, mock_lock):
        """Verify an item can be added to a document with a level."""
        self.tree.add_item('REQ', level='1.2.3')
        mock_add.assert_called_once_with(level='1.2.3')
        path = os.path.join(FILES, '.doorstop.yml')
        mock_lock.assert_called_once_with(path)

    def test_add_item_unknown_prefix(self):
        """Verify an exception is raised for an unknown prefix (item)."""
        # Cache miss
        self.assertRaises(DoorstopError, self.tree.add_item, 'UNKNOWN')
        # Cache hit
        self.assertRaises(DoorstopError, self.tree.add_item, 'UNKNOWN')

    @patch('doorstop.core.item.Item.delete')
    def test_remove_item(self, mock_delete):
        """Verify an item can be removed from a document."""
        self.tree.remove_item('req1')
        mock_delete.assert_called_once_with()

    def test_remove_item_unknown_item(self):
        """Verify an exception is raised removing an unknown item."""
        self.assertRaises(DoorstopError, self.tree.remove_item, 'req9999')

    @patch('doorstop.core.item.Item.link')
    def test_link_items(self, mock_link):
        """Verify two items can be linked."""
        self.tree.link_items('req1', 'req2')
        mock_link.assert_called_once_with('REQ002')

    def test_link_items_unknown_child_prefix(self):
        """Verify an exception is raised with an unknown child prefix."""
        self.assertRaises(DoorstopError,
                          self.tree.link_items, 'unknown1', 'req2')

    def test_link_items_unknown_child_number(self):
        """Verify an exception is raised with an unknown child number."""
        self.assertRaises(DoorstopError,
                          self.tree.link_items, 'req9999', 'req2')

    def test_link_items_unknown_parent_prefix(self):
        """Verify an exception is raised with an unknown parent prefix."""
        self.assertRaises(DoorstopError,
                          self.tree.link_items, 'req1', 'unknown1')

    def test_link_items_unknown_parent_number(self):
        """Verify an exception is raised with an unknown parent prefix."""
        self.assertRaises(DoorstopError,
                          self.tree.link_items, 'req1', 'req9999')

    @patch('doorstop.core.item.Item.unlink')
    def test_unlink_items(self, mock_unlink):
        """Verify two items can be unlinked."""
        self.tree.unlink_items('req3', 'req1')
        mock_unlink.assert_called_once_with('REQ001')

    def test_unlink_items_unknown_child_prefix(self):
        """Verify an exception is raised with an unknown child prefix."""
        self.assertRaises(DoorstopError,
                          self.tree.unlink_items, 'unknown1', 'req1')

    def test_unlink_items_unknown_child_number(self):
        """Verify an exception is raised with an unknown child number."""
        self.assertRaises(DoorstopError,
                          self.tree.unlink_items, 'req9999', 'req1')

    def test_unlink_items_unknown_parent_prefix(self):
        """Verify an exception is raised with an unknown parent prefix."""
        # Cache miss
        self.assertRaises(DoorstopError,
                          self.tree.unlink_items, 'req3', 'unknown1')
        # Cache hit
        self.assertRaises(DoorstopError,
                          self.tree.unlink_items, 'req3', 'unknown1')

    def test_unlink_items_unknown_parent_number(self):
        """Verify an exception is raised with an unknown parent prefix."""
        self.assertRaises(DoorstopError,
                          self.tree.unlink_items, 'req3', 'req9999')

    @patch('doorstop.core.vcs.git.WorkingCopy.lock')
    @patch('doorstop.core.tree._open')
    def test_edit_item(self, mock_open, mock_lock):
        """Verify an item can be edited in a tree."""
        self.tree.edit_item('req2', launch=True)
        path = os.path.join(FILES, 'REQ002.yml')
        mock_open.assert_called_once_with(path, tool=None)
        mock_lock.assert_called_once_with(path)

    def test_edit_item_unknown_prefix(self):
        """Verify an exception is raised for an unknown prefix (document)."""
        self.assertRaises(DoorstopError, self.tree.edit_item, 'unknown1')

    def test_edit_item_unknown_number(self):
        """Verify an exception is raised for an unknown number."""
        self.assertRaises(DoorstopError, self.tree.edit_item, 'req9999')

    def test_find_item(self):
        """Verify an item can be found by exact ID."""
        # Cache miss
        item = self.tree.find_item('req2-001')
        self.assertIsNot(None, item)
        # Cache hit
        item2 = self.tree.find_item('req2-001')
        self.assertIs(item2, item)

    def test_find_document(self):
        """Verify an document can be found by prefix"""
        # Cache miss
        document = self.tree.find_document('req')
        self.assertIsNot(None, document)
        # Cache hit
        document2 = self.tree.find_document('req')
        self.assertIs(document2, document)

    def test_load(self):
        """Verify an a tree can be reloaded."""
        self.tree.load()
        self.tree.load()  # should return immediately

    @patch('doorstop.core.document.Document.delete')
    def test_delete(self, mock_delete):
        """Verify a tree can be deleted."""
        self.tree.delete()
        self.assertEqual(0, len(self.tree))
        self.assertEqual(2, mock_delete.call_count)
        self.tree.delete()  # ensure a second delete is ignored


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

    @patch('doorstop.core.tree.build', Mock(return_value=Tree(Mock())))
    @patch('doorstop.core.tree.Tree.find_document')
    def test_find_document(self, mock_find_document):  # pylint: disable=R0201
        """Verify documents can be found using a convenience function."""
        from doorstop.core import tree
        tree._TREE = None  # pylint: disable=W0212
        prefix = 'req'
        find_document(prefix)
        mock_find_document.assert_called_once_with(prefix)

    @patch('doorstop.core.tree.build', Mock(return_value=Tree(Mock())))
    @patch('doorstop.core.tree.Tree.find_item')
    def test_find_item(self, mock_find_item):  # pylint: disable=R0201
        """Verify items can be found using a convenience function."""
        from doorstop.core import tree
        tree._TREE = None  # pylint: disable=W0212
        identifier = 'req1'
        find_item(identifier)
        mock_find_item.assert_called_once_with(identifier)
