#!/usr/bin/env python

"""
Unit tests for the doorstop.core.item module.
"""

import unittest
from unittest.mock import patch, Mock, MagicMock

import os

from doorstop import common
from doorstop.common import DoorstopError
from doorstop.core.item import Item

from doorstop.core.test import ENV, REASON
from doorstop.core.test import FILES, EMPTY, EXTERNAL, MockFileObject


YAML_DEFAULT = """
active: true
derived: false
level: 1.0
links: []
normative: true
ref: ''
text: ''
""".lstrip()


class MockItem(MockFileObject, Item):  # pylint: disable=W0223,R0902,R0904
    """Mock Item class with stubbed file IO."""


class TestItem(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for the Item class."""  # pylint: disable=C0103,W0212

    def setUp(self):
        path = os.path.join('path', 'to', 'RQ001.yml')
        self.item = MockItem(path)

    def test_init_invalid(self):
        """Verify an item cannot be initialized from an invalid path."""
        self.assertRaises(DoorstopError, Item, 'not/a/path')

    def test_load_empty(self):
        """Verify loading calls read."""
        self.item.load()
        self.item._read.assert_called_once_with(self.item.path)

    def test_load_error(self):
        """Verify an exception is raised with invalid YAML."""
        self.item._file = "invalid: -"
        self.assertRaises(DoorstopError, self.item.load)

    def test_load_unexpected(self):
        """Verify an exception is raised for unexpected file contents."""
        self.item._file = "unexpected"
        self.assertRaises(DoorstopError, self.item.load)

    def test_save_empty(self):
        """Verify saving calls write."""
        self.item.save()
        self.item._write.assert_called_once_with(YAML_DEFAULT, self.item.path)

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
        item1 = MockItem('path/to/fake1.yml')
        item1.level = (1, 1)
        item2 = MockItem('path/to/fake1.yml')
        item2.level = (1, 1, 1)
        item3 = MockItem('path/to/fake1.yml')
        item3.level = (1, 1, 2)
        self.assertLess(item1, item2)
        self.assertLess(item2, item3)
        self.assertGreater(item3, item1)

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

    def test_derived(self):
        """Verify an item's normative status can be set and read."""
        self.item.derived = 1  # converted to True
        self.assertIn("derived: true\n", self.item._write.call_args[0][0])
        self.assertTrue(self.item.derived)

    def test_normative(self):
        """Verify an item's normative status can be set and read."""
        self.item.normative = 0  # converted to False
        self.assertIn("normative: false\n", self.item._write.call_args[0][0])
        self.assertFalse(self.item.normative)

    def test_heading(self):
        """Verify an item's heading status can be set and read."""
        self.item.level = '1.1.1'
        self.item.heading = 1  # converted to True
        self.assertEqual(0, self.item.level[-1])
        self.assertFalse(self.item.normative)
        self.assertTrue(self.item.heading)
        self.item.heading = 0  # converted to False
        self.assertNotEqual(0, self.item.level[-1])
        self.assertTrue(self.item.normative)
        self.assertFalse(self.item.heading)

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

        mock_document_p = Mock()
        mock_document_p.prefix = 'RQ'

        mock_document_c = Mock()
        mock_document_c.parent = 'RQ'

        mock_item = Mock()
        mock_item.id = 'TST001'
        mock_item.links = ['RQ001']

        def mock_iter(self):  # pylint: disable=W0613
            """Mock Tree.__iter__ to yield a mock Document."""

            def mock_iter2(self):  # pylint: disable=W0613
                """Mock Document.__iter__ to yield a mock Item."""
                yield mock_item

            mock_document_c.__iter__ = mock_iter2
            yield mock_document_c

        self.item.add_link('fake1')
        mock_tree = Mock()
        mock_tree.__iter__ = mock_iter
        mock_tree.find_item = lambda identifier: Mock(id='fake1')
        rlinks, childrem = self.item.find_rlinks(mock_document_p, mock_tree)
        self.assertEqual(['TST001'], rlinks)
        self.assertEqual([mock_document_c], childrem)

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
        item = MockItem.new(EMPTY, FILES, 'TEST', '', 5, 42, (1, 2, 3))
        path = os.path.join(EMPTY, 'TEST00042.yml')
        self.assertEqual(path, item.path)
        self.assertEqual((1, 2, 3), item.level)
        MockItem._new.assert_called_once_with(path, name='item')

    @patch('doorstop.core.item.Item', MockItem)
    def test_new_special(self):
        """Verify items can be created with a specially named prefix."""
        MockItem._new.reset_mock()
        item = MockItem.new(EMPTY, FILES, 'VSM.HLR_01-002', '-', 3, 42, (1,))
        path = os.path.join(EMPTY, 'VSM.HLR_01-002-042.yml')
        self.assertEqual(path, item.path)
        self.assertEqual((1, 0), item.level)
        MockItem._new.assert_called_once_with(path, name='item')

    def test_new_existing(self):
        """Verify an exception is raised if the item already exists."""
        self.assertRaises(DoorstopError,
                          Item.new, FILES, FILES, 'REQ', '', 3, 2, (1, 2, 3))

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
        mock_item = Mock()
        mock_item.active = False
        mock_tree = MagicMock()
        mock_tree.find_item = Mock(return_value=mock_item)
        self.item.links = ['a']
        self.assertTrue(self.item.valid(tree=mock_tree))

    def test_valid_link_to_nonnormative(self):
        """Verify a link to an non-normative item can be checked."""
        mock_item = Mock()
        mock_item.normative = False
        mock_tree = MagicMock()
        mock_tree.find_item = Mock(return_value=mock_item)
        self.item.links = ['a']
        self.assertTrue(self.item.valid(tree=mock_tree))

    def test_valid_document(self):
        """Verify an item can be checked against a document."""
        mock_document = Mock()
        mock_document.parent = 'fake'
        self.assertTrue(self.item.valid(document=mock_document))

    def test_valid_document_with_links(self):
        """Verify an item can be checked against a document with links."""
        self.item.add_link('unknown1')
        mock_document = Mock()
        mock_document.parent = 'fake'
        self.assertTrue(self.item.valid(document=mock_document))

    def test_valid_document_with_bad_link_IDs(self):
        """Verify an item can be checked against a document w/ bad link IDs."""
        self.item.add_link('invalid')
        mock_document = Mock()
        mock_document.parent = 'fake'
        self.assertFalse(self.item.valid(document=mock_document))

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

        mock_tree = Mock()
        mock_tree.__iter__ = mock_iter
        mock_tree.find_item = lambda identifier: Mock(id='fake1')

        self.assertTrue(self.item.valid(tree=mock_tree))

    def test_valid_tree_error(self):
        """Verify an item can be checked against a tree with errors."""
        self.item.add_link('fake1')
        tree = MagicMock()
        tree.find_item = Mock(side_effect=DoorstopError)
        self.assertFalse(self.item.valid(tree=tree))

    def test_valid_both(self):
        """Verify an item can be checked against both."""

        def mock_iter(seq):
            """Creates a mock __iter__ method."""
            def _iter(self):  # pylint: disable=W0613
                """Mock __iter__method."""
                yield from seq
            return _iter

        mock_item = Mock()
        mock_item.links = [self.item.id]

        mock_document = Mock()
        mock_document.parent = 'BOTH'
        mock_document.prefix = 'BOTH'

        mock_document.__iter__ = mock_iter([mock_item])
        mock_tree = Mock()
        mock_tree.__iter__ = mock_iter([mock_document])

        self.assertTrue(self.item.valid(document=mock_document,
                                        tree=mock_tree))

    def test_valid_both_no_reverse_links(self):
        """Verify an item can be checked against both (no reverse links)."""

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

        mock_document = Mock()
        mock_document.prefix = 'RQ'

        mock_tree = Mock()
        mock_tree.__iter__ = mock_iter
        mock_tree.find_item = lambda identifier: Mock(id='fake1')

        self.assertTrue(self.item.valid(document=mock_document,
                                        tree=mock_tree))

    @patch('os.remove')
    def test_delete(self, mock_remove):
        """Verify an item can be deleted."""
        self.item.delete()
        mock_remove.assert_called_once_with(self.item.path)
        self.item.delete()  # ensure a second delete is ignored


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

    pass


if __name__ == '__main__':
    unittest.main()
