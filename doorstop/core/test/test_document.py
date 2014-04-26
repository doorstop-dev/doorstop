"""Unit tests for the doorstop.core.document module."""

import unittest
from unittest.mock import patch, Mock, MagicMock

import os
import logging

from doorstop.core.document import Document
from doorstop import common
from doorstop.common import DoorstopError, DoorstopWarning, DoorstopInfo

from doorstop.core.test import ROOT, FILES, EMPTY, NEW, MockFileObject
from doorstop.core.test.test_item import MockItem

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


class MockDocument(MockFileObject, Document):  # pylint: disable=W0223,R0902,R0904

    """Mock Document class with stubbed file IO."""


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

    def test_str(self):
        """Verify documents can be converted to strings."""
        common.VERBOSITY = 2
        self.assertEqual("REQ", str(self.document))

    def test_str_verbose(self):
        """Verify documents can be converted to strings in verbose mode."""
        common.VERBOSITY = 3
        relpath = os.path.relpath(self.document.path, self.document.root)
        text = "REQ (@{}{})".format(os.sep, relpath)
        self.assertEqual(text, str(self.document))

    def test_ne(self):
        """Verify document non-equality is correct."""
        self.assertNotEqual(self.document, None)

    def test_items(self):
        """Verify the items in a document can be accessed."""
        items = self.document.items
        logging.debug("items: {}".format(items))
        self.assertEqual(5, len(items))

    @patch('doorstop.core.document.Document', MockDocument)
    def test_new(self):
        """Verify a new document can be created with defaults."""
        MockDocument._new.reset_mock()
        path = os.path.join(EMPTY, '.doorstop.yml')
        document = MockDocument.new(EMPTY, root=FILES, prefix='NEW', digits=2)
        self.assertEqual('NEW', document.prefix)
        self.assertEqual(2, document.digits)
        MockDocument._new.assert_called_once_with(path, name='document')

    def test_new_existing(self):
        """Verify an exception is raised if the document already exists."""
        self.assertRaises(DoorstopError, Document.new, FILES, ROOT, 'DUPL')

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

    @patch('doorstop.core.item.Item.new')
    def test_add_item(self, mock_new):
        """Verify an item can be added to a document."""
        self.document.add_item()
        mock_new.assert_called_once_with(FILES, ROOT, 'REQ005', level=(2, 2))

    @patch('doorstop.core.item.Item.new')
    def test_add_empty(self, mock_new):
        """Verify an item can be added to an new document."""
        document = MockDocument(NEW, ROOT)
        document.prefix = 'NEW'
        self.assertIsNot(None, document.add_item())
        mock_new.assert_called_once_with(NEW, ROOT, 'NEW001', level=None)

    def test_add_contains(self):
        """Verify an added item is contained in the document."""
        item = self.document.items[0]
        self.assertIn(item, self.document)
        item2 = self.document.add_item()
        self.assertIn(item2, self.document)

    @patch('os.remove')
    def test_remove_item_contains(self, mock_remove):
        """Verify a removed item is not contained in the document."""
        item = self.document.items[0]
        self.assertIn(item, self.document)
        removed_item = self.document.remove_item(item.id)
        self.assertEqual(item, removed_item)
        self.assertNotIn(item, self.document)
        mock_remove.assert_called_once_with(item.path)

    @patch('os.remove')
    def test_remove_item_by_item(self, mock_remove):
        """Verify an item can be removed (by item)."""
        item = self.document.items[0]
        self.assertIn(item, self.document)
        removed_item = self.document.remove_item(item)
        self.assertEqual(item, removed_item)

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
    def test_validate(self, mock_get_issues):
        """Verify a document can be validated."""
        mock_get_issues.return_value = [DoorstopInfo('i')]
        self.assertTrue(self.document.validate())
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
    @patch('os.remove')
    def test_delete(self, mock_remove, mock_delete):
        """Verify a document can be deleted."""
        self.document.delete()
        mock_remove.assert_called_once_with(self.document.config)
        self.assertEqual(5, mock_delete.call_count)
        self.document.delete()  # ensure a second delete is ignored

    @patch('doorstop.core.document.Document.get_issues', Mock(return_value=[]))
    def test_issues(self):
        """Verify an document's issues convenience property can be accessed."""
        self.assertEqual(0, len(self.document.issues))

    def test_issues_duplicate_level(self):
        """Verify duplicate item levels are detected."""
        mock_item1 = Mock()
        mock_item1.id = 'HLT001'
        mock_item1.level = (4, 2)
        mock_item2 = Mock()
        mock_item2.id = 'HLT002'
        mock_item2.level = (4, 2)
        mock_items = [mock_item1, mock_item2]
        expected = DoorstopWarning("duplicate level: 4.2 (HLT001, HLT002)")
        issue = list(self.document._get_issues_level(mock_items))[0]
        self.assertIsInstance(issue, type(expected))
        self.assertEqual(expected.args, issue.args)

    def test_issues_skipped_level_over(self):
        """Verify skipped (over) item levels are detected."""
        mock_item1 = Mock()
        mock_item1.id = 'HLT001'
        mock_item1.level = (1, 1)
        mock_item2 = Mock()
        mock_item2.id = 'HLT002'
        mock_item2.level = (1, 3)
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
        mock_item1.level = (1, 1)
        mock_item2 = Mock()
        mock_item2.id = 'HLT002'
        mock_item2.level = (3, 0)
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
        mock_item1.level = (1, 1)
        mock_item2 = Mock()
        mock_item2.id = 'HLT002'
        mock_item2.level = (2, 2)
        mock_items = [mock_item1, mock_item2]
        expected = DoorstopWarning("skipped level: 1.1 (HLT001), 2.2 (HLT002)")
        issues = list(self.document._get_issues_level(mock_items))
        self.assertEqual(1, len(issues))
        self.assertIsInstance(issues[0], type(expected))
        self.assertEqual(expected.args, issues[0].args)


class TestModule(unittest.TestCase):  # pylint: disable=R0904

    """Unit tests for the doorstop.core.document module."""  # pylint: disable=C0103

    pass
