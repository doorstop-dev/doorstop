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

from doorstop.core.test import ENV, REASON, FILES


class MockItem(Item, Mock):
    pass


@patch('doorstop.core.item.Item', MockItem)
class TestDocument(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for the Document class."""  # pylint: disable=C0103,W0212

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
        self._out = "settings:\n  prefix: RQ\n  digits: 3"
        with patch.object(Document, '_read', self._mock_read):
            with patch.object(Document, '_write', self._mock_write):
                self.document = Document(FILES)

    def test_init(self):
        """Verify a document can be loaded from file."""
        self.assertEqual('RQ', self.document.prefix)


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestDocumentIntegration(unittest.TestCase):  # pylint: disable=R0904
    """Integration tests for the Document class."""  # pylint: disable=C0103


class TestModule(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for the doorstop.core.document module."""  # pylint: disable=C0103

    def test_tbd(self):
        """Verify TBD."""
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
