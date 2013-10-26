#!/usr/bin/env python

"""
Unit tests for the doorstop.core.processor module.
"""

import unittest

import os

from doorstop.core import processor
from doorstop.core.processor import Node

from doorstop.core.test import FILES


class TestNode(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for the Node class module."""  # pylint: disable=C0103

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

    def test_iter(self):
        """Verify a tree can be iterated over."""
        items = [d for d in self.tree]
        self.assertListEqual(['a', 'b1', 'b2', 'c1', 'c2'], items)

    def test_contains(self):
        """Verify a tree can be checked for contents."""
        child = self.tree.children[1].children[0]
        self.assertIn(child.document, self.tree)


class TestModule(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for the doorstop.core.processor module."""  # pylint: disable=C0103

    def test_run_empty(self):
        """Verify an empty directory is an invalid hiearchy."""
        path = os.path.join(FILES, 'empty')
        self.assertFalse(processor.run(path))


if __name__ == '__main__':
    unittest.main()
