"""Unit tests for the doorstop.core.importer module."""

import unittest
from unittest.mock import patch, Mock

import os
import tempfile
import shutil

from doorstop.core import importer
from doorstop.core.tree import Tree
from doorstop.common import DoorstopError

from doorstop.core.test import ENV, REASON
from doorstop.core.test.test_tree import MockDocument
from doorstop.core.test.test_document import MockItem


class TestNewDocument(unittest.TestCase):  # pylint: disable=R0904

    """Unit tests for the new_document function."""  # pylint: disable=C0103

    def setUp(self):
        # Create default document options
        self.prefix = 'PREFIX'
        self.root = tempfile.gettempdir()
        self.path = os.path.join(self.root, 'DIRECTORY')
        self.parent = 'PARENT_PREFIX'
        # Ensure the tree is reloaded
        mock_document = Mock()
        mock_document.root = self.root
        self.mock_tree = Tree(mock_document)
        importer._TREE = self.mock_tree  # pylint: disable=W0212

    @patch('doorstop.core.importer.build')
    @patch('doorstop.core.tree.Tree.new', Mock())
    def test_build(self, mock_build):
        """Verify the tree is built (if needed) before creating documents."""
        importer._TREE = None  # pylint: disable=W0212
        importer.new_document(self.prefix, self.path)
        mock_build.assert_called_once_with()

    @patch('doorstop.core.tree.Tree.new')
    def test_create_document(self, mock_new):
        """Verify a new document can be created to import items."""
        importer.new_document(self.prefix, self.path)
        mock_new.assert_called_once_with(self.path, self.prefix, parent=None)

    @patch('doorstop.core.tree.Tree.new')
    def test_create_document_with_parent(self, mock_new):
        """Verify a new document can be created with a parent."""
        importer.new_document(self.prefix, self.path, parent=self.parent)
        mock_new.assert_called_once_with(self.path, self.prefix,
                                         parent=self.parent)

    @patch('doorstop.core.tree.Tree.new', Mock(side_effect=DoorstopError))
    def test_create_document_already_exists(self):
        """Verify non-parent exceptions are re-raised."""
        self.assertRaises(DoorstopError,
                          importer.new_document, self.prefix, self.path)

    @patch('doorstop.core.tree.Tree.new', Mock(side_effect=DoorstopError))
    @patch('doorstop.core.document.Document.new')
    def test_create_document_unknown_parent(self, mock_new):
        """Verify documents can be created with unknown parents."""
        importer.new_document(self.prefix, self.path, parent=self.parent)
        mock_new.assert_called_once_with(self.path, self.root, self.prefix,
                                         parent=self.parent)


@unittest.skipUnless(os.getenv(ENV), REASON)
class TestNewDocumentIntegration(unittest.TestCase):  # pylint: disable=R0904

    """Integrations tests for the new_document function."""  # pylint: disable=C0103

    def setUp(self):
        # Create a temporary mock working copy
        self.cwd = os.getcwd()
        self.temp = tempfile.mkdtemp()
        os.chdir(self.temp)
        open(".mockvcs", 'w').close()
        # Create default document options
        self.prefix = 'PREFIX'
        self.root = self.temp
        self.path = os.path.join(self.root, 'DIRECTORY')
        self.parent = 'PARENT_PREFIX'
        # Ensure the tree is reloaded
        importer._TREE = None  # pylint: disable=W0212

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.temp)

    def test_create_document(self):
        """Verify a new document can be created to import items."""
        document = importer.new_document(self.prefix, self.path)
        self.assertEqual(self.prefix, document.prefix)
        self.assertEqual(self.path, document.path)

    def test_create_document_with_unknown_parent(self):
        """Verify a new document can be created with an unknown parent."""
        document = importer.new_document(self.prefix, self.path,
                                         parent=self.parent)
        self.assertEqual(self.prefix, document.prefix)
        self.assertEqual(self.path, document.path)
        self.assertEqual(self.parent, document.parent)

    def test_create_document_already_exists(self):
        """Verify non-parent exceptions are re-raised."""
        # Create a document
        importer.new_document(self.prefix, self.path)
        # Attempt to create the same document
        self.assertRaises(DoorstopError,
                          importer.new_document, self.prefix, self.path)


@patch('doorstop.core.item.Item', MockItem)  # pylint: disable=R0904
class TestAddItem(unittest.TestCase):  # pylint: disable=R0904

    """Unit tests for the add_item function."""  # pylint: disable=C0103

    PREFIX = 'PREFIX'
    PATH = os.path.join(tempfile.gettempdir(), 'DIRECTORY')

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
