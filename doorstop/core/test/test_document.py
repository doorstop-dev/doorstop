#!/usr/bin/env python

"""
Unit tests for the doorstop.core.document module.
"""

import unittest
from unittest.mock import patch, Mock

import os
import logging

from doorstop.core.item import Item
from doorstop.core.document import Document
from doorstop.common import DoorstopError

from doorstop.core.test import ROOT, FILES, EMPTY, NEW


class MockItem(Item, Mock):  # pylint: disable=R0904
    """Mock Item class for Document unit tests."""
    pass


class MockDocument(Document):
    """Document class with mock read/write methods after initialization."""

    @patch('os.path.isfile', Mock(return_value=True))
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._file = ""  # file system mock
        self._read = Mock(side_effect=self._mock_read)
        self._write = Mock(side_effect=self._mock_write)

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


@patch('doorstop.core.item.Item', MockItem)  # pylint: disable=R0904
class TestDocument(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for the Document class."""  # pylint: disable=C0103,W0212

    def setUp(self):
        self.document = MockDocument(FILES, root=ROOT)

    def test_load(self):
        """Verify the document config can be loaded from file."""
        self.document._file = "settings:\n  prefix: SYS\n  digits: 4"
        self.document.load()
        self.assertEqual('SYS', self.document.prefix)
        self.assertEqual(4, self.document.digits)

    def test_load_parent(self):
        """Verify the document config can be loaded from file with a parent."""
        self.document._file = "settings:\n  prefix: DC\n  parent: SYS"
        self.document.load()
        self.assertEqual('SYS', self.document.parent)

    def test_save(self):
        """Verify a document config can be saved."""
        self.document.prefix = 'SRD'
        self.document.digits = 5
        self.document.save()
        text = "settings:\n  digits: 5\n  parent: SYS\n  prefix: SRD\n"
        self.assertEqual(text, self.document._file)

    def test_save_parent(self):
        """Verify a document can be saved with a parent."""
        self.document.parent = 'SYS'
        self.document.save()
        self.assertIn("parent: SYS", self.document._file)

    def test_str(self):
        """Verify documents can be converted to strings."""
        path = os.path.join('doorstop', 'core', 'test', 'files')
        text = "REQ (@{}{})".format(os.sep, path)
        self.assertEqual(text, str(self.document))

    def test_ne(self):
        """Verify document non-equality is correct."""
        self.assertNotEqual(self.document, None)

    def test_items(self):
        """Verify the items in a document can be accessed."""
        items = self.document.items
        logging.debug("items: {}".format(items))
        self.assertEqual(3, len(items))

    @patch('doorstop.core.document.Document', MockDocument)
    def test_new(self):
        """Verify a new document can be created with defaults."""
        path = os.path.join(EMPTY, '.doorstop.yml')
        try:
            doc = MockDocument.new(EMPTY, root=FILES, prefix='NEW', digits=2)
        finally:
            os.remove(path)
        self.assertEqual('NEW', doc.prefix)
        self.assertEqual(2, doc.digits)
        MockDocument._new.assert_called_once_with(EMPTY, path)

    def test_new_existing(self):
        """Verify an exception is raised if the document already exists."""
        self.assertRaises(DoorstopError, Document.new, FILES, FILES, '_TEST')

    def test_invalid(self):
        """Verify an exception is raised on an invalid document."""
        self.assertRaises(DoorstopError, Document, EMPTY)

    @patch('doorstop.core.item.Item.new')
    def test_add(self, mock_new):
        """Verify an item can be added to a document."""
        self.document.add()
        mock_new.assert_called_once_with(FILES, ROOT, 'REQ', 2, 4, (2, 2))

    @patch('doorstop.core.item.Item.new')
    def test_add_empty(self, mock_new):
        """Verify an item can be added to an new document."""
        document = MockDocument(NEW, ROOT)
        self.assertIsNot(None, document.add())
        mock_new.assert_called_once_with(NEW, ROOT, 'NEW', 5, 1, None)

    def test_check(self):
        """Verify a document can be validated."""
        self.document.check()


class TestModule(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for the doorstop.core.document module."""  # pylint: disable=C0103

    def test_tbd(self):
        """Verify TBD."""
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
