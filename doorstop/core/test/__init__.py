"""
Integration tests for the doorstop.core package.
"""

import unittest

import os

from scripttest import TestFileEnvironment

from doorstop.core import Item
from doorstop.core import Document

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

FILES = os.path.join(os.path.dirname(__file__), 'files')

ENV = 'TEST_INTEGRATION'  # environment variable to enable integration tests
REASON = "'{0}' variable not set".format(ENV)


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestItem(unittest.TestCase):  # pylint: disable=R0904
    """Integration tests for the Item class."""  # pylint: disable=C0103

    def test_save_load(self):
        """Verify an item can be saved and loaded from a file."""
        item = Item(os.path.join(FILES, 'REQ001.yml'))
        item.text = "Hello, world!"
        item.links = ['SYS001', 'SYS002']
        item2 = Item(os.path.join(FILES, 'REQ001.yml'))
        self.assertEqual("Hello, world!", item2.text)
        self.assertEqual(['SYS001', 'SYS002'], item2.links)


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestDocument(unittest.TestCase):  # pylint: disable=R0904
    """Integration tests for the Document class."""  # pylint: disable=C0103


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestAPI(unittest.TestCase):  # pylint: disable=R0904
    """Integration tests for the Doorstop API."""

    pass
