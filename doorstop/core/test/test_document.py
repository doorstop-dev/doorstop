"""Unit tests for the doorstop.core.document module."""

import unittest
from unittest.mock import patch, Mock, MagicMock

import os
import logging

from doorstop.common import DoorstopError, DoorstopWarning, DoorstopInfo
from doorstop.core.types import Level
from doorstop.core.document import Document

from doorstop.core.test import ROOT, FILES, EMPTY, NEW
from doorstop.core.test import MockItem, MockDocument

YAML_DEFAULT = """
settings:
  digits: 3
  prefix: REQ
  sep: ''
""".lstrip()

YAML_CUSTOM = """
settings:
  digits: 4
  prefix: CUSTOM
  sep: '-'
""".lstrip()

YAML_CUSTOM_PARENT = """
settings:
  digits: 4
  parent: PARENT
  prefix: CUSTOM
  sep: '-'
""".lstrip()


@patch('doorstop.settings.REORDER', False)  # pylint: disable=R0904
@patch('doorstop.core.item.Item', MockItem)  # pylint: disable=R0904
class TestDocument(unittest.TestCase):  # pylint: disable=R0904

    """Unit tests for the Document class."""  # pylint: disable=C0103,W0212

    def setUp(self):
        self.document = MockDocument(FILES, root=ROOT)

    def test_init_invalid(self):
        """Verify a document cannot be initialized from an invalid path."""
        self.assertRaises(DoorstopError, Document, 'not/a/path')

    def test_load_empty(self):
        """Verify loading calls read."""
        self.document.load()
        self.document._read.assert_called_once_with(self.document.config)

    def test_load_error(self):
        """Verify an exception is raised with invalid YAML."""
        self.document._file = "invalid: -"
        self.assertRaises(DoorstopError, self.document.load)

    def test_load_unexpected(self):
        """Verify an exception is raised for unexpected file contents."""
        self.document._file = "unexpected"
        self.assertRaises(DoorstopError, self.document.load)

    def test_load(self):
        """Verify the document config can be loaded from file."""
        self.document._file = YAML_CUSTOM
        self.document.load(reload=True)
        self.assertEqual('CUSTOM', self.document.prefix)
        self.assertEqual('-', self.document.sep)
        self.assertEqual(4, self.document.digits)

    def test_load_parent(self):
        """Verify the document config can be loaded from file with a parent."""
        self.document._file = YAML_CUSTOM_PARENT
        self.document.load()
        self.assertEqual('PARENT', self.document.parent)

    def test_save_empty(self):
        """Verify saving calls write."""
        self.document.save()
        self.document._write.assert_called_once_with(YAML_DEFAULT,
                                                     self.document.config)

    def test_save_parent(self):
        """Verify a document can be saved with a parent."""
        self.document.parent = 'SYS'
        self.document.save()
        self.assertIn("parent: SYS", self.document._file)

    def test_save_custom(self):
        """Verify a document can be saved with a custom attribute."""
        self.document._data['custom'] = 'this'
        self.document.save()
        self.assertIn("custom: this", self.document._file)

    @patch('doorstop.common.VERBOSITY', 2)
    def test_str(self):
        """Verify a document can be converted to a string."""
        self.assertEqual("REQ", str(self.document))

    @patch('doorstop.common.VERBOSITY', 3)
    def test_str_verbose(self):
        """Verify a document can be converted to a string (verbose)."""
        relpath = os.path.relpath(self.document.path, self.document.root)
        text = "REQ (@{}{})".format(os.sep, relpath)
        self.assertEqual(text, str(self.document))

    def test_ne(self):
        """Verify document non-equality is correct."""
        self.assertNotEqual(self.document, None)

    def test_hash(self):
        """Verify documents can be hashed."""
        document1 = MockDocument('path/to/fake1')
        document2 = MockDocument('path/to/fake2')
        document3 = MockDocument('path/to/fake2')
        my_set = set()
        # Act
        my_set.add(document1)
        my_set.add(document2)
        my_set.add(document3)
        # Assert
        self.assertEqual(2, len(my_set))

    def test_len(self):
        """Verify a document has a length."""
        self.assertEqual(5, len(self.document))

    def test_items(self):
        """Verify the items in a document can be accessed."""
        items = self.document.items
        self.assertEqual(5, len(items))
        for item in self.document:
            logging.debug("item: {}".format(item))
            self.assertIs(self.document, item.document)
            self.assertIs(self.document.tree, item.tree)

    @patch('doorstop.core.document.Document', MockDocument)
    def test_new(self):
        """Verify a new document can be created with defaults."""
        MockDocument._new.reset_mock()
        path = os.path.join(EMPTY, '.doorstop.yml')
        document = MockDocument.new(None,
                                    EMPTY, root=FILES, prefix='NEW', digits=2)
        self.assertEqual('NEW', document.prefix)
        self.assertEqual(2, document.digits)
        MockDocument._new.assert_called_once_with(path, name='document')

    def test_new_existing(self):
        """Verify an exception is raised if the document already exists."""
        self.assertRaises(DoorstopError, Document.new,
                          None,
                          FILES, ROOT,
                          prefix='DUPL')

    def test_invalid(self):
        """Verify an exception is raised on an invalid document."""
        self.assertRaises(DoorstopError, Document, EMPTY)

    def test_relpath(self):
        """Verify the document's relative path string can be determined."""
        relpath = os.path.relpath(self.document.path, self.document.root)
        text = "@{}{}".format(os.sep, relpath)
        self.assertEqual(text, self.document.relpath)

    def test_sep(self):
        """Verify an documents's separator can be set and read."""
        self.document.sep = '_'
        self.assertIn("sep: _\n", self.document._write.call_args[0][0])
        self.assertEqual('_', self.document.sep)

    def test_sep_invalid(self):
        """Verify an invalid separator is rejected."""
        self.assertRaises(AssertionError, setattr, self.document, 'sep', '?')

    def test_digits(self):
        """Verify an documents's digits can be set and read."""
        self.document.digits = 42
        self.assertIn("digits: 42\n", self.document._write.call_args[0][0])
        self.assertEqual(42, self.document.digits)

    def test_depth(self):
        """Verify the maximum item level depth can be determined."""
        self.assertEqual(3, self.document.depth)

    def test_next(self):
        """Verify the next item number can be determined."""
        self.assertEqual(5, self.document.next)

    def test_object_references(self):
        """Verify a standalone document does not have object references."""
        self.assertIs(None, self.document.tree)

    @patch('doorstop.core.document.Document._reorder')
    @patch('doorstop.core.item.Item.new')
    def test_add_item(self, mock_new, mock_reorder):
        """Verify an item can be added to a document."""
        with patch('doorstop.settings.REORDER', True):
            self.document.add_item()
        mock_new.assert_called_once_with(None, self.document,
                                         FILES, ROOT, 'REQ005',
                                         level=Level('2.2'))
        self.assertEqual(0, mock_reorder.call_count)

    @patch('doorstop.core.document.Document.reorder')
    @patch('doorstop.core.item.Item.new')
    def test_add_item_with_level(self, mock_new, mock_reorder):
        """Verify an item can be added to a document with a level."""
        with patch('doorstop.settings.REORDER', True):
            item = self.document.add_item(level='4.2')
        mock_new.assert_called_once_with(None, self.document,
                                         FILES, ROOT, 'REQ005',
                                         level='4.2')
        mock_reorder.assert_called_once_with(keep=item)

    @patch('doorstop.core.item.Item.new')
    def test_add_item_with_number(self, mock_new):
        """Verify an item can be added to a document with a number."""
        self.document.add_item(number=999)
        mock_new.assert_called_once_with(None, self.document,
                                         FILES, ROOT, 'REQ999',
                                         level=Level('2.2'))

    @patch('doorstop.core.item.Item.new')
    def test_add_empty(self, mock_new):
        """Verify an item can be added to an new document."""
        document = MockDocument(NEW, ROOT)
        document.prefix = 'NEW'
        self.assertIsNot(None, document.add_item(reorder=False))
        mock_new.assert_called_once_with(None, document,
                                         NEW, ROOT, 'NEW001',
                                         level=None)

    def test_add_contains(self):
        """Verify an added item is contained in the document."""
        item = self.document.items[0]
        self.assertIn(item, self.document)
        item2 = self.document.add_item(reorder=False)
        self.assertIn(item2, self.document)

    @patch('doorstop.core.document.Document._reorder')
    @patch('os.remove')
    def test_remove(self, mock_remove, mock_reorder):
        """Verify an item can be removed."""
        with patch('doorstop.settings.REORDER', True):
            item = self.document.remove_item('REQ001')
        mock_reorder.assert_called_once_with(self.document.items,
                                             keep=None, start=None)
        mock_remove.assert_called_once_with(item.path)

    @patch('os.remove')
    def test_remove_item_contains(self, mock_remove):
        """Verify a removed item is not contained in the document."""
        item = self.document.items[0]
        self.assertIn(item, self.document)
        removed_item = self.document.remove_item(item.id, reorder=False)
        self.assertEqual(item, removed_item)
        self.assertNotIn(item, self.document)
        mock_remove.assert_called_once_with(item.path)

    @patch('os.remove')
    def test_remove_item_by_item(self, mock_remove):
        """Verify an item can be removed (by item)."""
        item = self.document.items[0]
        self.assertIn(item, self.document)
        removed_item = self.document.remove_item(item, reorder=False)
        self.assertEqual(item, removed_item)
        mock_remove.assert_called_once_with(item.path)

    def test_reorder(self):
        """Verify items can be reordered."""
        mock_items = [Mock(level=Level('2.3')),
                      Mock(level=Level('2.3')),
                      Mock(level=Level('2.7')),
                      Mock(level=Level('3.2.2')),
                      Mock(level=Level('3.4.2')),
                      Mock(level=Level('3.5.0')),
                      Mock(level=Level('3.5.0')),
                      Mock(level=Level('3.6')),
                      Mock(level=Level('5.0')),
                      Mock(level=Level('5.9'))]
        expected = [Level('2.3'),
                    Level('2.4'),
                    Level('2.5'),
                    Level('3.1.1'),
                    Level('3.2.1'),
                    Level('3.3.0'),
                    Level('3.4.0'),
                    Level('3.5'),
                    Level('4.0'),
                    Level('4.1')]
        Document._reorder(mock_items)
        actual = [item.level for item in mock_items]
        self.assertListEqual(expected, actual)

    def test_reorder_no_change(self):
        """Verify already ordered items can be reordered."""
        mock_items = [Mock(level=Level('1.1')),
                      Mock(level=Level('1.1.1.1')),
                      Mock(level=Level('2')),
                      Mock(level=Level('3')),
                      Mock(level=Level('4.1.1'))]
        expected = [Level('1.1'),
                    Level('1.1.1.1'),
                    Level('2'),
                    Level('3'),
                    Level('4.1.1')]
        Document._reorder(mock_items)
        actual = [item.level for item in mock_items]
        self.assertListEqual(expected, actual)

    def test_reorder_with_start(self):
        """Verify items can be reordered with a given start."""
        mock_item = Mock(level=Level('2.3'))
        mock_items = [Mock(level=Level('2.2')),
                      mock_item,
                      Mock(level=Level('2.3')),
                      Mock(level=Level('2.7')),
                      Mock(level=Level('3.2.2')),
                      Mock(level=Level('3.4.2')),
                      Mock(level=Level('3.5.0')),
                      Mock(level=Level('3.5.0')),
                      Mock(level=Level('3.6')),
                      Mock(level=Level('5.0')),
                      Mock(level=Level('5.9'))]
        expected = [Level('1.2'),
                    Level('1.3'),
                    Level('1.4'),
                    Level('1.5'),
                    Level('2.1.1'),
                    Level('2.2.1'),
                    Level('2.3.0'),
                    Level('2.4.0'),
                    Level('2.5'),
                    Level('3.0'),
                    Level('3.1')]
        Document._reorder(mock_items, start=(1, 2), keep=mock_item)
        actual = [item.level for item in mock_items]
        self.assertListEqual(expected, actual)

    def test_find_item(self):
        """Verify an item can be found by ID."""
        item = self.document.find_item('req2')
        self.assertIsNot(None, item)

    def test_find_item_exact(self):
        """Verify an item can be found by its exact ID."""
        item = self.document.find_item('req2-001')
        self.assertIsNot(None, item)

    def test_find_item_unknown_number(self):
        """Verify an exception is raised on an unknown number."""
        self.assertRaises(DoorstopError, self.document.find_item, 'req99')

    def test_find_item_unknown_ID(self):
        """Verify an exception is raised on an unknown ID."""
        self.assertRaises(DoorstopError, self.document.find_item, 'unknown99')

    @patch('doorstop.core.item.Item.get_issues')
    @patch('doorstop.core.document.Document.reorder')
    def test_validate(self, mock_reorder, mock_get_issues):
        """Verify a document can be validated."""
        mock_get_issues.return_value = [DoorstopInfo('i')]
        with patch('doorstop.settings.REORDER', True):
            self.assertTrue(self.document.validate())
        mock_reorder.assert_called_once_with(items=self.document.items)
        self.assertEqual(5, mock_get_issues.call_count)

    @patch('doorstop.core.item.Item.get_issues',
           Mock(return_value=[DoorstopError('error'),
                              DoorstopWarning('warning'),
                              DoorstopInfo('info')]))
    def test_validate_item(self):
        """Verify an item error fails the document check."""
        self.assertFalse(self.document.validate())

    @patch('doorstop.core.item.Item.get_issues', Mock(return_value=[]))
    def test_validate_hook(self):
        """Verify an item hook can be called."""
        mock_hook = MagicMock()
        self.document.validate(item_hook=mock_hook)
        self.assertEqual(5, mock_hook.call_count)

    @patch('doorstop.core.item.Item.delete')
    @patch('doorstop.common.delete')
    def test_delete(self, mock_common_delete, mock_item_delete):
        """Verify a document can be deleted."""
        self.document.delete()
        self.assertEqual(2, mock_common_delete.call_count)
        self.assertEqual(5, mock_item_delete.call_count)
        self.document.delete()  # ensure a second delete is ignored

    @patch('doorstop.core.document.Document.get_issues', Mock(return_value=[]))
    def test_issues(self):
        """Verify an document's issues convenience property can be accessed."""
        self.assertEqual(0, len(self.document.issues))

    def test_issues_duplicate_level(self):
        """Verify duplicate item levels are detected."""
        mock_item1 = Mock()
        mock_item1.id = 'HLT001'
        mock_item1.level = Level('4.2')
        mock_item2 = Mock()
        mock_item2.id = 'HLT002'
        mock_item2.level = Level('4.2')
        mock_items = [mock_item1, mock_item2]
        expected = DoorstopWarning("duplicate level: 4.2 (HLT001, HLT002)")
        issue = list(self.document._get_issues_level(mock_items))[0]
        self.assertIsInstance(issue, type(expected))
        self.assertEqual(expected.args, issue.args)

    def test_issues_skipped_level_over(self):
        """Verify skipped (over) item levels are detected."""
        mock_item1 = Mock()
        mock_item1.id = 'HLT001'
        mock_item1.level = Level('1.1')
        mock_item2 = Mock()
        mock_item2.id = 'HLT002'
        mock_item2.level = Level('1.3')
        mock_items = [mock_item1, mock_item2]
        expected = DoorstopWarning("skipped level: 1.1 (HLT001), 1.3 (HLT002)")
        issues = list(self.document._get_issues_level(mock_items))
        self.assertEqual(1, len(issues))
        self.assertIsInstance(issues[0], type(expected))
        self.assertEqual(expected.args, issues[0].args)

    def test_issues_skipped_level_out(self):
        """Verify skipped (out) item levels are detected."""
        mock_item1 = Mock()
        mock_item1.id = 'HLT001'
        mock_item1.level = Level('1.1')
        mock_item2 = Mock()
        mock_item2.id = 'HLT002'
        mock_item2.level = Level('3.0')
        mock_items = [mock_item1, mock_item2]
        expected = DoorstopWarning("skipped level: 1.1 (HLT001), 3.0 (HLT002)")
        issues = list(self.document._get_issues_level(mock_items))
        self.assertEqual(1, len(issues))
        self.assertIsInstance(issues[0], type(expected))
        self.assertEqual(expected.args, issues[0].args)

    def test_issues_skipped_level_out_over(self):
        """Verify skipped (out and over) item levels are detected."""
        mock_item1 = Mock()
        mock_item1.id = 'HLT001'
        mock_item1.level = Level('1.1')
        mock_item2 = Mock()
        mock_item2.id = 'HLT002'
        mock_item2.level = Level('2.2')
        mock_items = [mock_item1, mock_item2]
        expected = DoorstopWarning("skipped level: 1.1 (HLT001), 2.2 (HLT002)")
        issues = list(self.document._get_issues_level(mock_items))
        self.assertEqual(1, len(issues))
        self.assertIsInstance(issues[0], type(expected))
        self.assertEqual(expected.args, issues[0].args)


class TestModule(unittest.TestCase):  # pylint: disable=R0904

    """Unit tests for the doorstop.core.document module."""  # pylint: disable=C0103

    pass
