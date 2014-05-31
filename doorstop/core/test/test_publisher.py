"""Unit tests for the doorstop.core.publisher module."""

import unittest
from unittest.mock import patch, Mock, MagicMock

import os

from doorstop.common import DoorstopError
from doorstop.core import publisher
from doorstop.core.vcs.mockvcs import WorkingCopy

from doorstop.core.test import FILES, EMPTY
from doorstop.core.test.test_item import MockItem as _MockItem


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
        mock_item = Mock()
        mock_item.id = 'sys3'
        mock_item.document.prefix = 'sys'
        cls.item2.tree = Mock()
        cls.item2.tree.find_item = Mock(return_value=mock_item)
        mock_item2 = Mock()
        mock_item2.id = 'tst1'
        mock_item2.document.prefix = 'tst'
        cls.item2.find_child_links = lambda: [mock_item2.id]
        cls.item2.find_child_items = lambda: [mock_item2]

        cls.document = MagicMock()
        cls.document.items = [
            cls.item,
            cls.item2,
            MockItem('path/to/req1.yml',
                     _file="links: []\ntext: 'abc\n123'\nlevel: 1.1"),
            MockItem('path/to/req2.yml',
                     _file="links: []\ntext: ''\nlevel: 2"),
            MockItem('path/to/req4.yml',
                     _file="links: []\nref: 'CHECK_PUBLISHED_CONTENT'\n"
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
        path = os.path.join(dirpath, 'published.html')
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

    @patch('os.makedirs')
    @patch('builtins.open')
    def test_publish_document(self, mock_open, mock_makedirs):
        """Verify a document can be published."""
        dirpath = os.path.join('mock', 'directory')
        path = os.path.join(dirpath, 'published.html')
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
        """Verify text can be published from an item (heading)."""
        expected = "1.1     Heading\n\n"
        lines = publisher.lines(self.item, '.txt')
        # Act
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertEqual(expected, text)

    def test_lines_text_item_normative(self):
        """Verify text can be published from an item (normative)."""
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
        """Verify text can be published without checking references."""
        self.item.ref = 'abc123'
        self.item.heading = False
        # Act
        lines = publisher.lines(self.item, '.txt')
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertIn("Reference: 'abc123'", text)

    @patch('doorstop.settings.PUBLISH_CHILD_LINKS', True)
    def test_lines_text_item_with_child_links(self):
        """Verify text can be published with child links."""
        # Act
        lines = publisher.lines(self.item2, '.txt')
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertIn("Child links: tst1", text)

    def test_lines_markdown_item_heading(self):
        """Verify Markdown can be published from an item (heading)."""
        expected = "## 1.1 Heading {: #req3 }\n\n"
        # Act
        lines = publisher.lines(self.item, '.md', linkify=True)
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertEqual(expected, text)

    @patch('doorstop.settings.PUBLISH_CHILD_LINKS', True)
    def test_lines_markdown_item_with_child_links(self):
        """Verify Markdown can be published from an item (heading)."""
        # Act
        lines = publisher.lines(self.item2, '.md')
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertIn("Child links: tst1", text)

    def test_lines_markdown_item_normative(self):
        """Verify Markdown can be published from an item (normative)."""
        expected = ("## 1.2 req4" + '\n\n'
                    "This shall..." + '\n\n'
                    "Reference: Doorstop.sublime-project (line None)" + '\n\n'
                    "*Links: sys4*" + '\n\n')
        # Act
        lines = publisher.lines(self.item3, '.md', linkify=False)
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertEqual(expected, text)

    def test_lines_html_item(self):
        """Verify HTML can be published from an item."""
        expected = '<h2 id="req3">1.1 Heading</h2>\n'
        # Act
        lines = publisher.lines(self.item, '.html')
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertEqual(expected, text)

    @patch('doorstop.settings.PUBLISH_CHILD_LINKS', True)
    def test_lines_html_item_with_child_links(self):
        """Verify HTML can be published from an item w/ child links."""
        # Act
        lines = publisher.lines(self.item2, '.html')
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertIn("Child links:", text)
        self.assertIn(">tst1</a>", text)

    def test_lines_unknown(self):
        """Verify an exception is raised when iterating an unknown format."""
        # Act
        gen = publisher.lines(self.document, '.a')
        # Assert
        self.assertRaises(DoorstopError, list, gen)
