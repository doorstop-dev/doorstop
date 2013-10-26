"""
Integration tests for the doorstop.core package.
"""

import unittest

import os

from scripttest import TestFileEnvironment

from doorstop.core import Item
from doorstop.core import Document

ROOT = os.path.join(os.path.dirname(__file__), '..', '..', '..')

FILES = os.path.join(os.path.dirname(__file__), 'files')

ENV = 'TEST_INTEGRATION'  # environment variable to enable integration tests
REASON = "'{0}' variable not set".format(ENV)


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
        self.assertEqual(os.path.join(FILES, 'external', 'text.txt'), path)
        self.assertEqual(3, line)


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestDocument(unittest.TestCase):  # pylint: disable=R0904
    """Integration tests for the Document class."""  # pylint: disable=C0103

    EMPTY = os.path.join(FILES, 'empty')

    def tearDown(self):
        """Clean up temporary files."""
        for filename in os.listdir(TestDocument.EMPTY):
            path = os.path.join(TestDocument.EMPTY, filename)
            os.remove(path)

    def test_load(self):
        """Verify a document can be loaded from a directory."""
        doc = Document(FILES)
        self.assertEqual('RQ', doc.prefix)
        self.assertEqual(2, doc.digits)
        self.assertEqual(3, len(doc.items))

    def test_new(self):
        """Verify a new document can be created."""
        doc = Document(TestDocument.EMPTY, prefix='SYS', digits=4)
        self.assertEqual('SYS', doc.prefix)
        self.assertEqual(4, doc.digits)
        self.assertEqual(0, len(doc.items))


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestAPI(unittest.TestCase):  # pylint: disable=R0904
    """Integration tests for the Doorstop API."""

    pass
