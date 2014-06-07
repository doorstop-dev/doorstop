"""Unit tests for the doorstop.core.builder module."""

import unittest
from unittest.mock import patch, Mock

from doorstop.core.tree import Tree
from doorstop.core.builder import build, find_document, find_item, _clear_tree

from doorstop.core.test import FILES, EMPTY
from doorstop.core.test import MockDocumentSkip, MockDocumentNoSkip


class TestModule(unittest.TestCase):  # pylint: disable=R0904

    """Unit tests for the doorstop.core.builder module."""  # pylint: disable=C0103

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
        identifier = 'req1'
        find_item(identifier)
        mock_find_item.assert_called_once_with(identifier)
