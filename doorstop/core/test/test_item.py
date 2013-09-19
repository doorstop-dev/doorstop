#!/usr/bin/env python

"""
Unit tests for the doorstop.core.item module.
"""

import unittest
from unittest.mock import patch, Mock

import os

from doorstop.core.item import Item

FILES = os.path.join(os.path.dirname(__file__), 'files')


class TestItem(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for the Item class."""  # pylint: disable=C0103

    def setUp(self):
        self.item = Item('path')
        self.item._read = Mock(return_value="")
        self.item._write = Mock()

    def test_load(self):
        self.item.load()
        self.item._read.assert_called_once()

    def test_save(self):
        self.item.save()
        self.item._write.assert_called_once()

    def test_text(self):
        """Verify an item's text can be set and read."""
        self.item.text = "test text"
        self.assertEqual("test text", self.item.text)


class TestItemIntegration(unittest.TestCase):  # pylint: disable=R0904
    """Integration tests for the Item class."""  # pylint: disable=C0103

    def test_load(self):
        """Verify an item can be loaded from a file."""
        pass

    def test_save(self):
        """Verify an item can be saved to a file."""
        pass


class TestModule(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for the doorstop.core.item module."""  # pylint: disable=C0103

    def test_tbd(self):
        """Verify TBD."""
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
