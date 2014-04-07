"""Unit tests for the doorstop.core.importer module."""

import unittest
from unittest.mock import patch

import tempfile
import shutil

from doorstop.core import importer

from doorstop.core.test import ENV, REASON, FILES, SYS, EMPTY
from doorstop.core.test.test_document import MockDocument as _MockDocment


class MockDocument(_MockDocment):  # pylint: disable=W0223,R0902,R0904

    """Mock Document class that is always skipped in tree placement."""

    skip = True


class MockDocumentNoSkip(MockDocument):  # pylint: disable=W0223,R0902,R0904

    """Mock Document class that is never skipped in tree placement."""

    SKIP = '__disabled__'  # never skip mock Documents


@patch('doorstop.core.document.Document', MockDocument)  # pylint: disable=R0904
@patch('doorstop.core.tree.Document', MockDocument)  # pylint: disable=R0904
class TestModule(unittest.TestCase):  # pylint: disable=R0904

    """Unit tests for the doorstop.core.importer module."""  # pylint: disable=C0103

    def test_create_document(self):
        """Verify a new document can be created to import items."""
        prefix = 'PREFIX'
        path = tempfile.mkdtemp()
        try:
            document = importer.create_document(prefix, path)
            self.assertEqual(prefix, document.prefix)
        finally:
            shutil.rmtree(path)

    def test_add_item(self):
        """Verify items can be imported to an existing document."""
        identifier = 'PREFIX-0042'
        attrs = {'text': "The item text."}
        item = importer.add_item('PREFIX', identifier, attrs)
        self.assertEqual(identifier, item.id)
        self.assertEqual(attrs['text'], item.text)
