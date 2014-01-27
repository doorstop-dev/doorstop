#!/usr/bin/env python

"""
Unit tests for the doorstop.core.item module.
"""

import unittest
from unittest.mock import patch, Mock, MagicMock

import os
import logging

from doorstop import common
from doorstop.common import DoorstopError
from doorstop.core.item import Item

from doorstop.core.test import ENV, REASON, FILES, EMPTY, EXTERNAL


class MockItem(Item):  # pylint: disable=R0902,R0904
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
        self.assertEqual('', self.item._data['text'])
        self.assertEqual(set(), self.item._data['links'])
        self.assertEqual((1, 1, 1), self.item._data['level'])
        self.assertTrue(self.item.valid())

    def test_load_error(self):
        """Verify an exception is raised with invalid YAML."""
        self.item._file = "markdown: **Document and Item Creation**"
        self.assertRaises(DoorstopError, self.item.load)

    def test_save_empty(self):
        """Verify saving calls write."""
        self.item.save()
        text = ("active: true" + '\n'
                "derived: false" + '\n'
                "level: 1.0" + '\n'
                "links: []" + '\n'
                "normative: true" + '\n'
                "ref: ''" + '\n'
                "text: ''" + '\n')
        self.item._write.assert_called_once_with(text)

    def test_str(self):
        """Verify an item can be converted to strings."""
        common.VERBOSITY = 2
        self.assertEqual("RQ001", str(self.item))

    def test_str_verbose(self):
        """Verify an item can be converted to strings in verbose mode."""
        common.VERBOSITY = 3
        text = "RQ001 (@{}{})".format(os.sep, self.item.path)
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

    def test_relpath(self):
        """Verify an item's relative path string can be read but not set."""
        text = "@{}{}".format(os.sep, self.item.path)
        self.assertEqual(text, self.item.relpath)
        self.assertRaises(AttributeError, setattr, self.item, 'relpath', '.')

    def test_id_relpath(self):
        """Verify an item's ID and relative path string can be read."""
        text = "{} (@{}{})".format(self.item.id, os.sep, self.item.path)
        self.assertEqual(text, self.item.id_relpath)

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

    def test_depth(self):
        """Verify the depth can be read from the item's level."""
        self.item.level = (1,)
        self.assertEqual(1, self.item.depth)
        self.item.level = (1, 0)
        self.assertEqual(1, self.item.depth)
        self.item.level = (2, 0, 1)
        self.assertEqual(3, self.item.depth)
        self.item.level = (2, 0, 1, 1, 0, 0)
        self.assertEqual(4, self.item.depth)

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
        self.assertIn("level: 42.0\n", self.item._write.call_args[0][0])
        self.assertEqual((42, 0), self.item.level)

    def test_active(self):
        """Verify an item's active status can be set and read."""
        self.item.active = 0  # converted to False
        self.assertIn("active: false\n", self.item._write.call_args[0][0])
        self.assertFalse(self.item.active)

    def test_normative(self):
        """Verify an item's normative status can be set and read."""
        self.item.normative = 0  # converted to False
        self.assertIn("normative: false\n", self.item._write.call_args[0][0])
        self.assertFalse(self.item.normative)

    def test_derived(self):
        """Verify an item's normative status can be set and read."""
        self.item.derived = 1  # converted to True
        self.assertIn("derived: true\n", self.item._write.call_args[0][0])
        self.assertTrue(self.item.derived)

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

    def test_extended(self):
        """Verify an extended attribute can be used."""
        self.item.set('ext1', 'foobar')
        self.assertEqual('foobar', self.item.get('ext1'))

    def test_extended_get_standard(self):
        """Verify extended attribute access can get standard properties."""
        active = self.item.get('active')
        self.assertEqual(self.item.active, active)

    def test_extended_set_standard(self):
        """Verify extended attribute access can set standard properties."""
        self.item.set('text', "extended access")
        self.assertEqual("extended access", self.item.text)

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

    def test_find_ref(self):
        """Verify an item's reference can be found."""
        self.item.ref = "REF" + "123"  # to avoid matching in this file
        relpath, line = self.item.find_ref(EXTERNAL)
        self.assertEqual('text.txt', os.path.basename(relpath))
        self.assertEqual(3, line)

    def test_find_rlinks(self):
        """Verify an item's reverse links can be found."""

        mock_document = Mock()
        mock_document.parent = 'RQ'

        mock_item = Mock()
        mock_item.id = 'TST001'
        mock_item.links = ['RQ001']

        def mock_iter(self):  # pylint: disable=W0613
            """Mock Tree.__iter__ to yield a mock Document."""

            def mock_iter2(self):  # pylint: disable=W0613
                """Mock Document.__iter__ to yield a mock Item."""
                yield mock_item

            mock_document.__iter__ = mock_iter2
            yield mock_document

        self.item.add_link('fake1')
        tree = Mock()
        tree.__iter__ = mock_iter
        tree.find_item = lambda identifier: Mock(id='fake1')
        rlinks, childrem = self.item.find_rlinks(tree)
        self.assertEqual(['TST001'], rlinks)
        self.assertEqual([mock_document], childrem)

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
        item = MockItem.new(EMPTY, FILES, 'TEST', '', 42, 5, (1, 2, 3))
        path = os.path.join(EMPTY, 'TEST00042.yml')
        self.assertEqual(path, item.path)
        self.assertEqual((1, 2, 3), item.level)
        MockItem._new.assert_called_once_with(path)

    @patch('doorstop.core.item.Item', MockItem)
    def test_new_special(self):
        """Verify items can be created with a specially named prefix."""
        MockItem._new.reset_mock()
        item = MockItem.new(EMPTY, FILES, 'VSM.HLR_01-002', '-', 42, 3, (1,))
        path = os.path.join(EMPTY, 'VSM.HLR_01-002-042.yml')
        self.assertEqual(path, item.path)
        self.assertEqual((1, 0), item.level)
        MockItem._new.assert_called_once_with(path)

    def test_new_existing(self):
        """Verify an exception is raised if the item already exists."""
        self.assertRaises(DoorstopError,
                          Item.new, FILES, FILES, 'REQ', '', 2, 3, (1, 2, 3))

    def test_valid_invalid_ref(self):
        """Verify an invalid reference fails valid."""
        with patch('doorstop.core.item.Item.find_ref',
                   Mock(side_effect=DoorstopError)):
            self.assertFalse(self.item.valid())

    def test_valid_inactive(self):
        """Verify an inactive item is not checked."""
        self.item.active = False
        with patch('doorstop.core.item.Item.find_ref',
                   Mock(side_effect=DoorstopError)):
            self.assertTrue(self.item.valid())

    def test_valid_nonnormative_with_links(self):
        """Verify a non-normative item with links can be checked."""
        self.item.normative = False
        self.item.links = ['a']
        self.assertTrue(self.item.valid())

    def test_valid_link_to_inactive(self):
        """Verify a link to an inactive item can be checked."""
        item = Mock()
        item.active = False
        tree = MagicMock()
        tree.find_item = Mock(return_value=item)
        self.item.links = ['a']
        self.assertTrue(self.item.valid(tree=tree))

    def test_valid_link_to_nonnormative(self):
        """Verify a link to an non-normative item can be checked."""
        item = Mock()
        item.normative = False
        tree = MagicMock()
        tree.find_item = Mock(return_value=item)
        self.item.links = ['a']
        self.assertTrue(self.item.valid(tree=tree))

    def test_valid_document(self):
        """Verify an item can be checked against a document."""
        document = Mock()
        document.parent = 'fake'
        self.assertTrue(self.item.valid(document=document))

    def test_valid_document_with_links(self):
        """Verify an item can be checked against a document with links."""
        self.item.add_link('unknown1')
        document = Mock()
        document.parent = 'fake'
        self.assertTrue(self.item.valid(document=document))

    def test_valid_tree(self):
        """Verify an item can be checked against a tree."""

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

        self.item.add_link('fake1')
        tree = Mock()
        tree.__iter__ = mock_iter
        tree.find_item = lambda identifier: Mock(id='fake1')
        self.assertTrue(self.item.valid(tree=tree))

    def test_valid_tree_no_reverse_links(self):
        """Verify an item can be checked against a tree (no reverse links)."""

        def mock_iter(self):  # pylint: disable=W0613
            """Mock Tree.__iter__ to yield a mock Document."""
            mock_document = Mock()
            mock_document.parent = 'RQ'

            def mock_iter2(self):  # pylint: disable=W0613
                """Mock Document.__iter__ to yield a mock Item."""
                mock_item = Mock()
                mock_item.id = 'TST001'
                mock_item.links = []
                yield mock_item

            mock_document.__iter__ = mock_iter2
            yield mock_document

        self.item.add_link('fake1')
        tree = Mock()
        tree.__iter__ = mock_iter
        tree.find_item = lambda identifier: Mock(id='fake1')
        self.assertTrue(self.item.valid(tree=tree))

    def test_valid_tree_error(self):
        """Verify an item can be checked against a tree with errors."""
        self.item.add_link('fake1')
        tree = MagicMock()
        tree.find_item = Mock(side_effect=DoorstopError)
        self.assertFalse(self.item.valid(tree=tree))

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
