#!/usr/bin/env python

"""
Unit tests for the doorstop.core.item module.
"""

import unittest
from unittest.mock import Mock

import logging

from doorstop.common import DoorstopError
from doorstop.core.item import Item


class MockItem(Item):
    """Item class with mock read/write methods."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._file = ""  # file system mock
        self._read = Mock(side_effect=self._mock_read)
        self._write = Mock(side_effect=self._mock_write)

    def _mock_read(self):
        """Mock read method."""
        text = self._file
        logging.debug("mock read: {0}".format(repr(text)))
        return text

    def _mock_write(self, text):
        """Mock write method"""
        logging.debug("mock write: {0}".format(repr(text)))
        self._file = text


class TestItem(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for the Item class."""  # pylint: disable=C0103,W0212

    def setUp(self):
        self.item = MockItem('path/to/RQ001.yml')
        self.item._file = "links: []\ntext: ''\nlevel: 1.1.1"

    def test_load_empty(self):
        """Verify loading calls read."""
        self.item.load()
        self.item._read.assert_called_once_with()
        self.assertEqual('', self.item._text)
        self.assertEqual(set(), self.item._links)
        self.assertEqual((1, 1, 1), self.item._level)
        self.item.check()

    def test_load_error(self):
        """Verify an exception is raised with invalid YAML."""
        self.item._file = "markdown: **Document and Item Creation**"
        self.assertRaises(DoorstopError, self.item.load)

    def test_save_empty(self):
        """Verify saving calls write."""
        self.item.save()
        text = "level: 1\nlinks: []\ntext: ''\n"
        self.item._write.assert_called_once_with(text)

    def test_repr(self):
        """Verify an item can be represented."""
        self.assertEqual(self.item, eval(repr(self.item)))

    def test_str(self):
        """Verify an item can be printed."""
        self.assertEqual("RQ001 (@/path/to/RQ001.yml)", str(self.item))

    def test_ne(self):
        """Verify item non-equality is correct."""
        self.assertNotEqual(self.item, None)

    def test_lt(self):
        """Verify items can be compared."""
        item0 = MockItem('path/to/RQ002.yml', level=(1, 1))
        item1 = self.item
        item2 = MockItem('path/to/RQ003.yml', level=(1, 1, 2))
        self.assertLess(item0, item1)
        self.assertLess(item1, item2)
        self.assertGreater(item2, item0)

    def test_id(self):
        """Verify an item's ID can be read but not set."""
        self.assertEqual('RQ001', self.item.id)
        self.assertRaises(AttributeError, setattr, self.item, 'id', 'RQ002')

    def test_prefix(self):
        """Verify an item's prefix can be read but not set."""
        self.assertEqual('RQ', self.item.prefix)
        self.assertRaises(AttributeError, setattr, self.item, 'prefix', 'REQ')

    def test_number(self):
        """Verify an item's number can be read but not set."""
        self.assertEqual(1, self.item.number)
        self.assertRaises(AttributeError, setattr, self.item, 'number', 2)

    def test_level(self):
        """Verify an item's level can be set and read."""
        self.item.level = (1, 2, 3)
        self.assertEqual((1, 2, 3), self.item.level)
        text = "level: 1.2.3\nlinks: []\ntext: ''\n"
        self.item._write.assert_called_once_with(text)

    def test_level_from_text(self):
        """Verify an item's level can be set from text and read."""
        self.item.level = "4.2"
        self.assertEqual((4, 2), self.item.level)
        text = "level: 4.2\nlinks: []\ntext: ''\n"
        self.item._write.assert_called_once_with(text)

    def test_level_from_float(self):
        """Verify an item's level can be set from a float and read."""
        self.item.level = 4.2
        self.assertEqual((4, 2), self.item.level)
        text = "level: 4.2\nlinks: []\ntext: ''\n"
        self.item._write.assert_called_once_with(text)

    def test_level_from_int(self):
        """Verify an item's level can be set from a int and read."""
        self.item.level = 42
        self.assertEqual((42,), self.item.level)
        text = "level: 42\nlinks: []\ntext: ''\n"
        self.item._write.assert_called_once_with(text)

    def test_text(self):
        """Verify an item's text can be set and read."""
        self.item.text = "test text"
        self.assertEqual("test text", self.item.text)

    def test_ref(self):
        """Verify an item's reference can be set and read."""
        self.item.ref = "abc123"
        self.assertEqual("abc123", self.item.ref)
        text = "level: 1\nlinks: []\nref: abc123\ntext: ''\n"
        self.item._write.assert_called_once_with(text)

    def test_ref_none(self):
        """Verify item refs are only saved if they exist."""
        self.item.ref = None
        self.assertEqual(None, self.item.ref)
        text = "level: 1\nlinks: []\ntext: ''\n"
        self.item._write.assert_called_once_with(text)

    def test_find_ref_error(self):
        """Verify an error is raised when no external reference is found."""
        self.item.ref = "notfound"
        self.assertRaises(ValueError, self.item.find_ref)

    def test_find_ref_none(self):
        """Verify nothing returned when no external reference is specified."""
        self.assertEqual((None, None), self.item.find_ref())

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

    def test_invalid_file_name(self):
        """Verify an invalid file name cannot be a requirement."""
        self.assertRaises(ValueError, MockItem, "path/to/REQ.yaml")
        self.assertRaises(ValueError, MockItem, "path/to/001.yaml")

    def test_invalid_file_ext(self):
        """Verify an invalid file extension cannot be a requirement."""
        self.assertRaises(ValueError, MockItem, "path/to/REQ001")
        self.assertRaises(ValueError, MockItem, "path/to/REQ001.txt")


class TestModule(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for the doorstop.core.item module."""  # pylint: disable=C0103

    def test_tbd(self):
        """Verify TBD."""
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
