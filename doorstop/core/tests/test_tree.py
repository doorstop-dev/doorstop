#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.core.tree module."""

import logging
import operator
import os
import tempfile
import unittest
from unittest.mock import MagicMock, Mock, patch

from doorstop.common import DoorstopError, DoorstopInfo, DoorstopWarning
from doorstop.core.builder import build
from doorstop.core.document import Document
from doorstop.core.tests import EMPTY, FILES, SYS, MockDocumentSkip
from doorstop.core.tree import Tree


@patch('doorstop.core.document.Document', MockDocumentSkip)
class TestTreeStrings(unittest.TestCase):
    """Unit tests for the Tree class using strings."""

    @classmethod
    def setUpClass(cls):
        a = Tree('a', root='.')
        b1 = Tree('b1', parent=a, root='.')
        d = Tree('d', parent=b1, root='.')
        e = Tree('e', parent=d, root='.')
        b2 = Tree('b2', parent=a, root='.')
        c1 = Tree('c1', parent=b2, root='.')
        c2 = Tree('c2', parent=b2, root='.')
        a.children = [b1, b2]
        b1.children = [d]
        d.children = [e]
        b2.children = [c1, c2]
        cls.tree = a

    def test_repr(self):
        """Verify trees can be represented."""
        text = "<Tree a <- [ b1 <- [ d <- [ e ] ], b2 <- [ c1, c2 ] ]>"
        self.assertEqual(text, repr(self.tree))

    def test_str(self):
        """Verify trees can be converted to strings."""
        text = "a <- [ b1 <- [ d <- [ e ] ], b2 <- [ c1, c2 ] ]"
        self.assertEqual(text, str(self.tree))

    def test_len(self):
        """Verify a tree lengths are correct."""
        self.assertEqual(7, len(self.tree))

    def test_getitem(self):
        """Verify item access is not allowed on trees."""
        self.assertRaises(IndexError, operator.getitem, self.tree, 0)

    def test_iter(self):
        """Verify a tree can be iterated over."""
        items = [d for d in self.tree]
        self.assertListEqual(['a', 'b1', 'd', 'e', 'b2', 'c1', 'c2'], items)

    def test_contains(self):
        """Verify a tree can be checked for contents."""
        child = self.tree.children[1].children[0]
        self.assertIn(child.document, self.tree)

    def test_draw_utf8(self):
        """Verify trees structure can be drawn (UTF-8)."""
        text = (
            "a" + '\n'
            "│   " + '\n'
            "├── b1" + '\n'
            "│   │   " + '\n'
            "│   └── d" + '\n'
            "│       │   " + '\n'
            "│       └── e" + '\n'
            "│   " + '\n'
            "└── b2" + '\n'
            "    │   " + '\n'
            "    ├── c1" + '\n'
            "    │   " + '\n'
            "    └── c2"
        )
        logging.debug('expected:\n%s', text)
        text2 = self.tree.draw(encoding='UTF-8')
        logging.debug('actual:\n%s', text2)
        self.assertEqual(text, text2)

    def test_draw_cp437(self):
        """Verify trees structure can be drawn (cp437)."""
        text = (
            "a" + '\n'
            "┬   " + '\n'
            "├── b1" + '\n'
            "│   ┬   " + '\n'
            "│   └── d" + '\n'
            "│       ┬   " + '\n'
            "│       └── e" + '\n'
            "│   " + '\n'
            "└── b2" + '\n'
            "    ┬   " + '\n'
            "    ├── c1" + '\n'
            "    │   " + '\n'
            "    └── c2"
        )
        logging.debug('expected:\n%s', text)
        text2 = self.tree.draw(encoding='cp437')
        logging.debug('actual:\n%s', text2)
        self.assertEqual(text, text2)

    def test_draw_unknown(self):
        """Verify trees structure can be drawn (unknown)."""
        text = (
            "a" + '\n'
            "|   " + '\n'
            "+-- b1" + '\n'
            "|   |   " + '\n'
            "|   +-- d" + '\n'
            "|       |   " + '\n'
            "|       +-- e" + '\n'
            "|   " + '\n'
            "+-- b2" + '\n'
            "    |   " + '\n'
            "    +-- c1" + '\n'
            "    |   " + '\n'
            "    +-- c2"
        )
        logging.debug('expected:\n%s', text)
        text2 = self.tree.draw(encoding='unknown')
        logging.debug('actual:\n%s', text2)
        self.assertEqual(text, text2)

    @patch('doorstop.settings.REORDER', False)
    def test_from_list(self):
        """Verify a tree can be created from a list."""
        a = MockDocumentSkip(EMPTY)
        a.prefix = 'A'  # type: ignore
        b = MockDocumentSkip(EMPTY)
        b.prefix = 'B'  # type: ignore
        b.parent = 'A'  # type: ignore
        c = MockDocumentSkip(EMPTY)
        c.prefix = 'C'  # type: ignore
        c.parent = 'B'  # type: ignore
        docs = [a, b, c]
        tree = Tree.from_list(docs)
        self.assertEqual(3, len(tree))
        self.assertTrue(tree.validate())

    def test_from_list_no_root(self):
        """Verify an error occurs when the tree has no root."""
        a = MockDocumentSkip(EMPTY)
        a.prefix = 'A'  # type: ignore
        a.parent = 'B'  # type: ignore
        b = MockDocumentSkip(EMPTY)
        b.prefix = 'B'  # type: ignore
        b.parent = 'A'  # type: ignore
        docs = [a, b]
        self.assertRaises(DoorstopError, Tree.from_list, docs)

    def test_from_list_multiple_roots(self):
        """Verify an error occurs when the tree has multiple roots."""
        a = MockDocumentSkip(EMPTY)
        a.prefix = 'A'  # type: ignore
        b = MockDocumentSkip(EMPTY)
        b.prefix = 'B'  # type: ignore
        docs = [a, b]
        self.assertRaises(DoorstopError, Tree.from_list, docs)

    def test_from_list_missing_parent(self):
        """Verify an error occurs when a node has a missing parent."""
        a = MockDocumentSkip(EMPTY)
        a.prefix = 'A'  # type: ignore
        b = MockDocumentSkip(EMPTY)
        b.prefix = 'B'  # type: ignore
        b.parent = 'A'  # type: ignore
        c = MockDocumentSkip(EMPTY)
        c.prefix = 'C'  # type: ignore
        c.parent = '?'  # type: ignore
        docs = [a, b, c]
        self.assertRaises(DoorstopError, Tree.from_list, docs)

    def test_place_no_parent(self):
        """Verify an error occurs when a node is missing a parent."""
        a = MockDocumentSkip(EMPTY)
        a.prefix = 'A'  # type: ignore
        b = MockDocumentSkip(EMPTY)
        b.prefix = 'B'  # type: ignore
        tree = Tree(a)
        self.assertRaises(DoorstopError, tree._place, b)  # pylint: disable=W0212


@patch('doorstop.core.document.Document', MockDocumentSkip)
@patch('doorstop.core.tree.Document', MockDocumentSkip)
class TestTree(unittest.TestCase):
    """Unit tests for the Tree class."""

    def setUp(self):
        document = Document(SYS)
        self.tree = Tree(document)
        document.tree = self.tree
        document = Document(FILES)
        self.tree._place(document)  # pylint: disable=W0212
        document.tree = self.tree
        self.tree._vcs = Mock()  # pylint: disable=W0212

    @patch('doorstop.core.vcs.find_root', Mock(return_value=EMPTY))
    def test_place_empty(self):
        """Verify a document can be placed in an empty tree."""
        tree = build(EMPTY)
        doc = MockDocumentSkip.new(tree, os.path.join(EMPTY, 'temp'), EMPTY, 'TEMP')
        tree._place(doc)  # pylint: disable=W0212
        self.assertEqual(1, len(tree))

    @patch('doorstop.core.vcs.find_root', Mock(return_value=EMPTY))
    def test_place_empty_no_parent(self):
        """Verify a document with parent cannot be placed in an empty tree."""
        tree = build(EMPTY)
        doc = MockDocumentSkip.new(
            tree, os.path.join(EMPTY, 'temp'), EMPTY, 'TEMP', parent='REQ'
        )
        self.assertRaises(DoorstopError, tree._place, doc)  # pylint: disable=W0212

    def test_documents(self):
        """Verify the documents in a tree can be accessed."""
        documents = self.tree.documents
        self.assertEqual(2, len(documents))
        for document in self.tree:
            logging.debug("document: {}".format(document))
            self.assertIs(self.tree, document.tree)

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

    @patch('doorstop.settings.REORDER', False)
    @patch(
        'doorstop.core.document.Document.get_issues',
        Mock(
            return_value=[
                DoorstopError('error'),
                DoorstopWarning('warning'),
                DoorstopInfo('info'),
            ]
        ),
    )
    def test_validate_document(self):
        """Verify a document error fails the tree validation."""
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

    def test_get_traceability(self):
        """Verify traceability rows are correct."""
        rows = [
            (self.tree.find_item('SYS001'), self.tree.find_item('REQ001')),
            (self.tree.find_item('SYS002'), self.tree.find_item('REQ001')),
            (None, self.tree.find_item('REQ002')),
            (None, self.tree.find_item('REQ004')),
        ]
        # Act
        rows2 = self.tree.get_traceability()
        # Assert
        self.maxDiff = None
        self.assertListEqual(rows, rows2)

    def test_new_document(self):
        """Verify a new document can be created on a tree."""
        self.tree.create_document(EMPTY, '_TEST', parent='REQ')

    def test_new_document_unknown_parent(self):
        """Verify an exception is raised for an unknown parent."""
        temp = tempfile.mkdtemp()
        self.assertRaises(
            DoorstopError, self.tree.create_document, temp, '_TEST', parent='UNKNOWN'
        )
        self.assertFalse(os.path.exists(temp))

    @patch('doorstop.core.document.Document.add_item')
    def test_add_item(self, mock_add_item):
        """Verify an item can be added to a document."""
        self.tree.add_item('REQ')
        mock_add_item.assert_called_once_with(number=None, level=None, reorder=True)

    @patch('doorstop.core.document.Document.add_item')
    def test_add_item_level(self, mock_add):
        """Verify an item can be added to a document with a level."""
        self.tree.add_item('REQ', level='1.2.3')
        mock_add.assert_called_once_with(number=None, level='1.2.3', reorder=True)

    def test_add_item_unknown_prefix(self):
        """Verify an exception is raised for an unknown prefix (item)."""
        # Cache miss
        self.assertRaises(DoorstopError, self.tree.add_item, 'UNKNOWN')
        # Cache hit
        self.assertRaises(DoorstopError, self.tree.add_item, 'UNKNOWN')

    @patch('doorstop.settings.REORDER', False)
    @patch('doorstop.core.item.Item.delete')
    def test_remove_item(self, mock_delete):
        """Verify an item can be removed from a document."""
        self.tree.remove_item('req1', reorder=False)
        mock_delete.assert_called_once_with()

    def test_remove_item_unknown_item(self):
        """Verify an exception is raised removing an unknown item."""
        self.assertRaises(DoorstopError, self.tree.remove_item, 'req9999')

    @patch('doorstop.core.item.Item.link')
    def test_link_items(self, mock_link):
        """Verify two items can be linked."""
        self.tree.link_items('req1', 'req2')
        mock_link.assert_called_once_with('REQ002')

    def test_link_items_self_reference(self):
        """Verify an exception is raised with a self reference."""
        try:
            self.tree.link_items('req1', 'req1')
            self.fail()
        except DoorstopError as error:
            self.assertEqual(str(error), "link would be self reference")

    def test_link_items_cyclic_dependency(self):
        """Verify an exception is raised with a cyclic dependency."""
        self.tree.link_items('req1', 'sys2')
        msg = "^link would create a cyclic dependency: " "SYS002 -> REQ001 -> SYS002$"
        self.assertRaisesRegex(DoorstopError, msg, self.tree.link_items, 'sys2', 'req1')

    def test_link_items_unknown_child_prefix(self):
        """Verify an exception is raised with an unknown child prefix."""
        self.assertRaises(DoorstopError, self.tree.link_items, 'unknown1', 'req2')

    def test_link_items_unknown_child_number(self):
        """Verify an exception is raised with an unknown child number."""
        self.assertRaises(DoorstopError, self.tree.link_items, 'req9999', 'req2')

    def test_link_items_unknown_parent_prefix(self):
        """Verify an exception is raised with an unknown parent prefix."""
        self.assertRaises(DoorstopError, self.tree.link_items, 'req1', 'unknown1')

    def test_link_items_unknown_parent_number(self):
        """Verify an exception is raised with an unknown parent prefix."""
        self.assertRaises(DoorstopError, self.tree.link_items, 'req1', 'req9999')

    @patch('doorstop.core.item.Item.unlink')
    def test_unlink_items(self, mock_unlink):
        """Verify two items can be unlinked."""
        self.tree.unlink_items('req3', 'req1')
        mock_unlink.assert_called_once_with('REQ001')

    def test_unlink_items_unknown_child_prefix(self):
        """Verify an exception is raised with an unknown child prefix."""
        self.assertRaises(DoorstopError, self.tree.unlink_items, 'unknown1', 'req1')

    def test_unlink_items_unknown_child_number(self):
        """Verify an exception is raised with an unknown child number."""
        self.assertRaises(DoorstopError, self.tree.unlink_items, 'req9999', 'req1')

    def test_unlink_items_unknown_parent_prefix(self):
        """Verify an exception is raised with an unknown parent prefix."""
        # Cache miss
        self.assertRaises(DoorstopError, self.tree.unlink_items, 'req3', 'unknown1')
        # Cache hit
        self.assertRaises(DoorstopError, self.tree.unlink_items, 'req3', 'unknown1')

    def test_unlink_items_unknown_parent_number(self):
        """Verify an exception is raised with an unknown parent prefix."""
        self.assertRaises(DoorstopError, self.tree.unlink_items, 'req3', 'req9999')

    @patch('doorstop.core.editor.launch')
    def test_edit_item(self, mock_launch):
        """Verify an item can be edited in a tree."""
        self.tree.edit_item('req2', launch=True)
        path = os.path.join(FILES, 'REQ002.yml')
        mock_launch.assert_called_once_with(path, tool=None)

    def test_edit_item_unknown_prefix(self):
        """Verify an exception is raised for an unknown prefix (document)."""
        self.assertRaises(DoorstopError, self.tree.edit_item, 'unknown1')

    def test_edit_item_unknown_number(self):
        """Verify an exception is raised for an unknown number."""
        self.assertRaises(DoorstopError, self.tree.edit_item, 'req9999')

    def test_find_item(self):
        """Verify an item can be found by exact UID."""
        # Cache miss
        item = self.tree.find_item('req2-001')
        self.assertIsNot(None, item)
        # Cache hit
        item2 = self.tree.find_item('req2-001')
        self.assertIs(item2, item)

    def test_find_document(self):
        """Verify an document can be found by prefix."""
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
