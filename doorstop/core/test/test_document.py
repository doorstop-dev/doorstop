#!/usr/bin/env python

"""
Unit tests for the doorstop.core.document module.
"""

import unittest
from unittest.mock import patch, Mock

import logging

from doorstop.core.item import Item
from doorstop.core.document import Document

from doorstop.core.test import FILES


class MockItem(Item, Mock):
    """Mock Item class for Document unit tests."""
    pass


@patch('doorstop.core.item.Item', MockItem)  # pylint: disable=R0904
class TestDocument(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for the Document class."""  # pylint: disable=C0103,W0212

    _out = ""

    def _mock_read(self):
        """Mock read function."""
        text = self._out
        logging.debug("mock read: {0}".format(repr(text)))
        return text

    def _mock_write(self, text):
        """Mock write function"""
        logging.debug("mock write: {0}".format(repr(text)))
        self._out = text

    def setUp(self):
        with patch.object(Document, '_read', self._mock_read):
            with patch.object(Document, '_write', self._mock_write):
                self.document = Document(FILES, 'RQ', 3)

    def test_init(self):
        """Verify document attributes are created."""
        self.assertEqual('RQ', self.document.prefix)
        self.assertEqual(3, self.document.digits)

    def test_load(self):
        """Verify the document config can be loaded from file."""
        text = "settings:\n  prefix: SYS\n  digits: 4"
        with patch.object(self.document, '_read', Mock(return_value=text)):
            self.document.load()
        self.assertEqual('SYS', self.document.prefix)
        self.assertEqual(4, self.document.digits)

    def test_items(self):
        """Verify the items in a document can be accessed."""
        self.assertRaises(NotImplementedError, getattr, self.document, 'items')


class TestModule(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for the doorstop.core.document module."""  # pylint: disable=C0103

    def test_tbd(self):
        """Verify TBD."""
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
