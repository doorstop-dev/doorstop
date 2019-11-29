# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.core.builder module."""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from doorstop.core.builder import _clear_tree, build, find_document, find_item
from doorstop.core.item import Item
from doorstop.core.tests import EMPTY, FILES, MockDocumentNoSkip, MockDocumentSkip
from doorstop.core.tree import Tree


class TestModule(unittest.TestCase):
    """Unit tests for the doorstop.core.builder module."""

    @patch('doorstop.core.vcs.find_root', Mock(return_value=EMPTY))
    def test_run_empty(self):
        """Verify an empty directory is an empty hierarchy."""
        tree = build(EMPTY)
        self.assertEqual(0, len(tree))

    @patch('doorstop.core.document.Document', MockDocumentNoSkip)
    @patch('doorstop.core.vcs.find_root', Mock(return_value=FILES))
    def test_build(self):
        """Verify a tree can be built."""
        tree = build(FILES)
        self.assertEqual(4, len(tree))

    @patch('doorstop.core.document.Document', MockDocumentSkip)
    @patch('doorstop.core.vcs.find_root', Mock(return_value=FILES))
    def test_build_with_skips(self):
        """Verify documents can be skipped while building a tree."""
        tree = build(FILES)
        self.assertEqual(0, len(tree))

    @patch('doorstop.core.builder.build', Mock(return_value=Tree(Mock())))
    @patch('doorstop.core.tree.Tree.find_document')
    def test_find_document(self, mock_find_document):  # pylint: disable=R0201
        """Verify documents can be found using a convenience function."""
        _clear_tree()
        prefix = 'req'
        find_document(prefix)
        mock_find_document.assert_called_once_with(prefix)

    @patch('doorstop.core.builder.build', Mock(return_value=Tree(Mock())))
    @patch('doorstop.core.tree.Tree.find_item')
    def test_find_item(self, mock_find_item):  # pylint: disable=R0201
        """Verify items can be found using a convenience function."""
        _clear_tree()
        uid = 'req1'
        find_item(uid)
        mock_find_item.assert_called_once_with(uid)

    def test_tree_finds_documents(self):
        """Verify items can be found using a convenience function."""

        temp = tempfile.mkdtemp()
        cwd = temp
        root = temp

        # Step 1: Create a new tree with one item.
        tree = build(cwd, root)
        document = tree.create_document(cwd, 'TST')
        item = Item.new(tree, document, cwd, cwd, "TST-001")
        item.save()

        # Step 2: Find a newly created tree
        same_tree_again = build(cwd, root)

        # Verify that that the tree, document and its item can be found.
        self.assertEqual(1, len(same_tree_again.documents))
        document = same_tree_again.document
        self.assertIsNotNone(document)
        self.assertEqual(1, len(document.items))
        item = document.items[0]
        self.assertEqual('TST-001', item.uid)

    def test_tree_does_not_find_documents_when_skipall_file_present(self):
        """Verify items can be found using a convenience function."""

        temp = tempfile.mkdtemp()
        cwd = temp
        root = temp

        # Step 1: Create a new tree with one item.
        tree = build(cwd, root)
        document = tree.create_document(cwd, 'TST')
        item = Item.new(tree, document, cwd, cwd, "TST-001")
        item.save()

        # Step 2: Put a .doorstop.skip-all to the root of the tree.
        path = os.path.join(temp, '.doorstop.skip-all')
        open(path, 'a').close()

        # Step 3: Find a newly created tree
        same_tree_again = build(cwd, root)

        # Verify that the tree does not have a document because it was ignored.
        document = same_tree_again.document
        self.assertIsNone(document)

    def test_tree_finds_subdocuments(self):
        """Verify items can be found using a convenience function."""

        temp = tempfile.mkdtemp()
        cwd = temp
        root = temp

        # Step 1: Create a new tree with one item in a document in a subfolder.
        tree = build(cwd, root)
        document = tree.create_document(cwd, 'TST')

        subfolder = os.path.join(temp, 'SUBFOLDER')
        os.makedirs(os.path.join(temp, subfolder))

        sub_document = tree.create_document(subfolder, 'TST_SUB', parent='TST')

        item = Item.new(tree, sub_document, subfolder, cwd, "TST_SUB-001")
        item.save()

        # Step 2: Read existing tree
        same_tree_again = build(cwd, root)

        # Verify that the tree has:
        # - both root-level and subfolder documents
        # - item in a subdocument
        self.assertEqual(2, len(same_tree_again.documents))
        sub_document = same_tree_again.documents[1]
        self.assertIsNotNone(document)
        self.assertEqual(1, len(sub_document.items))
        item = sub_document.items[0]
        self.assertEqual('TST_SUB-001', item.uid)

    def test_tree_skips_subdocuments_when_skipall_file_present(self):
        """Verify items can be found using a convenience function."""

        temp = tempfile.mkdtemp()
        cwd = temp
        root = temp

        # Step 1: Create a new tree with one item in a document in a subfolder.
        tree = build(cwd, root)
        tree.create_document(cwd, 'TST')

        subfolder = os.path.join(temp, 'SUBFOLDER')
        os.makedirs(os.path.join(temp, subfolder))

        sub_document = tree.create_document(subfolder, 'TST_SUB', parent='TST')

        item = Item.new(tree, sub_document, subfolder, cwd, "TST_SUB-001")
        item.save()

        # Step 2: Put a .doorstop.skip-all into the subfolder.
        path = os.path.join(subfolder, '.doorstop.skip-all')
        open(path, 'a').close()

        # Verify that building tree ignores subfolder's document.
        same_tree_again = build(cwd, root)
        self.assertEqual(1, len(same_tree_again.documents))
