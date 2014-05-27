"""Unit tests for the doorstop.core.publisher module."""

import unittest
from unittest.mock import patch, Mock, MagicMock

import os
import tempfile
import shutil

from doorstop.common import DoorstopError
from doorstop.core import publisher
from doorstop.core.vcs.mockvcs import WorkingCopy

from doorstop.core.test import FILES, EMPTY, ENV, REASON
from doorstop.core.test.test_item import MockItem as _MockItem

# Whenever the report format is changed:
#  1. set CHECK_PUBLISHED_CONTENT to False
#  2. re-run all tests
#  3. manually verify the newly generated reports are correct
#  4. set CHECK_PUBLISHED_CONTENT to True
CHECK_PUBLISHED_CONTENT = True


class MockItem(_MockItem):  # pylint: disable=W0223,R0902,R0904

    """Mock item class with stubbed IO and a mock VCS reference."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree = Mock()
        self.tree.vcs = WorkingCopy(None)


class BaseTestCase(unittest.TestCase):  # pylint: disable=R0904

    """Base test class for the doorstop.core.publisher module."""  # pylint: disable=C0103

    @classmethod
    def setUpClass(cls):
        cls.item = MockItem('path/to/req3.yml',
                            _file=("links: [sys3]" + '\n'
                                   "text: 'Heading'" + '\n'
                                   "level: 1.1.0" + '\n'
                                   "normative: false"))
        cls.item2 = MockItem('path/to/req3.yml',
                             _file=("links: [sys3]\ntext: '" +
                                    ("Hello, world! " * 10) +
                                    "'\nlevel: 1.2"))
        cls.item2.find_child_links = lambda: ['tst1']
        cls.document = MagicMock()
        cls.document.items = [
            cls.item,
            cls.item2,
            MockItem('path/to/req1.yml',
                     _file="links: []\ntext: 'abc\n123'\nlevel: 1.1"),
            MockItem('path/to/req2.yml',
                     _file="links: [sys1, sys2]\ntext: ''\nlevel: 2"),
            MockItem('path/to/req4.yml',
                     _file="links: [sys2]\nref: 'CHECK_PUBLISHED_CONTENT'\n"
                     "level: 2.1.1"),
            MockItem('path/to/req2.yml',
                     _file="links: [sys1]\ntext: 'Heading 2'\nlevel: 2.1.0\n"
                     "normative: false"),
        ]
        cls.item3 = MockItem('path/to/req4.yml', _file=(
            "links: [sys4]" + '\n'
            "text: 'This shall...'" + '\n'
            "ref: Doorstop.sublime-project" + '\n'
            "level: 1.2" + '\n'
            "normative: true"))


class TestModule(BaseTestCase):  # pylint: disable=R0904

    """Unit tests for the doorstop.core.publisher module."""  # pylint: disable=C0103

    @patch('os.makedirs')
    @patch('builtins.open')
    @patch('doorstop.core.publisher.lines')
    def test_publish_html(self, mock_lines, mock_open, mock_makedirs):
        """Verify a (mock) HTML file can be created."""
        dirpath = os.path.join('mock', 'directory')
        path = os.path.join(dirpath, 'report.html')
        # Act
        publisher.publish(self.document, path, '.html')
        # Assert
        mock_makedirs.assert_called_once_with(dirpath)
        mock_open.assert_called_once_with(path, 'w')
        mock_lines.assert_called_once_with(self.document, '.html')

    def test_publish_unknown(self):
        """Verify an exception is raised when publishing unknown formats."""
        self.assertRaises(DoorstopError,
                          publisher.publish, self.document, 'a.a')
        self.assertRaises(DoorstopError,
                          publisher.publish, self.document, 'a.txt', '.a')

    # TODO: change to published.*

    @patch('os.makedirs')
    @patch('builtins.open')
    def test_publish_document(self, mock_open, mock_makedirs):
        """Verify a document can be published."""
        dirpath = os.path.join('mock', 'directory')
        path = os.path.join(dirpath, 'report.html')
        mock_document = MagicMock()
        mock_document.items = []
        # Act
        publisher.publish(mock_document, path)
        # Assert
        mock_makedirs.assert_called_once_with(dirpath)
        self.assertEqual(2, mock_open.call_count)

    def test_index(self):
        """Verify an HTML index can be created."""
        # Arrange
        path = os.path.join(FILES, 'index.html')
        # Act
        publisher.index(FILES)
        # Assert
        self.assertTrue(os.path.isfile(path))

    def test_index_no_files(self):
        """Verify an HTML index is only created when files exist."""
        path = os.path.join(EMPTY, 'index.html')
        # Act
        publisher.index(EMPTY)
        # Assert
        self.assertFalse(os.path.isfile(path))

    def test_lines_text_item_heading(self):
        """Verify a text report can be created from an item (heading)."""
        expected = "1.1     Heading\n\n"
        lines = publisher.lines(self.item, '.txt')
        # Act
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertEqual(expected, text)

    def test_lines_text_item_normative(self):
        """Verify a text report can be created from an item (normative)."""
        expected = ("1.2     req4" + '\n\n'
                    "        This shall..." + '\n\n'
                    "        Reference: Doorstop.sublime-project (line None)"
                    + '\n\n'
                    "        Links: sys4" + '\n\n')
        lines = publisher.lines(self.item3, '.txt')
        # Act
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertEqual(expected, text)

    @patch('doorstop.settings.CHECK_REF', False)
    def test_lines_text_item_no_ref(self):
        """Verify a text report can be created without checking references."""
        self.item.ref = 'abc123'
        self.item.heading = False
        # Act
        lines = publisher.lines(self.item, '.txt')
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertIn("Reference: 'abc123'", text)

    @patch('doorstop.settings.PUBLISH_CHILD_LINKS', True)
    def test_lines_text_item_with_child_links(self):
        """Verify a text report can be created with child links."""
        # Act
        lines = publisher.lines(self.item2, '.txt')
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertIn("Child links: tst1", text)

    def test_lines_markdown_item_heading(self):
        """Verify a Markdown report can be created from an item (heading)."""
        expected = "## 1.1 Heading\n\n"
        # Act
        lines = publisher.lines(self.item, '.md')
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertEqual(expected, text)

    def test_lines_markdown_item_normative(self):
        """Verify a Markdown report can be created from an item (normative)."""
        expected = ("## 1.2 req4" + '\n\n'
                    "This shall..." + '\n\n'
                    "Reference: Doorstop.sublime-project (line None)" + '\n\n'
                    "*Links: sys4*" + '\n\n')
        # Act
        lines = publisher.lines(self.item3, '.md')
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertEqual(expected, text)

    def test_lines_html_item(self):
        """Verify an HTML report can be created from an item."""
        expected = "<h2>1.1 Heading</h2>\n"
        # Act
        lines = publisher.lines(self.item, '.html')
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertEqual(expected, text)

    @patch('doorstop.settings.PUBLISH_CHILD_LINKS', True)
    def test_lines_html_item_with_child_links(self):
        """Verify an HTML report can be created from an item w/ child links."""
        # Act
        lines = publisher.lines(self.item2, '.html')
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertIn("Child links: tst1", text)

    def test_lines_unknown(self):
        """Verify an exception is raised when iterating an unknown format."""
        # Act
        gen = publisher.lines(self.document, '.a')
        # Assert
        self.assertRaises(DoorstopError, list, gen)


@unittest.skipUnless(os.getenv(ENV) or not CHECK_PUBLISHED_CONTENT, REASON)  # pylint: disable=R0904
class TestModuleIntegration(BaseTestCase):  # pylint: disable=R0904

    """Integration tests for the doorstop.core.publisher module."""  # pylint: disable=C0103

    def test_publish_html(self):
        """Verify an HTML file can be created."""
        temp = tempfile.mkdtemp()
        try:
            path = os.path.join(temp, 'report.html')
            # Act
            publisher.publish(self.document, path, '.html')
            # Assert
            self.assertTrue(os.path.isfile(path))
        finally:
            shutil.rmtree(temp)

    def test_lines_text_document(self):
        """Verify text can be published from a document."""
        path = os.path.join(FILES, 'report.txt')
        expected = open(path).read()
        # Act
        lines = publisher.lines(self.document, '.txt')
        text = ''.join(line + '\n' for line in lines)
        # Assert
        if CHECK_PUBLISHED_CONTENT:
            self.assertEqual(expected, text)
        with open(path, 'w') as outfile:
            outfile.write(text)

    @patch('doorstop.settings.PUBLISH_CHILD_LINKS', True)
    def test_lines_text_document_with_child_links(self):
        """Verify text can be published from a document with child links."""
        path = os.path.join(FILES, 'report2.txt')
        expected = open(path).read()
        # Act
        lines = publisher.lines(self.document, '.txt')
        text = ''.join(line + '\n' for line in lines)
        # Assert
        if CHECK_PUBLISHED_CONTENT:
            self.assertEqual(expected, text)
        with open(path, 'w') as outfile:
            outfile.write(text)

    def test_lines_markdown_document(self):
        """Verify Markdown can be published from a document."""
        path = os.path.join(FILES, 'report.md')
        expected = open(path).read()
        # Act
        lines = publisher.lines(self.document, '.md')
        text = ''.join(line + '\n' for line in lines)
        # Assert
        if CHECK_PUBLISHED_CONTENT:
            self.assertEqual(expected, text)
        with open(path, 'w') as outfile:
            outfile.write(text)

    @patch('doorstop.settings.PUBLISH_CHILD_LINKS', True)
    def test_lines_markdown_document_with_child_links(self):
        """Verify Markdown can be published from a document w/ child links."""
        path = os.path.join(FILES, 'report2.md')
        expected = open(path).read()
        # Act
        lines = publisher.lines(self.document, '.md')
        text = ''.join(line + '\n' for line in lines)
        # Assert
        if CHECK_PUBLISHED_CONTENT:
            self.assertEqual(expected, text)
        with open(path, 'w') as outfile:
            outfile.write(text)

    def test_lines_html_document(self):
        """Verify HTML can be published from a document."""
        path = os.path.join(FILES, 'report.html')
        expected = open(path).read()
        # Act
        lines = publisher.lines(self.document, '.html')
        text = ''.join(line + '\n' for line in lines)
        # Assert
        if CHECK_PUBLISHED_CONTENT:
            self.assertEqual(expected, text)
        with open(path, 'w') as outfile:
            outfile.write(text)

    @patch('doorstop.settings.PUBLISH_CHILD_LINKS', True)
    def test_lines_html_document_with_child_links(self):
        """Verify HTML can be published from a document with child links."""
        path = os.path.join(FILES, 'report2.html')
        expected = open(path).read()
        # Act
        lines = publisher.lines(self.document, '.html')
        text = ''.join(line + '\n' for line in lines)
        # Assert
        if CHECK_PUBLISHED_CONTENT:
            self.assertEqual(expected, text)
        with open(path, 'w') as outfile:
            outfile.write(text)
