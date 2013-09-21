#!/usr/bin/env python

"""
Unit tests for the doorstop.core.item module.
"""

import unittest
from unittest.mock import Mock

import os

from doorstop.core.item import Item

FILES = os.path.join(os.path.dirname(__file__), 'files')


class TestItem(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for the Item class."""  # pylint: disable=C0103,W0212

    def _mock_read(self):
        """Mock read function."""
        return self._out

    def _mock_write(self, out):
        """Mock write function"""
        self._out = out

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


class TestItemIntegration(unittest.TestCase):  # pylint: disable=R0904
    """Integration tests for the Item class."""  # pylint: disable=C0103

    def test_save_load(self):
        """Verify an item can be saved and loaded from a file."""
        item = Item(os.path.join(FILES, 'REQ001.yml'))
        item.text = "Hello, world!"
        item.links = ['SYS001', 'SYS002']
        item2 = Item(os.path.join(FILES, 'REQ001.yml'))
        self.assertEqual("Hello, world!", item2.text)
        self.assertEqual(['SYS001', 'SYS002'], item2.links)


class TestModule(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for the doorstop.core.item module."""  # pylint: disable=C0103

    def test_tbd(self):
        """Verify TBD."""
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
