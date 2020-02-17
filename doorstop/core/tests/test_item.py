# SPDX-License-Identifier: LGPL-3.0-only
# pylint: disable=C0302

"""Unit tests for the doorstop.core.item module."""

import logging
import os
import unittest
from typing import List
from unittest.mock import MagicMock, Mock, patch

from doorstop import common
from doorstop.common import DoorstopError
from doorstop.core.item import Item, UnknownItem
from doorstop.core.tests import (
    EMPTY,
    EXTERNAL,
    FILES,
    TESTS_ROOT,
    MockItem,
    MockSimpleDocument,
)
from doorstop.core.types import Stamp, Text
from doorstop.core.vcs.mockvcs import WorkingCopy

YAML_DEFAULT = """
active: true
derived: false
header: ''
level: 1.0
links: []
normative: true
ref: ''
reviewed: null
text: ''
""".lstrip()

YAML_EXTENDED_ATTRIBUTES = """
a:
- b
- c
active: true
d:
  e: f
  g: h
derived: false
header: ''
i: j
k: null
level: 1.0
links: []
normative: true
ref: ''
reviewed: null
text: |
  something
""".lstrip()

YAML_STRING_ATTRIBUTES = """
aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa: |
  b
active: true
cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc: d
derived: false
e: |
  fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
g: hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh
header: ''
i:
  jjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjj: |
    k
  llllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllll: m
  n: |
    ooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo
  p: qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq
  r:
  - |
    ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss
  - ttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttt
level: 1.0
links: []
normative: true
ref: ''
reviewed: null
text: ''
""".lstrip()


class ListLogHandler(logging.NullHandler):
    def __init__(self, log):
        super().__init__()
        self.records: List[str] = []
        self.log = log

    def __enter__(self):
        self.log.addHandler(self)
        return self

    def __exit__(self, kind, value, traceback):
        self.log.removeHandler(self)

    def handle(self, record):
        self.records.append(str(record.msg))


class TestItem(unittest.TestCase):
    """Unit tests for the Item class."""

    # pylint: disable=protected-access,no-value-for-parameter

    def setUp(self):
        path = os.path.join('path', 'to', 'RQ001.yml')
        self.item = MockItem(MockSimpleDocument(), path)

    def test_init_invalid(self):
        """Verify an item cannot be initialized from an invalid path."""
        self.assertRaises(DoorstopError, Item, None, 'not/a/path')

    def test_no_tree_references(self):
        """Verify a standalone item has no tree reference."""
        self.assertIs(None, self.item.tree)

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

    def test_set_attributes(self):
        """Verify setting attributes calls write with the attributes."""
        self.item.set_attributes(
            {
                'a': ['b', 'c'],
                'd': {'e': 'f', 'g': 'h'},
                'i': 'j',
                'k': None,
                'text': 'something',
            }
        )
        self.item._write.assert_called_once_with(
            YAML_EXTENDED_ATTRIBUTES, self.item.path
        )

    def test_string_attributes(self):
        """Verify string attributes are properly formatted."""
        self.item.set_attributes(
            {
                'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa': 'b',
                'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc': 'd',
                'e': 'fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff',
                'g': 'hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh',
                'i': {
                    'jjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjj': 'k',
                    'llllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllll': 'm',
                    'n': 'ooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo',
                    'p': 'qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq',
                    'r': [
                        'ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss',
                        'ttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttt',
                    ],
                },
            }
        )
        self.item._write.assert_called_once_with(YAML_STRING_ATTRIBUTES, self.item.path)

    def test_set_attributes_reference_valid_input(self):
        """Verify that setting 'references' with a correct value does not raise errors."""
        try:
            self.item._set_attributes(
                {'references': [{'type': 'file', 'path': 'some/path'}]}
            )
        except AttributeError:
            self.fail("didn't expect _set_attributes to raise AttributeError")

    def test_set_attributes_reference_malformed_input(self):
        """Verify that setting 'references' with a wrong value raises errors."""
        with self.assertRaises(AttributeError):
            self.item._set_attributes({'references': 'foo'})
        with self.assertRaises(AttributeError):
            self.item._set_attributes({'references': ['foo']})
        with self.assertRaises(AttributeError):
            self.item._set_attributes({'references': [{'type': 'FOO'}]})
        with self.assertRaises(AttributeError):
            self.item._set_attributes({'references': [{'type': 'file'}]})
        with self.assertRaises(AttributeError):
            self.item._set_attributes(
                {'references': [{'type': 'file', 'path': 0xDEAD}]}
            )

    @patch('doorstop.common.verbosity', 2)
    def test_str(self):
        """Verify an item can be converted to a string."""
        self.assertEqual("RQ001", str(self.item))

    @patch('doorstop.common.verbosity', 3)
    def test_str_verbose(self):
        """Verify an item can be converted to a string (verbose)."""
        text = "RQ001 (@{}{})".format(os.sep, self.item.path)
        self.assertEqual(text, str(self.item))

    def test_hash(self):
        """Verify items can be hashed."""
        item1 = MockItem(None, 'path/to/fake1.yml')
        item2 = MockItem(None, 'path/to/fake2.yml')
        item3 = MockItem(None, 'path/to/fake2.yml')
        my_set = set()
        # Act
        my_set.add(item1)
        my_set.add(item2)
        my_set.add(item3)
        # Assert
        self.assertEqual(2, len(my_set))

    def test_ne(self):
        """Verify item non-equality is correct."""
        self.assertNotEqual(self.item, None)

    def test_lt(self):
        """Verify items can be compared."""
        item1 = MockItem(None, 'path/to/fake1.yml')
        item1.level = (1, 1)  # type: ignore
        item2 = MockItem(None, 'path/to/fake1.yml')
        item2.level = (1, 1, 1)  # type: ignore
        item3 = MockItem(None, 'path/to/fake1.yml')
        item3.level = (1, 1, 2)  # type: ignore
        self.assertLess(item1, item2)
        self.assertLess(item2, item3)
        self.assertGreater(item3, item1)

    def test_uid(self):
        """Verify an item's UID can be read but not set."""
        self.assertEqual('RQ001', self.item.uid)
        self.assertRaises(AttributeError, setattr, self.item, 'uid', 'RQ002')

    def test_relpath(self):
        """Verify an item's relative path string can be read but not set."""
        text = "@{}{}".format(os.sep, self.item.path)
        self.assertEqual(text, self.item.relpath)
        self.assertRaises(AttributeError, setattr, self.item, 'relpath', '.')

    def test_level(self):
        """Verify an item's level can be set and read."""
        self.item.level = (1, 2, 3)
        self.assertIn("level: 1.2.3\n", self.item._write.call_args[0][0])
        self.assertEqual((1, 2, 3), self.item.level)

    def test_level_with_float(self):
        """Verify an item's level can be set and read (2-part w/ float)."""
        self.item.level = (1, 10)
        self.assertIn("level: '1.10'\n", self.item._write.call_args[0][0])
        self.assertEqual((1, 10), self.item.level)

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
        self.assertEqual((4, 2), self.item.level)

    def test_level_from_text_2_digits(self):
        """Verify an item's level can be set from text (2 digits) and read."""
        self.item.level = "10.10"
        self.assertIn("level: '10.10'\n", self.item._write.call_args[0][0])
        self.assertEqual((10, 10), self.item.level)

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
        self.assertFalse(self.item.normative)
        self.assertTrue(self.item.heading)
        self.item.heading = 0  # converted to False
        self.assertTrue(self.item.normative)
        self.assertFalse(self.item.heading)

    def test_reviewed(self):
        """Verify an item's review status can be set and read."""
        self.assertFalse(self.item.reviewed)  # not reviewed by default
        self.item.reviewed = 1  # calls `review()`
        self.assertTrue(self.item.reviewed)
        self.item.reviewed = 0  # converted to None
        self.assertFalse(self.item.reviewed)

    def test_text(self):
        """Verify an item's text can be set and read."""
        value = "abc "
        text = "abc"
        yaml = "text: |\n  abc\n"
        self.item.text = value
        self.assertEqual(text, self.item.text)
        self.assertIn(yaml, self.item._write.call_args[0][0])

    def test_text_sbd(self):
        """Verify newlines separate sentences in an item's text."""
        value = (
            "A sentence. Another sentence! Hello? Hi.\n"
            "A new line (here). And another sentence."
        )
        text = (
            "A sentence. Another sentence! Hello? Hi.\n"
            "A new line (here). And another sentence."
        )
        yaml = (
            "text: |\n"
            "  A sentence. Another sentence! Hello? Hi.\n"
            "  A new line (here). And another sentence.\n"
        )
        self.item.text = value
        self.assertEqual(text, self.item.text)
        self.assertIn(yaml, self.item._write.call_args[0][0])

    def test_text_ordered_list(self):
        """Verify newlines are preserved in an ordered list."""
        self.item.text = "A list:\n\n1. Abc\n2. Def\n"
        expected = "A list:\n\n1. Abc\n2. Def"
        self.assertEqual(expected, self.item.text)

    def test_text_unordered_list(self):
        """Verify newlines are preserved in an ordered list."""
        self.item.text = "A list:\n\n- Abc\n- Def\n"
        expected = "A list:\n\n- Abc\n- Def"
        self.assertEqual(expected, self.item.text)

    def test_text_split_numbers(self):
        """Verify lines ending in numbers aren't changed."""
        self.item.text = "Split at a number: 1\n42 or punctuation.\nHere."
        expected = "Split at a number: 1\n42 or punctuation.\nHere."
        self.assertEqual(expected, self.item.text)

    def test_text_newlines(self):
        """Verify newlines are preserved when deliberate."""
        self.item.text = "Some text.\n\nNote: here.\n"
        expected = "Some text.\n\nNote: here."
        self.assertEqual(expected, self.item.text)

    def test_text_formatting(self):
        """Verify newlines are not removed around formatting."""
        self.item.text = "The thing\n**_SHALL_** do this.\n"
        expected = "The thing\n**_SHALL_** do this."
        self.assertEqual(expected, self.item.text)

    def test_text_non_heading(self):
        """Verify newlines are preserved around non-headings."""
        self.item.text = "break (before \n#2) symbol should not be a heading."
        expected = "break (before\n#2) symbol should not be a heading."
        self.assertEqual(expected, self.item.text)

    def test_text_heading(self):
        """Verify newlines are preserved around headings."""
        self.item.text = "should be a heading\n\n# right here"
        expected = "should be a heading\n\n# right here"
        self.assertEqual(expected, self.item.text)

    def test_ref(self):
        """Verify an item's reference can be set and read."""
        self.item.ref = "abc123"
        self.assertIn("ref: abc123\n", self.item._write.call_args[0][0])
        self.assertNotIn("references:", self.item._write.call_args[0][0])
        self.assertEqual("abc123", self.item.ref)

    def test_references(self):
        """Verify an item's reference can be set and read."""
        references = [
            {'type': 'file', 'path': 'abc1'},
            {"type": "file", "path": "abc2"},
        ]
        self.item.references = references
        self.assertIn(
            "references:\n- path: abc1\n  type: file\n- path: abc2\n  type: file",
            self.item._write.call_args[0][0],
        )
        # We let 'references' and 'ref' co-exist for now.
        self.assertIn("ref: ''", self.item._write.call_args[0][0])
        self.assertListEqual(references, self.item.references)

    def test_extended(self):
        """Verify an extended attribute (`str`) can be used."""
        self.item.set('ext1', 'foobar')
        self.assertIn("ext1: foobar\n", self.item._write.call_args[0][0])
        self.assertEqual('foobar', self.item.get('ext1'))
        self.assertEqual(['ext1'], self.item.extended)

    def test_extended_text(self):
        """Verify an extended attribute (`Text`) can be used."""
        self.item.set('ext1', Text('foobar'))
        self.assertIn("ext1: foobar\n", self.item._write.call_args[0][0])
        self.assertEqual('foobar', self.item.get('ext1'))
        self.assertEqual(['ext1'], self.item.extended)

    def test_extended_wrap(self):
        """Verify a long extended attribute is wrapped."""
        text = "This extended attribute should be long enough to wrap."
        self.item.set('a_very_long_extended_attr', text)
        self.assertEqual(text, self.item.get('a_very_long_extended_attr'))

    def test_extended_wrap_multi(self):
        """Verify a long extended attribute is wrapped with newlines."""
        text = "Another extended attribute.\n\nNote: with a note."
        self.item.set('ext2', text)
        self.assertEqual(text, self.item.get('ext2'))

    def test_extended_get_standard(self):
        """Verify extended attribute access can get standard properties."""
        active = self.item.get('active')
        self.assertEqual(self.item.active, active)

    def test_extended_set_standard(self):
        """Verify extended attribute access can set standard properties."""
        self.item.set('text', "extended access")
        self.assertEqual("extended access", self.item.text)

    @patch('doorstop.core.item.Item.load')
    @patch('doorstop.core.editor.launch')
    def test_edit(self, mock_launch, mock_load):
        """Verify an item can be edited."""
        self.item.tree = Mock()
        # Act
        self.item.edit(tool='mock_editor')
        # Assert
        self.item.tree.vcs.lock.assert_called_once_with(self.item.path)
        self.item.tree.vcs.edit.assert_called_once_with(self.item.path)
        mock_launch.assert_called_once_with(self.item.path, tool='mock_editor')
        mock_load.assert_called_once_with(True)

    def test_link(self):
        """Verify links can be added to an item."""
        self.item.link('abc')
        self.item.link('123')
        self.assertEqual(['123', 'abc'], self.item.links)

    def test_link_duplicate(self):
        """Verify duplicate links are ignored."""
        self.item.link('abc')
        self.item.link('abc')
        self.assertEqual(['abc'], self.item.links)

    def test_unlink_duplicate(self):
        """Verify removing a link twice is not an error."""
        self.item.links = ['123', 'abc']
        self.item.unlink('abc')
        self.item.unlink('abc')
        self.assertEqual(['123'], self.item.links)

    def test_link_by_item(self):
        """Verify links can be added to an item (by item)."""
        path = os.path.join('path', 'to', 'ABC123.yml')
        item = MockItem(None, path)
        self.item.link(item)
        self.assertEqual(['ABC123'], self.item.links)

    def test_unlink_by_item(self):
        """Verify links can be removed (by item)."""
        path = os.path.join('path', 'to', 'ABC123.yml')
        item = MockItem(None, path)
        self.item.links = ['ABC123']
        self.item.unlink(item)
        self.assertEqual([], self.item.links)

    def test_links_alias(self):
        """Verify 'parent_links' is an alias for links."""
        links1 = ['alias1']
        links2 = ['alias2']
        self.item.parent_links = links1
        self.assertEqual(links1, self.item.links)
        self.item.links = links2
        self.assertEqual(links2, self.item.parent_links)

    def test_parent_items(self):
        """Verify 'parent_items' exists to mirror the child behavior."""
        mock_tree = Mock()
        mock_tree.find_item = Mock(return_value='mock_item')
        self.item.tree = mock_tree
        self.item.links = ['mock_uid']
        # Act
        items = self.item.parent_items
        # Assert
        self.assertEqual(['mock_item'], items)

    def test_parent_items_unknown(self):
        """Verify 'parent_items' can handle unknown items."""
        mock_tree = Mock()
        mock_tree.find_item = Mock(side_effect=DoorstopError)
        self.item.tree = mock_tree
        self.item.links = ['mock_uid']
        # Act
        items = self.item.parent_items
        # Assert
        self.assertIsInstance(items[0], UnknownItem)

    def test_parent_documents(self):
        """Verify 'parent_documents' exists to mirror the child behavior."""
        mock_tree = Mock()
        mock_tree.find_document = Mock(return_value='mock_document')
        self.item.tree = mock_tree
        self.item.links = ['mock_uid']
        self.item.document = Mock()
        self.item.document.prefix = 'mock_prefix'
        # Act
        documents = self.item.parent_documents
        # Assert
        self.assertEqual(['mock_document'], documents)

    def test_parent_documents_unknown(self):
        """Verify 'parent_documents' can handle unknown documents."""
        mock_tree = Mock()
        mock_tree.find_document = Mock(side_effect=DoorstopError)
        self.item.tree = mock_tree
        self.item.links = ['mock_uid']
        self.item.document = Mock()
        self.item.document.prefix = 'mock_prefix'
        # Act
        documents = self.item.parent_documents
        # Assert
        self.assertEqual([], documents)

    @patch('doorstop.settings.CACHE_PATHS', False)
    def test_find_ref(self):
        """Verify an item's reference can be found."""
        self.item.ref = "REF" "123"  # space to avoid matching in this file
        self.item.tree = Mock()
        self.item.tree.vcs = WorkingCopy(EXTERNAL)
        # Act
        relpath, line = self.item.find_ref()
        # Assert
        self.assertEqual('text.txt', os.path.basename(relpath))
        self.assertEqual(3, line)

    def test_find_ref_filename(self):
        """Verify an item's reference can also be a filename."""
        self.item.ref = "text.txt"
        self.item.tree = Mock()
        self.item.tree.vcs = WorkingCopy(FILES)
        self.item.tree.vcs._ignores_cache = ["*published*"]
        # Act
        relpath, line = self.item.find_ref()
        # Assert
        self.assertEqual('text.txt', os.path.basename(relpath))
        self.assertEqual(None, line)

    def test_find_ref_error(self):
        """Verify an error occurs when no external reference found."""
        self.item.ref = "not" "found"  # space to avoid matching in this file
        self.item.tree = Mock()
        self.item.tree.vcs = WorkingCopy(EMPTY)
        # Act and assert
        self.assertRaises(DoorstopError, self.item.find_ref)

    def test_find_skip_self(self):
        """Verify reference searches skip the item's file."""
        self.item.path = __file__
        self.item.ref = "148710938710289248"  # random and unique to this file
        self.item.tree = Mock()
        self.item.tree.vcs = WorkingCopy(EMPTY)
        self.item.tree.vcs._path_cache = [(__file__, 'filename', 'relpath')]
        # Act and assert
        self.assertRaises(DoorstopError, self.item.find_ref)

    def test_find_ref_none(self):
        """Verify nothing returned when no external reference is specified."""
        self.item.tree = Mock()
        self.assertEqual((None, None), self.item.find_ref())

    @patch('doorstop.settings.CACHE_PATHS', False)
    def test_find_references(self):
        """Verify an item's references can be found."""
        self.item.references = [
            {"path": "files/REQ001.yml"},
            {"path": "files/REQ002.yml"},
        ]

        self.item.root = TESTS_ROOT
        self.item.tree = Mock()
        self.item.tree.vcs = WorkingCopy(TESTS_ROOT)

        # Act
        ref = self.item.find_references()

        # Assert
        self.assertEqual(2, len(ref))

        relpath_1, keyword_line_1 = ref[0]
        self.assertEqual(relpath_1, os.path.join('files', 'REQ001.yml'))
        self.assertEqual(keyword_line_1, None)

        relpath_2, keyword_line_2 = ref[1]
        self.assertEqual(relpath_2, os.path.join('files', 'REQ002.yml'))
        self.assertEqual(keyword_line_2, None)

    @patch('doorstop.settings.CACHE_PATHS', False)
    def test_find_references_valid_keyword(self):
        """Verify an item's references can be found."""
        keyword = "Lorem ipsum dolor sit amet"
        self.item.references = [{"path": "files/REQ001.yml", "keyword": keyword}]

        self.item.root = TESTS_ROOT
        self.item.tree = Mock()
        self.item.tree.vcs = WorkingCopy(TESTS_ROOT)

        # Act
        ref = self.item.find_references()

        # Assert
        self.assertEqual(1, len(ref))

        ref_path, ref_keyword_line = ref[0]
        self.assertEqual(ref_path, os.path.join('files', 'REQ001.yml'))
        self.assertEqual(ref_keyword_line, 12)

    @patch('doorstop.settings.CACHE_PATHS', False)
    def test_find_references_invalid_keyword(self):
        """Verify an item's references can be found."""
        self.item.references = [
            {"path": "files/REQ001.yml", "keyword": "INVALID KEYWORD"}
        ]

        self.item.root = TESTS_ROOT
        self.item.tree = Mock()
        self.item.tree.vcs = WorkingCopy(TESTS_ROOT)

        with self.assertRaises(DoorstopError) as context:
            self.item.find_references()

        self.assertTrue('external reference not found' in str(context.exception))

    def test_find_ref_error_multiple(self):
        """Verify an error occurs when no external reference found."""
        self.item.references = [{"path": "this/path/does/not/exist.yml"}]
        self.item.tree = Mock()
        self.item.tree.vcs = WorkingCopy(EMPTY)
        # Act and assert
        self.assertRaises(DoorstopError, self.item.find_references)

    def test_find_child_objects(self):
        """Verify an item's child objects can be found."""

        mock_document_p = Mock()
        mock_document_p.prefix = 'RQ'

        mock_document_c = Mock()
        mock_document_c.parent = 'RQ'

        mock_item = Mock()
        mock_item.uid = 'TST001'
        mock_item.links = ['RQ001']

        def mock_iter(self):  # pylint: disable=W0613
            """Mock Tree.__iter__ to yield a mock Document."""

            def mock_iter2(self):  # pylint: disable=W0613
                """Mock Document.__iter__ to yield a mock Item."""
                yield mock_item

            mock_document_c.__iter__ = mock_iter2
            yield mock_document_c

        self.item.link('fake1')
        mock_tree = Mock()
        mock_tree.__iter__ = mock_iter
        mock_tree.find_item = lambda uid: Mock(uid='fake1')
        self.item.tree = mock_tree
        self.item.document = mock_document_p

        links = self.item.find_child_links()
        items = self.item.find_child_items()
        documents = self.item.find_child_documents()
        self.assertEqual(['TST001'], links)
        self.assertEqual([mock_item], items)
        self.assertEqual([mock_document_c], documents)

    def test_find_child_objects_standalone(self):
        """Verify a standalone item has no child objects."""
        self.assertEqual([], self.item.child_links)
        self.assertEqual([], self.item.child_items)
        self.assertEqual([], self.item.child_documents)

    def test_invalid_file_name(self):
        """Verify an invalid file name cannot be a requirement."""
        self.assertRaises(DoorstopError, MockItem, None, "path/to/REQ.yaml")
        self.assertRaises(DoorstopError, MockItem, None, "path/to/001.yaml")

    def test_invalid_file_ext(self):
        """Verify an invalid file extension cannot be a requirement."""
        self.assertRaises(DoorstopError, MockItem, None, "path/to/REQ001")
        self.assertRaises(DoorstopError, MockItem, None, "path/to/REQ001.txt")

    @patch('doorstop.core.item.Item', MockItem)
    def test_new(self):
        """Verify items can be created."""
        MockItem._create.reset_mock()
        item = MockItem.new(
            None, MockSimpleDocument(), EMPTY, FILES, 'TEST00042', level=(1, 2, 3)
        )
        path = os.path.join(EMPTY, 'TEST00042.yml')
        self.assertEqual(path, item.path)
        self.assertEqual((1, 2, 3), item.level)
        MockItem._create.assert_called_once_with(path, name='item')

    @patch('doorstop.core.item.Item', MockItem)
    def test_new_cache(self):
        """Verify new items are cached."""
        mock_tree = Mock()
        mock_tree._item_cache = {}
        item = MockItem.new(
            mock_tree, MockSimpleDocument(), EMPTY, FILES, 'TEST00042', level=(1, 2, 3)
        )
        self.assertEqual(item, mock_tree._item_cache[item.uid])
        mock_tree.vcs.add.assert_called_once_with(item.path)

    @patch('doorstop.core.item.Item', MockItem)
    def test_new_special(self):
        """Verify items can be created with a specially named prefix."""
        MockItem._create.reset_mock()
        item = MockItem.new(
            None, MockSimpleDocument(), EMPTY, FILES, 'VSM.HLR_01-002-042', level=(1, 0)
        )
        path = os.path.join(EMPTY, 'VSM.HLR_01-002-042.yml')
        self.assertEqual(path, item.path)
        self.assertEqual((1,), item.level)
        MockItem._create.assert_called_once_with(path, name='item')

    def test_new_existing(self):
        """Verify an exception is raised if the item already exists."""
        self.assertRaises(
            DoorstopError, Item.new, None, None, FILES, FILES, 'REQ002', level=(1, 2, 3)
        )

    def test_stamp(self):
        """Verify an item's contents can be stamped."""
        stamp = 'OoHOpBnrt8us7ph8DVnz5KrQs6UBqj_8MEACA0gWpjY='
        self.assertEqual(stamp, self.item.stamp())

    def test_stamp_contribution_references(self):
        """Verify that references attribute contributes to a stamp."""
        expected_stamp_before = 'OoHOpBnrt8us7ph8DVnz5KrQs6UBqj_8MEACA0gWpjY='

        stamp_before = self.item.stamp()
        self.assertEqual(expected_stamp_before, stamp_before)

        self.item.references = [{'type': 'file', 'path': 'foo'}]

        stamp_after = self.item.stamp()
        self.assertNotEqual(stamp_after, expected_stamp_before)

    def test_stamp_with_one_extended_reviewed(self):
        """Verify fingerprint with one extended reviewed attribute."""
        self.item._data['type'] = 'functional'
        self.item.document.extended_reviewed = ['type']
        stamp = 'MmcvtzB20PHv0IBhxpNtpZCa0CfYwHnPr3Jk8W-TRxk='
        self.assertEqual(stamp, self.item.stamp())
        self.item.document.extended_reviewed = []
        stamp = 'OoHOpBnrt8us7ph8DVnz5KrQs6UBqj_8MEACA0gWpjY='
        self.assertEqual(stamp, self.item.stamp())

    def test_stamp_with_complex_extended_reviewed(self):
        """Verify fingerprint with complex extended reviewed attribute."""
        self.item.document.extended_reviewed = ['attr']
        self.item._data['attr'] = ['a', 'b', ['c', {'d': 'e', 'f': ['g']}]]
        stamp = 'JcCRKBgLLTOatY8OpAMabblP7Mu24JZRn3WgoXwjmSk='
        self.assertEqual(stamp, self.item.stamp())

    def test_stamp_with_none_extended_reviewed(self):
        """Verify fingerprint with None extended reviewed attribute."""
        self.item.document.extended_reviewed = ['attr']
        self.item._data['attr'] = None
        stamp = 'e0qDli7ZJwhf161b_v7AdGNNl7xHx-bs28aFFk7aqT4='
        self.assertEqual(stamp, self.item.stamp())

    def test_stamp_with_value_one_extended_reviewed(self):
        """Verify fingerprint with value one extended reviewed attribute."""
        self.item.document.extended_reviewed = ['attr']
        self.item._data['attr'] = 1
        stamp = '0s4QQh2AZXSoZNYGcfybCGLHAgO4EWY9gxK_LVNiqOA='
        self.assertEqual(stamp, self.item.stamp())
        self.item._data['attr'] = '1'
        stamp = 'GWlkpsRSzT_lgE4CNvE4wrUZZwM3iHKHOa6idcHUSUw='
        self.assertEqual(stamp, self.item.stamp())

    def test_stamp_with_empty_string_extended_reviewed(self):
        """Verify fingerprint with empty string extended reviewed attribute."""
        self.item.document.extended_reviewed = ['attr']
        self.item._data['attr'] = ''
        stamp = 'H70VgWPTH89Q9KfIJBfeilC7-wYAtWigxZ2iUcZ9j-8='
        self.assertEqual(stamp, self.item.stamp())

    def test_stamp_with_list_extended_reviewed(self):
        """Verify fingerprint with list extended reviewed attributes."""
        self.item.document.extended_reviewed = ['attr']
        self.item._data['attr'] = []
        stamp = 'qwUP7VgUbHWIdj-T2ZfGhROfJQwSHDhsC6WR9vUTk1U='
        self.assertEqual(stamp, self.item.stamp())
        self.item._data['attr'] = [None]
        stamp = 'GHDRiY4C3twnXDTCqoCAD_iymfe892ZzQuYjuccFBT0='
        self.assertEqual(stamp, self.item.stamp())
        self.item._data['attr'] = ['']
        stamp = 'Rfwtl2j56CdQLtE4b5StEa0ECVTqlOpABLdhEa1avyo='
        self.assertEqual(stamp, self.item.stamp())
        self.item._data['attr'] = [[]]
        stamp = 'AXWIEp9CYI4UWzIw4NinvDrUFzQl_8rCL9B_PmGisYk='
        self.assertEqual(stamp, self.item.stamp())
        self.item._data['attr'] = [{}]
        stamp = 'C5Bm5ej09zaJxbtbE9PIcno8M9lIBIC6sJOmNJkrJH8='
        self.assertEqual(stamp, self.item.stamp())

    def test_stamp_with_empty_dict_extended_reviewed(self):
        """Verify fingerprint with empty dict extended reviewed attribute."""
        self.item.document.extended_reviewed = ['attr']
        self.item._data['attr'] = {}
        stamp = '5Yv0vWG2h5rAQt_1LujZuD9X6udWO52KVaSA5SJ3Emc='
        self.assertEqual(stamp, self.item.stamp())

    def test_stamp_with_two_extended_reviewed(self):
        """Verify fingerprint with two extended reviewed attributes."""
        self.item._data['type'] = 'functional'
        self.item._data['verification-method'] = 'test'
        self.item.document.extended_reviewed = ['type', 'verification-method']
        stamp = 'TF_q0ofVwjaJI1RYu9jtDeSCm5gAQWIqsxpPxAW5D64='
        self.assertEqual(stamp, self.item.stamp())

    def test_stamp_with_reversed_extended_reviewed(self):
        """Verify fingerprint with reversed extended reviewed attributes."""
        self.item._data['type'] = 'functional'
        self.item._data['verification-method'] = 'test'
        self.item.document.extended_reviewed = ['verification-method', 'type']
        stamp = 'dMWAazlLoeZSwlD87nEwQtAFq32WQuX_Bd_8kehaKJg='
        self.assertEqual(stamp, self.item.stamp())

    def test_stamp_with_missing_extended_reviewed_reverse(self):
        """Verify fingerprint with missing extended reviewed attributes."""
        self.item._data['type'] = 'functional'
        self.item._data['verification-method'] = 'test'
        self.item.document.extended_reviewed = [
            'missing',
            'type',
            'verification-method',
        ]
        stamp = 'TF_q0ofVwjaJI1RYu9jtDeSCm5gAQWIqsxpPxAW5D64='
        self.assertEqual(stamp, self.item.stamp())
        self.item.document.extended_reviewed = [
            'missing',
            'type',
            'verification-method',
            'missing-2',
        ]
        stamp = 'TF_q0ofVwjaJI1RYu9jtDeSCm5gAQWIqsxpPxAW5D64='
        self.assertEqual(stamp, self.item.stamp())
        self.item.document.extended_reviewed = [
            'type',
            'verification-method',
            'missing-2',
        ]
        stamp = 'TF_q0ofVwjaJI1RYu9jtDeSCm5gAQWIqsxpPxAW5D64='
        self.assertEqual(stamp, self.item.stamp())

    def test_stamp_links(self):
        """Verify an item's contents can be stamped."""
        self.item.link('mock_link')
        stamp = 'yE7YshtnqRzPryOsmNI6nkeRmE97LPB19eenX0b5cIk='
        self.assertEqual(stamp, self.item.stamp(links=True))

    def test_clear(self):
        """Verify an item's links can be cleared as suspect."""
        mock_item = Mock()
        mock_item.uid = 'mock_uid'
        mock_item.stamp = Mock(return_value=Stamp('abc123'))
        mock_tree = MagicMock()
        mock_tree.find_item = Mock(return_value=mock_item)
        self.item.tree = mock_tree
        self.item.link('mock_uid')
        self.assertFalse(self.item.cleared)
        self.assertEqual(None, self.item.links[0].stamp)
        # Act
        self.item.clear()
        # Assert
        self.assertTrue(self.item.cleared)
        self.assertEqual('abc123', self.item.links[0].stamp)

    def test_clear_by_uid(self):
        """Verify an item's links can be cleared as suspect by UID."""
        mock_item = Mock()
        mock_item.uid = 'mock_uid'
        mock_item.stamp = Mock(return_value=Stamp('abc123'))
        mock_tree = MagicMock()
        mock_tree.find_item = Mock(return_value=mock_item)
        self.item.tree = mock_tree
        self.item.link('mock_uid')
        self.assertFalse(self.item.cleared)
        self.assertEqual(None, self.item.links[0].stamp)
        # Act
        self.item.clear(['other_uid'])
        # Assert
        self.assertFalse(self.item.cleared)
        self.assertEqual(None, self.item.links[0].stamp)
        # Act
        self.item.clear(['mock_uid'])
        # Assert
        self.assertTrue(self.item.cleared)
        self.assertEqual('abc123', self.item.links[0].stamp)

    def test_review(self):
        """Verify an item can be marked as reviewed."""
        self.item.reviewed = False
        self.item.review()
        self.assertTrue(self.item.reviewed)

    @patch('doorstop.common.delete')
    def test_delete(self, mock_delete):
        """Verify an item can be deleted."""
        self.item.delete()
        mock_delete.assert_called_once_with(self.item.path)
        self.item.delete()  # ensure a second delete is ignored

    @patch('doorstop.common.delete', Mock())
    def test_delete_cache(self):
        """Verify an item is expunged after delete."""
        self.item.tree = Mock()
        self.item.tree._item_cache = {self.item.uid: self.item}
        self.item.delete()
        self.item.tree.vcs.delete.assert_called_once_with(self.item.path)
        self.assertIs(None, self.item.tree._item_cache[self.item.uid])


class TestFormatting(unittest.TestCase):
    """Unit tests for text formatting in Items."""

    ITEM = os.path.join(FILES, 'REQ001.yml')

    def setUp(self):
        self.backup = common.read_text(self.ITEM)

    def tearDown(self):
        common.write_text(self.backup, self.ITEM)

    def test_load_save(self):
        """Verify text formatting is preserved."""
        item = Item(None, self.ITEM)
        item.load()
        item.save()
        text = common.read_text(self.ITEM)
        self.maxDiff = None
        self.assertEqual(self.backup, text)


class TestUnknownItem(unittest.TestCase):
    """Unit tests for the UnknownItem class."""  # pylint: disable= W0212

    def setUp(self):
        self.item = UnknownItem('RQ001')

    @patch('doorstop.common.verbosity', 2)
    def test_str(self):
        """Verify an unknown item can be converted to a string."""
        self.assertEqual("RQ001", str(self.item))

    @patch('doorstop.common.verbosity', 3)
    def test_str_verbose(self):
        """Verify an unknown item can be converted to a string (verbose)."""
        text = "RQ001 (@{}{})".format(os.sep, '???')
        self.assertEqual(text, str(self.item))

    def test_uid(self):
        """Verify an unknown item's UID can be read but not set."""
        self.assertEqual('RQ001', self.item.uid)
        self.assertRaises(AttributeError, setattr, self.item, 'uid', 'RQ002')

    def test_le(self):
        """Verify unknown item's UID less operator."""
        self.assertTrue(self.item < UnknownItem('RQ002'))
        self.assertFalse(self.item < self.item)

    def test_relpath(self):
        """Verify an item's relative path string can be read but not set."""
        text = "@{}{}".format(os.sep, '???')
        self.assertEqual(text, self.item.relpath)
        self.assertRaises(AttributeError, setattr, self.item, 'relpath', '.')

    @patch('doorstop.core.item.log.debug')
    def test_attributes(self, mock_warning):
        """Verify all other `Item` attributes raise an exception."""
        self.assertRaises(AttributeError, getattr, self.item, 'path')
        self.assertRaises(AttributeError, getattr, self.item, 'text')
        self.assertRaises(AttributeError, getattr, self.item, 'delete')
        self.assertRaises(AttributeError, getattr, self.item, 'not_on_item')
        self.assertEqual(2, mock_warning.call_count)

    @patch('doorstop.core.item.log.debug')
    def test_attributes_with_spec(self, mock_warning):
        """Verify all other `Item` attributes raise an exception."""
        spec = Item(None, os.path.join(FILES, 'REQ001.yml'))
        self.item = UnknownItem(self.item.uid, spec=spec)
        self.assertRaises(AttributeError, getattr, self.item, 'path')
        self.assertRaises(AttributeError, getattr, self.item, 'text')
        self.assertRaises(AttributeError, getattr, self.item, 'delete')
        self.assertRaises(AttributeError, getattr, self.item, 'not_on_item')
        self.assertEqual(3, mock_warning.call_count)

    def test_stamp(self):
        """Verify an unknown item has no stamp."""
        self.assertEqual(Stamp(None), self.item.stamp())
