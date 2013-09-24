#!/usr/bin/env python

"""
Unit tests for the doorstop.core.item module.
"""

import unittest
from unittest.mock import Mock

import os
import logging

from doorstop.core.item import Item

from doorstop.core.test import ENV, REASON, FILES


class TestItem(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for the Item class."""  # pylint: disable=C0103,W0212

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
        self.item = Item('path')
        self._out = "links: []\ntext: ''\n"
        self.item._read = Mock(side_effect=self._mock_read)
        self.item._write = Mock(side_effect=self._mock_write)

    def test_load_empty(self):
        """Verify loading calls read."""
        self.item.load()
        self.item._read.assert_called_once_with()
        self.assertEqual('', self.item._text)
        self.assertEqual(set(), self.item._links)

    def test_save_empty(self):
        """Verify saving calls write."""
        self.item.save()
        text = "links: []\ntext: ''\n"
        self.item._write.assert_called_once_with(text)

    def test_text(self):
        """Verify an item's text can be set and read."""
        self.item.text = "test text"
        self.assertEqual("test text", self.item.text)

    def test_link_add(self):
        """Verify links can be added to an item."""
        self.item.add_link('abc')
        self.item.add_link('123')
        self.assertEqual(['123', 'abc'], self.item.links)

    def test_link_add_duplicate(self):
        """Verify duplicate links are ignored."""
        self.item.add_link('abc')
        self.item.add_link('abc')
        self.assertEqual(['abc'], self.item.links)

    def test_link_remove_duplicate(self):
        """Verify removing a link twice is not an error."""
        self.item.links = ['123', 'abc']
        self.item.remove_link('abc')
        self.item.remove_link('abc')
        self.assertEqual(['123'], self.item.links)


class TestModule(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for the doorstop.core.item module."""  # pylint: disable=C0103

    def test_tbd(self):
        """Verify TBD."""
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
