"""Unit tests for the doorstop.core.item module."""

import unittest
from unittest.mock import patch, Mock, MagicMock

import os

from doorstop import common
from doorstop.common import DoorstopError
from doorstop.core.types import Text, Stamp
from doorstop.core.item import Item, UnknownItem
from doorstop.core.vcs.mockvcs import WorkingCopy

from doorstop.core.test import FILES, EMPTY, EXTERNAL
from doorstop.core.test import MockItem


YAML_DEFAULT = """
active: true
derived: false
level: 1.0
links: []
normative: true
ref: ''
reviewed: null
text: ''
""".lstrip()


class TestItem(unittest.TestCase):
    """Unit tests for the Item class."""  # pylint: disable=W0212

    def setUp(self):
        path = os.path.join('path', 'to', 'RQ001.yml')
        self.item = MockItem(path)

    def test_init_invalid(self):
        """Verify an item cannot be initialized from an invalid path."""
        self.assertRaises(DoorstopError, Item, 'not/a/path')

    def test_object_references(self):
        """Verify a standalone item does not have object references."""
        self.assertIs(None, self.item.document)
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
        item1 = MockItem('path/to/fake1.yml')
        item2 = MockItem('path/to/fake2.yml')
        item3 = MockItem('path/to/fake2.yml')
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
        item1 = MockItem('path/to/fake1.yml')
        item1.level = (1, 1)
        item2 = MockItem('path/to/fake1.yml')
        item2.level = (1, 1, 1)
        item3 = MockItem('path/to/fake1.yml')
        item3.level = (1, 1, 2)
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

    def test_cleared(self):
        """Verify an item's suspect link status can be set and read."""
        mock_item = Mock()
        mock_item.uid = 'mock_uid'
        mock_item.stamp = Mock(return_value=Stamp('abc123'))
        mock_tree = MagicMock()
        mock_tree.find_item = Mock(return_value=mock_item)
        self.item.tree = mock_tree
        self.item.link('mock_uid')
        self.item.cleared = 1  # updates each stamp
        self.assertTrue(self.item.cleared)
        self.item.cleared = 0  # sets each stamp to None
        self.assertFalse(self.item.cleared)

    def test_reviwed(self):
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
        value = ("A sentence. Another sentence! Hello? Hi.\n"
                 "A new line (here). And another sentence.")
        text = ("A sentence. Another sentence! Hello? Hi.\n"
                "A new line (here). And another sentence.")
        yaml = ("text: |\n"
                "  A sentence. Another sentence! Hello? Hi.\n"
                "  A new line (here). And another sentence.\n")
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
        self.assertEqual("abc123", self.item.ref)

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

    @patch('doorstop.core.editor.launch')
    def test_edit(self, mock_launch):
        """Verify an item can be edited."""
        self.item.tree = Mock()
        # Act
        self.item.edit(tool='mock_editor')
        # Assert
        self.item.tree.vcs.lock.assert_called_once_with(self.item.path)
        self.item.tree.vcs.edit.assert_called_once_with(self.item.path)
        mock_launch.assert_called_once_with(self.item.path, tool='mock_editor')

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
        item = MockItem(path)
        self.item.link(item)
        self.assertEqual(['ABC123'], self.item.links)

    def test_unlink_by_item(self):
        """Verify links can be removed (by item)."""
        path = os.path.join('path', 'to', 'ABC123.yml')
        item = MockItem(path)
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

    def test_parent_documents_no_document(self):
        """Verify 'parent_documents' is only valid with a document."""
        self.item.tree = Mock()
        self.assertIs(None, self.item.parent_documents)

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
        self.assertRaises(DoorstopError, MockItem, "path/to/REQ.yaml")
        self.assertRaises(DoorstopError, MockItem, "path/to/001.yaml")

    def test_invalid_file_ext(self):
        """Verify an invalid file extension cannot be a requirement."""
        self.assertRaises(DoorstopError, MockItem, "path/to/REQ001")
        self.assertRaises(DoorstopError, MockItem, "path/to/REQ001.txt")

    @patch('doorstop.core.item.Item', MockItem)
    def test_new(self):
        """Verify items can be created."""
        MockItem._create.reset_mock()
        item = MockItem.new(None, None,
                            EMPTY, FILES, 'TEST00042',
                            level=(1, 2, 3))
        path = os.path.join(EMPTY, 'TEST00042.yml')
        self.assertEqual(path, item.path)
        self.assertEqual((1, 2, 3), item.level)
        MockItem._create.assert_called_once_with(path, name='item')

    @patch('doorstop.core.item.Item', MockItem)
    def test_new_cache(self):
        """Verify new items are cached."""
        mock_tree = Mock()
        mock_tree._item_cache = {}
        item = MockItem.new(mock_tree, None,
                            EMPTY, FILES, 'TEST00042',
                            level=(1, 2, 3))
        self.assertEqual(item, mock_tree._item_cache[item.uid])
        mock_tree.vcs.add.assert_called_once_with(item.path)

    @patch('doorstop.core.item.Item', MockItem)
    def test_new_special(self):
        """Verify items can be created with a specially named prefix."""
        MockItem._create.reset_mock()
        item = MockItem.new(None, None,
                            EMPTY, FILES, 'VSM.HLR_01-002-042',
                            level=(1, 0))
        path = os.path.join(EMPTY, 'VSM.HLR_01-002-042.yml')
        self.assertEqual(path, item.path)
        self.assertEqual((1,), item.level)
        MockItem._create.assert_called_once_with(path, name='item')

    def test_new_existing(self):
        """Verify an exception is raised if the item already exists."""
        self.assertRaises(DoorstopError, Item.new,
                          None, None,
                          FILES, FILES, 'REQ002',
                          level=(1, 2, 3))

    def test_validate_invalid_ref(self):
        """Verify an invalid reference fails validity."""
        with patch('doorstop.core.item.Item.find_ref',
                   Mock(side_effect=DoorstopError)):
            self.assertFalse(self.item.validate())

    def test_validate_inactive(self):
        """Verify an inactive item is not checked."""
        self.item.active = False
        with patch('doorstop.core.item.Item.find_ref',
                   Mock(side_effect=DoorstopError)):
            self.assertTrue(self.item.validate())

    def test_validate_reviewed(self):
        """Verify that checking a reviewed item updates the stamp."""
        self.item._data['reviewed'] = True
        self.assertTrue(self.item.validate())
        stamp = 'c6a87755b8756b61731c704c6a7be4a2'
        self.assertEqual(stamp, self.item._data['reviewed'])

    @patch('doorstop.settings.REVIEW_NEW_ITEMS', False)
    def test_validate_reviewed_first(self):
        """Verify that a missing initial review leaves the stamp empty."""
        self.item._data['reviewed'] = Stamp(None)
        self.assertTrue(self.item.validate())
        self.assertEqual(Stamp(None), self.item._data['reviewed'])

    @patch('doorstop.settings.ERROR_ALL', True)
    def test_validate_reviewed_second(self):
        """Verify that a modified stamp fails review."""
        self.item._data['reviewed'] = Stamp('abc123')
        self.assertFalse(self.item.validate())

    def test_validate_cleared(self):
        """Verify that checking a cleared link updates the stamp."""
        mock_item = Mock()
        mock_item.stamp = Mock(return_value=Stamp('abc123'))
        mock_tree = MagicMock()
        mock_tree.find_item = Mock(return_value=mock_item)
        self.item.tree = mock_tree
        self.item.links = [{'mock_uid': True}]
        self.assertTrue(self.item.validate())
        self.assertEqual('abc123', self.item.links[0].stamp)

    def test_validate_cleared_new(self):
        """Verify that new links are stamped automatically."""
        mock_item = Mock()
        mock_item.stamp = Mock(return_value=Stamp('abc123'))
        mock_tree = MagicMock()
        mock_tree.find_item = Mock(return_value=mock_item)
        self.item.tree = mock_tree
        self.item.links = [{'mock_uid': None}]
        self.assertTrue(self.item.validate())
        self.assertEqual('abc123', self.item.links[0].stamp)

    def test_validate_nonnormative_with_links(self):
        """Verify a non-normative item with links can be checked."""
        self.item.normative = False
        self.item.links = ['a']
        self.assertTrue(self.item.validate())

    @patch('doorstop.settings.STAMP_NEW_LINKS', False)
    def test_validate_link_to_inactive(self):
        """Verify a link to an inactive item can be checked."""
        mock_item = Mock()
        mock_item.active = False
        mock_tree = MagicMock()
        mock_tree.find_item = Mock(return_value=mock_item)
        self.item.links = ['a']
        self.item.tree = mock_tree
        self.assertTrue(self.item.validate())

    @patch('doorstop.settings.STAMP_NEW_LINKS', False)
    def test_validate_link_to_nonnormative(self):
        """Verify a link to an non-normative item can be checked."""
        mock_item = Mock()
        mock_item.normative = False
        mock_tree = MagicMock()
        mock_tree.find_item = Mock(return_value=mock_item)
        self.item.links = ['a']
        self.item.tree = mock_tree
        self.assertTrue(self.item.validate())

    def test_validate_document(self):
        """Verify an item can be checked against a document."""
        mock_document = Mock()
        mock_document.parent = 'fake'
        self.item.document = mock_document
        self.assertTrue(self.item.validate())

    def test_validate_document_with_links(self):
        """Verify an item can be checked against a document with links."""
        self.item.link('unknown1')
        mock_document = Mock()
        mock_document.parent = 'fake'
        self.item.document = mock_document
        self.assertTrue(self.item.validate())

    def test_validate_document_with_bad_link_uids(self):
        """Verify an item can be checked against a document w/ bad links."""
        self.item.link('invalid')
        mock_document = Mock()
        mock_document.parent = 'fake'
        self.item.document = mock_document
        self.assertFalse(self.item.validate())

    @patch('doorstop.settings.STAMP_NEW_LINKS', False)
    def test_validate_tree(self):
        """Verify an item can be checked against a tree."""

        def mock_iter(self):  # pylint: disable=W0613
            """Mock Tree.__iter__ to yield a mock Document."""
            mock_document = Mock()
            mock_document.parent = 'RQ'

            def mock_iter2(self):  # pylint: disable=W0613
                """Mock Document.__iter__ to yield a mock Item."""
                mock_item = Mock()
                mock_item.uid = 'TST001'
                mock_item.links = ['RQ001']
                yield mock_item

            mock_document.__iter__ = mock_iter2
            yield mock_document

        self.item.link('fake1')

        mock_tree = Mock()
        mock_tree.__iter__ = mock_iter
        mock_tree.find_item = lambda uid: Mock(uid='fake1')

        self.item.tree = mock_tree

        self.assertTrue(self.item.validate())

    def test_validate_tree_error(self):
        """Verify an item can be checked against a tree with errors."""
        self.item.link('fake1')
        mock_tree = MagicMock()
        mock_tree.find_item = Mock(side_effect=DoorstopError)
        self.item.tree = mock_tree
        self.assertFalse(self.item.validate())

    @patch('doorstop.settings.REVIEW_NEW_ITEMS', False)
    def test_validate_both(self):
        """Verify an item can be checked against both."""

        def mock_iter(seq):
            """Creates a mock __iter__ method."""

            def _iter(self):  # pylint: disable=W0613
                """Mock __iter__method."""
                yield from seq
            return _iter

        mock_item = Mock()
        mock_item.links = [self.item.uid]

        mock_document = Mock()
        mock_document.parent = 'BOTH'
        mock_document.prefix = 'BOTH'

        mock_document.__iter__ = mock_iter([mock_item])
        mock_tree = Mock()
        mock_tree.__iter__ = mock_iter([mock_document])

        self.item.document = mock_document
        self.item.tree = mock_tree

        self.assertTrue(self.item.validate())

    @patch('doorstop.settings.STAMP_NEW_LINKS', False)
    @patch('doorstop.settings.REVIEW_NEW_ITEMS', False)
    def test_validate_both_no_reverse_links(self):
        """Verify an item can be checked against both (no reverse links)."""

        def mock_iter(self):  # pylint: disable=W0613
            """Mock Tree.__iter__ to yield a mock Document."""
            mock_document = Mock()
            mock_document.parent = 'RQ'

            def mock_iter2(self):  # pylint: disable=W0613
                """Mock Document.__iter__ to yield a mock Item."""
                mock_item = Mock()
                mock_item.uid = 'TST001'
                mock_item.links = []
                yield mock_item

            mock_document.__iter__ = mock_iter2
            yield mock_document

        self.item.link('fake1')

        mock_document = Mock()
        mock_document.prefix = 'RQ'

        mock_tree = Mock()
        mock_tree.__iter__ = mock_iter
        mock_tree.find_item = lambda uid: Mock(uid='fake1')

        self.item.document = mock_document
        self.item.tree = mock_tree

        self.assertTrue(self.item.validate())

    @patch('doorstop.core.item.Item.get_issues', Mock(return_value=[]))
    def test_issues(self):
        """Verify an item's issues convenience property can be accessed."""
        self.assertEqual(0, len(self.item.issues))

    def test_stamp(self):
        """Verify an item's contents can be stamped."""
        stamp = 'c6a87755b8756b61731c704c6a7be4a2'
        self.assertEqual(stamp, self.item.stamp())

    def test_stamp_links(self):
        """Verify an item's contents can be stamped."""
        self.item.link('mock_link')
        stamp = '1020719292bbdc4090bd236cf41cd104'
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
        item = Item(self.ITEM)
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

    def test_relpath(self):
        """Verify an item's relative path string can be read but not set."""
        text = "@{}{}".format(os.sep, '???')
        self.assertEqual(text, self.item.relpath)
        self.assertRaises(AttributeError, setattr, self.item, 'relpath', '.')

    def test_prefix(self):
        """Verify an item's prefix can be read but not set."""
        self.assertEqual('RQ', self.item.prefix)
        self.assertRaises(AttributeError, setattr, self.item, 'prefix', 'REQ')

    def test_number(self):
        """Verify an item's number can be read but not set."""
        self.assertEqual(1, self.item.number)
        self.assertRaises(AttributeError, setattr, self.item, 'number', 2)

    @patch('doorstop.core.item.log.debug')
    def test_attributes(self, mock_warning):
        """Verify all other `Item` attributes raise an exception."""
        self.assertRaises(AttributeError, getattr, self.item, 'path')
        self.assertRaises(AttributeError, getattr, self.item, 'text')
        self.assertRaises(AttributeError, getattr, self.item, 'get_issues')
        self.assertRaises(AttributeError, getattr, self.item, 'delete')
        self.assertRaises(AttributeError, getattr, self.item, 'not_on_item')
        self.assertEqual(3, mock_warning.call_count)

    @patch('doorstop.core.item.log.debug')
    def test_attributes_with_spec(self, mock_warning):
        """Verify all other `Item` attributes raise an exception."""
        spec = Item(os.path.join(FILES, 'REQ001.yml'))
        self.item = UnknownItem(self.item.uid, spec=spec)
        self.assertRaises(AttributeError, getattr, self.item, 'path')
        self.assertRaises(AttributeError, getattr, self.item, 'text')
        self.assertRaises(AttributeError, getattr, self.item, 'get_issues')
        self.assertRaises(AttributeError, getattr, self.item, 'delete')
        self.assertRaises(AttributeError, getattr, self.item, 'not_on_item')
        self.assertEqual(4, mock_warning.call_count)

    def test_stamp(self):
        """Verify an unknown item has no stamp."""
        self.assertEqual(Stamp(None), self.item.stamp())
