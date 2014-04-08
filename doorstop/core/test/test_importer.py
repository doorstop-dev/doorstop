"""Unit tests for the doorstop.core.importer module."""

import unittest
from unittest.mock import patch, Mock

import os
import tempfile
import shutil

from doorstop.core import importer
from doorstop.common import DoorstopError

from doorstop.core.test import ENV, REASON, FILES, SYS, EMPTY
from doorstop.core.test.test_tree import MockDocument
from doorstop.core.test.test_document import MockItem


@patch('doorstop.core.document.Document', MockDocument)  # pylint: disable=R0904
@patch('doorstop.core.tree.Document', MockDocument)  # pylint: disable=R0904
class TestNewDocument(unittest.TestCase):  # pylint: disable=R0904

    """Unit tests for new_document function."""  # pylint: disable=C0103

    def setUp(self):
        self.cwd = os.getcwd()
        self.temp = tempfile.mkdtemp()
        os.chdir(self.temp)

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.temp)

    def test_create_document(self):
        """Verify a new document can be created to import items."""
        prefix = 'PREFIX'
        path = os.path.join(self.temp, 'DIRECTORY')
        document = importer.new_document(prefix, path)
        self.assertEqual(prefix, document.prefix)
        self.assertEqual(path, document.path)

    def test_create_document_with_parent(self):
        """Verify a new document can be created with a parent."""
        prefix = 'PREFIX'
        parent = 'PARENT_PREFIX'
        path = os.path.join(self.temp, 'DIRECTORY')
        document = importer.new_document(prefix, path, parent=parent)
        self.assertEqual(prefix, document.prefix)
        self.assertEqual(path, document.path)
        self.assertEqual(parent, document.parent)

    @patch('doorstop.core.tree.Tree.new', Mock(side_effect=DoorstopError))
    def test_create_document_already_exists(self):
        """Verify non-parent exceptions are re-raised."""
        prefix = 'PREFIX'
        path = os.path.join(tempfile.gettempdir(), 'DIRECTORY')
        self.assertRaises(DoorstopError, importer.new_document, prefix, path)


@patch('doorstop.core.item.Item', MockItem)  # pylint: disable=R0904
class TestAddItem(unittest.TestCase):  # pylint: disable=R0904

    """Unit tests for the add_item function."""  # pylint: disable=C0103

    PREFIX = 'PREFIX'
    PATH = os.path.join(tempfile.gettempdir(), 'DIRECTORY')

    def setUp(self):
        self.cwd = os.getcwd()
        self.temp = tempfile.mkdtemp()
        os.chdir(self.temp)

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.temp)

    def mock_find_document(self, prefix):
        """Mock Tree.find_document()."""
        assert prefix == TestAddItem.PREFIX
        document = MockDocument(TestAddItem.PATH)
        document.prefix = TestAddItem.PREFIX
        return document

    @patch('doorstop.core.tree.Tree.find_document', mock_find_document)
    def test_add_item(self):
        """Verify an item can be imported into an existing document."""
        identifier = 'PREFIX-0042'
        item = importer.add_item(self.PREFIX, identifier)
        self.assertEqual(identifier, item.id)
        self.assertEqual("", item.text)

    @patch('doorstop.core.tree.Tree.find_document', mock_find_document)
    def test_add_item_with_attrs(self):
        """Verify an item can be imported with attributes."""
        identifier = 'PREFIX-0042'
        attrs = {'text': "The item text."}
        item = importer.add_item(self.PREFIX, identifier, attrs=attrs)
        self.assertEqual(identifier, item.id)
        self.assertEqual(attrs['text'], item.text)
