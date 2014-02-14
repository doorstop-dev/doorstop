"""
Integration tests for the doorstop.core package.
"""

import unittest
from unittest.mock import patch

import os

from doorstop.core import Item
from doorstop.core import Document
from doorstop.core import Tree, build

from doorstop.core.test import ENV, REASON, ROOT, FILES, EMPTY


class DocumentNoSkip(Document):
    """Document class that is never skipped."""

    SKIP = '__disabled__'  # never skip test Documents


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestItem(unittest.TestCase):  # pylint: disable=R0904
    """Integration tests for the Item class."""  # pylint: disable=C0103

    def test_save_load(self):
        """Verify an item can be saved and loaded from a file."""
        item = Item(os.path.join(FILES, 'REQ001.yml'))
        item.level = '1.2.3'
        item.text = "Hello, world!"
        item.links = ['SYS001', 'SYS002']
        item2 = Item(os.path.join(FILES, 'REQ001.yml'))
        self.assertEqual((1, 2, 3), item2.level)
        self.assertEqual("Hello, world!", item2.text)
        self.assertEqual(['SYS001', 'SYS002'], item2.links)

    def test_find_ref(self):
        """Verify an item's external reference can be found."""
        item = Item(os.path.join(FILES, 'REQ003.yml'))
        path, line = item.find_ref()
        relpath = os.path.relpath(os.path.join(FILES, 'external', 'text.txt'),
                                  ROOT)
        self.assertEqual(relpath, path)
        self.assertEqual(3, line)


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestDocument(unittest.TestCase):  # pylint: disable=R0904
    """Integration tests for the Document class."""  # pylint: disable=C0103

    def tearDown(self):
        """Clean up temporary files."""
        for filename in os.listdir(EMPTY):
            path = os.path.join(EMPTY, filename)
            os.remove(path)

    def test_load(self):
        """Verify a document can be loaded from a directory."""
        doc = Document(FILES)
        self.assertEqual('REQ', doc.prefix)
        self.assertEqual(2, doc.digits)
        self.assertEqual(5, len(doc.items))

    def test_new(self):
        """Verify a new document can be created."""
        doc = Document.new(EMPTY, FILES, prefix='SYS', digits=4)
        self.assertEqual('SYS', doc.prefix)
        self.assertEqual(4, doc.digits)
        self.assertEqual(0, len(doc.items))


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestTree(unittest.TestCase):  # pylint: disable=R0904
    """Integration tests for the Tree class."""

    ITEM = os.path.join(FILES, 'REQ001.yml')

    def setUp(self):
        with open(self.ITEM, 'rb') as item:
            self.backup = item.read()

    def tearDown(self):
        with open(self.ITEM, 'wb') as item:
            item.write(self.backup)

    @patch('doorstop.core.document.Document', DocumentNoSkip)
    def test_valid_invalid_link(self):
        """Verify a tree is invalid with a bad link."""
        item = Item(self.ITEM)
        item.add_link('SYS003')
        tree = build(FILES, root=FILES)
        self.assertIsInstance(tree, Tree)
        self.assertFalse(tree.valid())
