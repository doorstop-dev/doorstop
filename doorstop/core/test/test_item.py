#!/usr/bin/env python

"""
Unit tests for the doorstop.core.item module.
"""

import unittest
from unittest.mock import patch, Mock

import os
import logging

from doorstop.common import DoorstopError
from doorstop.core.item import Item

from doorstop.core.test import ENV, REASON, FILES, EMPTY, EXTERNAL


class MockItem(Item):
    """Item class with mock read/write methods."""

    @patch('os.path.isfile', Mock(return_value=True))
    def __init__(self, *args, **kwargs):
        self._file = kwargs.pop('_file', "")  # file system mock
        super().__init__(*args, **kwargs)
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

    _new = Mock()


class TestItem(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for the Item class."""  # pylint: disable=C0103,W0212

    def setUp(self):
        self.path = os.path.join('path', 'to', 'RQ001.yml')
        self.item = MockItem(self.path, _file=("links: []\n"
                                               "ref: ''\n"
                                               "text: ''\n"
                                               "level: 1.1.1"))

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
        text = ("level: 1" + '\n'
                "links: []" + '\n'
                "normative: true" + '\n'
                "ref: ''" + '\n'
                "text: ''" + '\n')
        self.item._write.assert_called_once_with(text)

    def test_str(self):
        """Verify an item can be printed."""
        text = "RQ001 (@{}{})".format(os.sep, self.path)
        self.assertEqual(text, str(self.item))

    def test_ne(self):
        """Verify item non-equality is correct."""
        self.assertNotEqual(self.item, None)

    def test_lt(self):
        """Verify items can be compared."""
        item0 = MockItem('path/to/RQ002.yml')
        item0.level = (1, 1)
        item1 = self.item
        item2 = MockItem('path/to/RQ003.yml')
        item2.level = (1, 1, 2)
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
        self.assertIn("level: 1.2.3\n", self.item._write.call_args[0][0])
        self.assertEqual((1, 2, 3), self.item.level)

    def test_heading(self):
        """Verify the heading can be read from the item's level."""
        self.item.level = (1,)
        self.assertEqual(1, self.item.heading)
        self.item.level = (1, 0)
        self.assertEqual(1, self.item.heading)
        self.item.level = (2, 0, 1)
        self.assertEqual(3, self.item.heading)
        self.item.level = (2, 0, 1, 1, 0, 0)
        self.assertEqual(4, self.item.heading)

    def test_level_from_text(self):
        """Verify an item's level can be set from text and read."""
        self.item.level = "4.2.0 "
        self.assertIn("level: 4.2.0\n", self.item._write.call_args[0][0])
        self.assertEqual((4, 2, 0), self.item.level)

    def test_level_from_float(self):
        """Verify an item's level can be set from a float and read."""
        self.item.level = 4.2
        self.assertIn("level: 4.2\n", self.item._write.call_args[0][0])
        self.assertEqual((4, 2), self.item.level)

    def test_level_from_int(self):
        """Verify an item's level can be set from a int and read."""
        self.item.level = 42
        self.assertIn("level: 42\n", self.item._write.call_args[0][0])
        self.assertEqual((42,), self.item.level)

    def test_text(self):
        """Verify an item's text can be set and read."""
        self.item.text = "abc "
        self.assertIn("text: |\n  abc\n", self.item._write.call_args[0][0])
        self.assertEqual("abc", self.item.text)

    def test_text_sentences(self):
        """Verify newlines separate sentences in an item's text."""
        self.item.text = ("A sentence. Another sentence! Hello? Hi.\n"
                          "A new line. And another sentence.")
        expected = ("A sentence.\n"
                    "Another sentence!\n"
                    "Hello?\n"
                    "Hi.\n"
                    "A new line.\n"
                    "And another sentence.")
        self.assertEqual(expected, self.item.text)

    def test_ref(self):
        """Verify an item's reference can be set and read."""
        self.item.ref = "abc123"
        self.assertIn("ref: abc123\n", self.item._write.call_args[0][0])
        self.assertEqual("abc123", self.item.ref)

    def test_find_ref(self):
        """Verify an item's reference can be found."""
        self.item.ref = "REF" + "123"  # to avoid matching in this file
        relpath, line = self.item.find_ref(EXTERNAL)
        self.assertEqual('text.txt', os.path.basename(relpath))
        self.assertEqual(3, line)

    def test_find_ref_filename(self):
        """Verify an item's reference can also be a filename."""
        self.item.ref = "text.txt"
        relpath, line = self.item.find_ref(FILES)
        self.assertEqual('text.txt', os.path.basename(relpath))
        self.assertEqual(None, line)

    def test_find_ref_error(self):
        """Verify an error occurs when no external reference found."""
        self.item.ref = "not found".replace(' ', '')  # avoids self match
        self.assertRaises(DoorstopError, self.item.find_ref, root=EMPTY)

    @unittest.skipUnless(os.getenv(ENV), REASON)
    def test_find_ref_error_long(self):
        """Verify an error occurs when no external reference found (long)."""
        self.item.ref = "not found".replace(' ', '')  # avoids self match
        self.assertRaises(DoorstopError, self.item.find_ref)

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

    def test_normative(self):
        """Verify an item's normative status can be set and read."""
        self.item.normative = 0  # converted to False
        self.assertIn("normative: false\n", self.item._write.call_args[0][0])
        self.assertFalse(self.item.normative)

    def test_extended(self):
        """Verify an extended attribute can be used."""
        self.item.set('ext1', 'foobar')
        self.assertEqual('foobar', self.item.get('ext1'))

    def test_invalid_file_name(self):
        """Verify an invalid file name cannot be a requirement."""
        self.assertRaises(DoorstopError, MockItem, "path/to/REQ.yaml")
        self.assertRaises(DoorstopError, MockItem, "path/to/001.yaml")

    def test_invalid_file_ext(self):
        """Verify an invalid file extension cannot be a requirement."""
        self.assertRaises(DoorstopError, MockItem, "path/to/REQ001")
        self.assertRaises(DoorstopError, MockItem, "path/to/REQ001.txt")

    @patch('doorstop.core.item.Item', MockItem)
    def test_new(self):
        """Verify items can be created."""
        MockItem._new.reset_mock()
        item = MockItem.new(EMPTY, FILES, 'TEST', 5, 42, (1, 2, 3))
        path = os.path.join(EMPTY, 'TEST00042.yml')
        self.assertEqual(path, item.path)
        self.assertEqual((1, 2, 3), item.level)
        MockItem._new.assert_called_once_with(path)

    @patch('doorstop.core.item.Item', MockItem)
    def test_new_special(self):
        """Verify items can be created with a specially named prefix."""
        MockItem._new.reset_mock()
        item = MockItem.new(EMPTY, FILES, 'VSM.HLR_01-002-', 3, 42, (1,))
        path = os.path.join(EMPTY, 'VSM.HLR_01-002-042.yml')
        self.assertEqual(path, item.path)
        self.assertEqual((1,), item.level)
        MockItem._new.assert_called_once_with(path)

    def test_new_existing(self):
        """Verify an exception is raised if the item already exists."""
        self.assertRaises(DoorstopError,
                          Item.new, FILES, FILES, 'REQ', 3, 2, (1, 2, 3))

    def test_check_document(self):
        """Verify an item can be checked against a document."""
        document = Mock()
        document.parent = 'fake'
        self.item.check(document=document)

    def test_check_document_with_links(self):
        """Verify an item can be checked against a document with links."""
        self.item.add_link('unknown1')
        document = Mock()
        document.parent = 'fake'
        self.item.check(document=document)

    def test_check_tree(self):
        """Verify an item can be checked against a tree."""
        self.item.add_link('fake1')
        tree = Mock(find_item=Mock())

        def mock_iter(self):  # pylint: disable=W0613
            """Mock Tree.__iter__ to yield a mock Document."""
            mock_document = Mock()
            mock_document.parent = 'RQ'

            def mock_iter2(self):  # pylint: disable=W0613
                """Mock Document.__iter__ to yield a mock Item."""
                mock_item = Mock()
                mock_item.id = 'TST001'
                mock_item.links = ['RQ001']
                yield mock_item

            mock_document.__iter__ = mock_iter2
            yield mock_document
        tree.__iter__ = mock_iter
        self.item.check(tree=tree)

    def test_check_tree_non_normative(self):
        """Verify a non-normative item can be checked against a tree."""
        self.item.normative = False
        self.item.add_link('fake1')
        tree = Mock(find_item=Mock())

        def mock_iter(self):  # pylint: disable=W0613
            """Mock Tree.__iter__ to yield a mock Document."""
            mock_document = Mock()
            mock_document.parent = 'RQ'

            def mock_iter2(self):  # pylint: disable=W0613
                """Mock Document.__iter__ to yield a mock Item."""
                mock_item = Mock()
                mock_item.id = 'TST001'
                mock_item.links = ['RQ001']
                yield mock_item

            mock_document.__iter__ = mock_iter2
            yield mock_document
        tree.__iter__ = mock_iter
        self.item.check(tree=tree)

    def test_check_tree_no_down_links(self):
        """Verify an item can be checked against a tree without down links."""
        self.item.add_link('fake1')
        tree = Mock(find_item=Mock())

        def mock_iter(self):  # pylint: disable=W0613
            """Mock Tree.__iter__ to yield a mock Document."""
            mock_document = Mock()
            mock_document.parent = 'RQ'

            def mock_iter2(self):  # pylint: disable=W0613
                """Mock Document.__iter__ to yield a mock Item."""
                mock_item = Mock()
                mock_item.links = []
                yield mock_item

            mock_document.__iter__ = mock_iter2
            yield mock_document
        tree.__iter__ = mock_iter
        self.item.check(tree=tree)

    def test_check_tree_error(self):
        """Verify an item can be checked against a tree with errors."""
        self.item.add_link('fake1')
        tree = Mock(find_item=Mock(side_effect=DoorstopError))
        self.assertRaises(DoorstopError, self.item.check, tree=tree)

    @patch('os.remove')
    def test_delete(self, mock_remove):
        """Verify an item can be deleted."""
        self.item.delete()
        mock_remove.assert_called_once_with(self.item.path)


class TestFormatting(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for text formatting in Items."""  # pylint: disable=C0103

    ITEM = os.path.join(FILES, 'REQ001.yml')

    def setUp(self):
        with open(self.ITEM, 'rb') as infile:
            self.backup = infile.read()

    def tearDown(self):
        with open(self.ITEM, 'wb') as outfile:
            outfile.write(self.backup)

    def test_load_save(self):
        """Verify text formatting is preserved."""
        item = Item(self.ITEM)
        item.load()
        item.save()
        with open(self.ITEM, 'rb') as infile:
            text = infile.read()
        self.assertEqual(self.backup, text)


class TestModule(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for the doorstop.core.item module."""  # pylint: disable=C0103

    def test_tbd(self):
        """Verify TBD."""
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
