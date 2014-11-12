# -*- coding: utf-8 -*-

"""Unit tests for the doorstop.core.importer module."""

import unittest
from unittest.mock import patch, Mock, MagicMock

import os
import logging

from doorstop.common import DoorstopError
from doorstop.core.tree import Tree
from doorstop.core import importer
from doorstop.core.builder import _set_tree

from doorstop.core.test.test_document import FILES, MockItem

LOREM_IPSUM = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed \
do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad \
minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex \
ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate \
velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat \
cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id \
est laborum."


class TestModule(unittest.TestCase):

    """Unit tests for the doorstop.core.importer module."""  # pylint: disable=R0201

    maxDiff = None

    def test_import_file_unknown(self):
        """Verify an exception is raised when importing unknown formats."""
        mock_document = Mock()
        self.assertRaises(DoorstopError,
                          importer.import_file, 'a.a', mock_document)
        self.assertRaises(DoorstopError,
                          importer.import_file, 'a.csv', mock_document, '.a')

    @patch('doorstop.core.importer._file_csv')
    def test_import_file(self, mock_file_csv):
        """Verify an extension is parsed from the import path."""
        mock_path = 'path/to/file.csv'
        mock_document = Mock()
        importer.FORMAT_FILE['.csv'] = mock_file_csv
        importer.import_file(mock_path, mock_document)
        mock_file_csv.assert_called_once_with(mock_path, mock_document,
                                              mapping=None)

    @patch('doorstop.core.importer.check')
    def test_import_file_custom_ext(self, mock_check):
        """Verify a custom extension can be specified for import."""
        mock_path = 'path/to/file.ext'
        mock_document = Mock()
        importer.import_file(mock_path, mock_document, ext='.custom')
        mock_check.assert_called_once_with('.custom')

    @patch('doorstop.core.importer.add_item')
    def test_file_yml(self, mock_add_item):
        """Verify a YAML file can be imported."""
        path = os.path.join(FILES, 'exported.yml')
        mock_document = Mock()
        mock_document.find_item = Mock(side_effect=DoorstopError)
        # Act
        importer._file_yml(path, mock_document)  # pylint: disable=W0212
        # Assert
        self.assertEqual(5, mock_add_item.call_count)

    @patch('doorstop.core.importer.add_item')
    def test_file_yml_duplicates(self, mock_add_item):
        """Verify a YAML file can be imported (over existing items)."""
        path = os.path.join(FILES, 'exported.yml')
        mock_document = Mock()
        # Act
        importer._file_yml(path, mock_document)  # pylint: disable=W0212
        # Assert
        self.assertEqual(5, mock_add_item.call_count)

    def test_file_yml_bad_format(self):
        """Verify YAML file import can handle bad data."""
        path = os.path.join(FILES, 'exported.csv')
        self.assertRaises(DoorstopError, importer._file_yml, path, None)  # pylint: disable=W0212

    @patch('doorstop.core.importer._itemize')
    def test_file_csv(self, mock_itemize):
        """Verify a CSV file can be imported."""  # pylint: disable=C0301
        path = os.path.join(FILES, 'exported.csv')
        mock_document = Mock()
        # Act
        importer._file_csv(path, mock_document)  # pylint: disable=W0212
        # Assert
        args, kwargs = mock_itemize.call_args
        logging.debug("args: {}".format(args))
        logging.debug("kwargs: {}".format(kwargs))
        header, data, document = args
        expected_header = ['uid', 'level', 'text', 'ref', 'links',
                           'active', 'derived', 'normative', 'reviewed']
        self.assertEqual(expected_header, header)
        expected_data = [
            ['REQ001', '1.2.3', LOREM_IPSUM, '', 'SYS001\nSYS002:abc123', True, False, True, ''],
            ['REQ003', '1.4', 'Unicode: -40° ±1%', 'REF''123', 'REQ001', True, False, True, ''],
            ['REQ004', '1.6', 'Hello, world!', '', '', True, False, True, ''],
            ['REQ002', '2.1', 'Hello, world!', '', '', True, False, True, 'b5fbcc355112791bbcd2ea881c7c5f81'],
            ['REQ2-001', '2.1', 'Hello, world!', '', 'REQ001', True, False, True, ''],
        ]
        self.assertEqual(expected_data, data)
        self.assertIs(mock_document, document)

    @patch('doorstop.core.importer._itemize')
    def test_file_csv_modified(self, mock_itemize):
        """Verify a CSV file (with modifications) can be imported."""  # pylint: disable=C0301
        path = os.path.join(FILES, 'exported-modified.csv')
        mock_document = Mock()
        # Act
        importer._file_csv(path, mock_document)  # pylint: disable=W0212
        # Assert
        args, kwargs = mock_itemize.call_args
        logging.debug("args: {}".format(args))
        logging.debug("kwargs: {}".format(kwargs))
        header, data, document = args
        expected_header = ['id', 'level', 'text', 'ref', 'links',
                           'active', 'derived', 'normative', 'additional']
        self.assertEqual(expected_header, header)
        expected_data = [
            ['REQ0555', '1.2.3', 'Hello, world!\n', '', 'SYS001,\nSYS002', True, False, False, ''],
            ['REQ003', '1.4', 'Hello, world!\n', 'REF''123', 'REQ001', False, False, True, 'Some "quoted" text \'here\'.'],
            ['REQ004', '1.6', 'Hello, world!\n', '', '', False, True, True, ''],
            ['REQ002', '2.1', 'Hello, world!\n', '', '', True, False, True, ''],
            ['REQ2-001', '2.1', 'Hello, world!\n', '', 'REQ001', True, False, True, ''],
        ]
        self.assertEqual(expected_data, data)
        self.assertIs(mock_document, document)

    @patch('doorstop.core.importer._file_csv')
    def test_file_tsv(self, mock_file_csv):
        """Verify a TSV file can be imported."""
        mock_path = 'path/to/file.tsv'
        mock_document = Mock()
        # Act
        importer._file_tsv(mock_path, mock_document)  # pylint: disable=W0212
        # Assert
        mock_file_csv.assert_called_once_with(mock_path, mock_document,
                                              delimiter='\t', mapping=None)

    @patch('doorstop.core.importer._itemize')
    def test_file_xlsx(self, mock_itemize):
        """Verify a XLSX file can be imported."""  # pylint: disable=C0301
        path = os.path.join(FILES, 'exported.xlsx')
        mock_document = Mock()
        # Act
        importer._file_xlsx(path, mock_document)  # pylint: disable=W0212
        # Assert
        args, kwargs = mock_itemize.call_args
        logging.debug("args: {}".format(args))
        logging.debug("kwargs: {}".format(kwargs))
        header, data, document = args
        expected_header = ['uid', 'level', 'text', 'ref', 'links',
                           'active', 'derived', 'normative', 'reviewed']
        self.assertEqual(expected_header, header)
        expected_data = [
            ['REQ001', '1.2.3', LOREM_IPSUM, None, 'SYS001\nSYS002:abc123', True, False, True, None],
            ['REQ003', '1.4', 'Unicode: -40° ±1%', 'REF''123', 'REQ001', True, False, True, None],
            ['REQ004', '1.6', 'Hello, world!', None, None, True, False, True, None],
            ['REQ002', '2.1', 'Hello, world!', None, None, True, False, True, 'b5fbcc355112791bbcd2ea881c7c5f81'],
            ['REQ2-001', '2.1', 'Hello, world!', None, 'REQ001', True, False, True, None],
        ]
        self.assertEqual(expected_data, data)
        self.assertIs(mock_document, document)

    @patch('doorstop.core.importer.add_item')
    def test_itemize(self, mock_add_item):
        """Verify item data can be converted to items."""
        header = ['uid', 'text', 'links', 'ext1']
        data = [['req1', 'text1', '', 'val1'],
                ['req2', '', 'sys1,sys2', False]]
        mock_document = Mock()
        mock_document.prefix = 'PREFIX'
        # Act
        importer._itemize(header, data, mock_document)  # pylint: disable=W0212
        # Assert
        self.assertEqual(2, mock_add_item.call_count)
        args, kwargs = mock_add_item.call_args
        self.assertEqual('PREFIX', args[0])
        self.assertEqual('req2', args[1])
        expected_attrs = {'ext1': False,
                          'links': ['sys1', 'sys2'],
                          'text': ''}
        self.assertEqual(expected_attrs, kwargs['attrs'])
        self.assertIs(mock_document, kwargs['document'])

    @patch('doorstop.core.importer.add_item')
    def test_itemize_implicit_active(self, mock_add_item):
        """Verify item data can be converted to items (implicit active)."""
        header = ['uid', 'text', 'links', 'ext1', 'active']
        data = [['req2', '', '', False, '']]
        mock_document = Mock()
        mock_document.prefix = 'PREFIX'
        # Act
        importer._itemize(header, data, mock_document)  # pylint: disable=W0212
        # Assert
        args, kwargs = mock_add_item.call_args
        self.assertEqual('PREFIX', args[0])
        self.assertEqual('req2', args[1])
        expected_attrs = {'active': True,
                          'ext1': False,
                          'links': [],
                          'text': ''}
        self.assertEqual(expected_attrs, kwargs['attrs'])

    @patch('doorstop.core.importer.add_item')
    def test_itemize_explicit_inactive(self, mock_add_item):
        """Verify item data can be converted to items (explicit inactive)."""
        header = ['uid', 'text', 'links', 'ext1', 'active']
        data = [['req2', '', '', False, False]]
        mock_document = Mock()
        mock_document.prefix = 'PREFIX'
        # Act
        importer._itemize(header, data, mock_document)  # pylint: disable=W0212
        # Assert
        args, kwargs = mock_add_item.call_args
        self.assertEqual('PREFIX', args[0])
        self.assertEqual('req2', args[1])
        expected_attrs = {'active': False,
                          'ext1': False,
                          'links': [],
                          'text': ''}
        self.assertEqual(expected_attrs, kwargs['attrs'])

    @patch('doorstop.core.importer.add_item')
    def test_itemize_with_mapping(self, mock_add_item):
        """Verify item data can be converted to items with mapping."""
        header = ['myid', 'text', 'links', 'ext1']
        data = [['req1', 'text1', '', 'val1'],
                ['req2', 'text2', 'sys1,sys2', None]]
        mock_document = Mock()
        mapping = {'MyID': 'uid'}
        # Act
        importer._itemize(header, data, mock_document, mapping=mapping)  # pylint: disable=W0212
        # Assert
        self.assertEqual(2, mock_add_item.call_count)

    @patch('doorstop.core.importer.add_item')
    def test_itemize_replace_existing(self, mock_add_item):
        """Verify item data can replace existing items."""
        header = ['uid', 'text', 'links', 'ext1']
        data = [['req1', 'text1', '', 'val1'],
                ['req2', 'text2', 'sys1,sys2', None]]
        mock_document = Mock()
        mock_document.find_item = Mock(side_effect=DoorstopError)
        # Act
        importer._itemize(header, data, mock_document)  # pylint: disable=W0212
        # Assert
        self.assertEqual(2, mock_add_item.call_count)

    @patch('doorstop.core.importer.add_item')
    def test_itemize_blank_column(self, mock_add_item):
        """Verify item data can include invalid values."""
        header = ['id', 'text', None, 'links', 'ext1']  # test 'id' is accepted
        data = [['req1', 'text1', 'blank', '', 'val1']]
        mock_document = Mock()
        mock_document.prefix = 'prefix'
        importer._itemize(header, data, mock_document)  # pylint: disable=W0212
        expected_attrs = {'links': [], 'ext1': 'val1', 'text': 'text1'}
        mock_add_item.assert_called_once_with(mock_document.prefix, 'req1',
                                              attrs=expected_attrs,
                                              document=mock_document)

    @patch('doorstop.core.importer.add_item')
    def test_itemize_new_rows(self, mock_add_item):
        """Verify items can be added from item data blank UIDs."""
        header = ['uid', 'text', 'links', 'ext1']
        data = [
            ['req1', 'text1', '', 'val1'],
            ['req2', '', 'sys1,sys2', False],
            [None, 'A new item.', '', ''],  # blank UID: None
            ['', 'A new item.', '', ''],  # blank UID: empty
            [' ', 'A new item.', '', ''],  # blank UID: whitespace
            ['', '', '', ''],  # skipped
            ['...', 'Another new item.', '', ''],  # placeholder UID
        ]
        mock_document = Mock()
        mock_document.prefix = 'PREFIX'
        mock_document.next_number = 3
        mock_document.digits = 3
        # Act
        importer._itemize(header, data, mock_document)  # pylint: disable=W0212
        # Assert
        self.assertEqual(6, mock_add_item.call_count)

    @patch('doorstop.core.importer.add_item', Mock(side_effect=DoorstopError))
    def test_itemize_invalid(self):
        """Verify item data can include invalid values."""
        header = ['uid', 'text', 'links', 'ext1']
        data = [['req1', 'text1', '', 'val1'],
                ['invalid']]
        mock_document = Mock()
        importer._itemize(header, data, mock_document)  # pylint: disable=W0212


class TestModuleCreateDocument(unittest.TestCase):

    """Unit tests for the doorstop.core.importer:create_document function."""

    def setUp(self):
        # Create default document options
        self.prefix = 'PREFIX'
        self.root = 'ROOT'
        self.path = os.path.join(self.root, 'DIRECTORY')
        self.parent = 'PARENT_PREFIX'
        # Ensure the tree is reloaded
        mock_document = Mock()
        mock_document.root = self.root
        self.mock_tree = Tree(mock_document)
        _set_tree(self.mock_tree)

    @patch('doorstop.core.tree.Tree.create_document')
    def test_create_document(self, mock_new):
        """Verify a new document can be created for import."""
        importer.create_document(self.prefix, self.path)
        mock_new.assert_called_once_with(self.path, self.prefix, parent=None)

    @patch('doorstop.core.builder._get_tree')
    @patch('doorstop.core.tree.Tree.create_document')
    def test_create_document_explicit_tree(self, mock_new, mock_get_tree):
        """Verify a new document can be created for import (explicit tree)."""
        mock_document = Mock()
        mock_document.root = None
        tree = Tree(document=mock_document)
        importer.create_document(self.prefix, self.path, tree=tree)
        self.assertFalse(mock_get_tree.called)
        mock_new.assert_called_once_with(self.path, self.prefix, parent=None)
        self.assertIn(mock_document, tree)

    @patch('doorstop.core.tree.Tree.create_document')
    def test_create_document_with_parent(self, mock_new):
        """Verify a new document can be created for import with a parent."""
        importer.create_document(self.prefix, self.path, parent=self.parent)
        mock_new.assert_called_once_with(self.path, self.prefix,
                                         parent=self.parent)

    @patch('doorstop.core.tree.Tree.create_document',
           Mock(side_effect=DoorstopError))
    def test_create_document_already_exists(self):
        """Verify non-parent import exceptions are re-raised."""
        self.assertRaises(DoorstopError,
                          importer.create_document, self.prefix, self.path)

    @patch('doorstop.core.tree.Tree.create_document',
           Mock(side_effect=DoorstopError))
    @patch('doorstop.core.document.Document.new')
    def test_create_document_unknown_parent(self, mock_new):
        """Verify documents can be created for import with unknown parents."""
        importer.create_document(self.prefix, self.path, parent=self.parent)
        mock_new.assert_called_once_with(self.mock_tree,
                                         self.path, self.root, self.prefix,
                                         parent=self.parent)


@patch('doorstop.core.item.Item', MockItem)
class TestModuleAddItem(unittest.TestCase):

    """Unit tests for the doorstop.core.importer:add_item function."""

    prefix = 'PREFIX'
    root = 'ROOT'
    path = os.path.join(root, 'DIRECTORY')
    parent = 'PARENT_PREFIX'

    mock_document = Mock()
    mock_document._items = []  # pylint: disable=W0212

    def setUp(self):
        # Create default item attributes
        self.uid = 'PREFIX-00042'
        # Ensure the tree is reloaded
        mock_document = Mock()
        mock_document.root = self.root
        mock_document.prefix = self.prefix
        self.mock_tree = Tree(mock_document)
        _set_tree(self.mock_tree)

    def mock_find_document(self, prefix):
        """Mock `Tree.find_document()` to return a mock document."""
        assert isinstance(self, Tree)
        assert prefix == TestModuleAddItem.prefix
        TestModuleAddItem.mock_document.prefix = prefix
        TestModuleAddItem.mock_document.path = TestModuleAddItem.path
        TestModuleAddItem.mock_document.root = TestModuleAddItem.root
        return TestModuleAddItem.mock_document

    @patch('doorstop.core.tree.Tree.find_document', mock_find_document)
    @patch('doorstop.core.item.Item.new')
    def test_add_item(self, mock_new):
        """Verify an item can be imported into an existing document."""
        importer.add_item(self.prefix, self.uid)
        mock_new.assert_called_once_with(self.mock_tree, self.mock_document,
                                         self.path, self.root, self.uid,
                                         auto=False)

    @patch('doorstop.core.builder._get_tree')
    @patch('doorstop.core.tree.Tree.find_document', mock_find_document)
    @patch('doorstop.core.item.Item.new')
    def test_add_item_explicit_document(self, mock_new, mock_get_tree):
        """Verify an item can be imported into an explicit document."""
        mock_document = self.mock_document
        mock_tree = mock_document.tree
        mock_document.tree._item_cache = MagicMock()  # pylint:disable=W0212
        importer.add_item(self.prefix, self.uid, document=mock_document)
        self.assertFalse(mock_get_tree.called)
        mock_new.assert_called_once_with(mock_tree, mock_document,
                                         self.path, self.root, self.uid,
                                         auto=False)

    @patch('doorstop.settings.ADDREMOVE_FILES', False)
    @patch('doorstop.core.tree.Tree.find_document', mock_find_document)
    def test_add_item_with_attrs(self):
        """Verify an item can be imported with attributes."""
        attrs = {'text': "The item text.", 'ext': "External attrubte."}
        item = importer.add_item(self.prefix, self.uid, attrs=attrs)
        self.assertEqual(self.uid, item.uid)
        self.assertEqual(attrs['text'], item.text)
        self.assertEqual(attrs['ext'], item.get('ext'))
