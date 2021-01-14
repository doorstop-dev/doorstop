# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.core.publisher module."""

# pylint: disable=unused-argument,protected-access

import os
import unittest
from unittest import mock
from unittest.mock import MagicMock, Mock, call, patch

from doorstop.common import DoorstopError
from doorstop.core import publisher
from doorstop.core.document import Document
from doorstop.core.tests import (
    EMPTY,
    FILES,
    ROOT,
    MockDataMixIn,
    MockDocument,
    MockItem,
    MockItemAndVCS,
)


class TestModule(MockDataMixIn, unittest.TestCase):
    """Unit tests for the doorstop.core.publisher module."""

    @patch('os.path.isdir', Mock(return_value=False))
    @patch('os.makedirs')
    @patch('builtins.open')
    def test_publish_document(self, mock_open, mock_makedirs):
        """Verify a document can be published."""
        dirpath = os.path.join('mock', 'directory')
        path = os.path.join(dirpath, 'published.html')
        self.document.items = []
        # Act
        path2 = publisher.publish(self.document, path)
        # Assert
        self.assertIs(path, path2)
        mock_makedirs.assert_called_once_with(os.path.join(dirpath, Document.ASSETS))
        mock_open.assert_called_once_with(path, 'wb')

    @patch('os.path.isdir', Mock(return_value=False))
    @patch('os.makedirs')
    @patch('builtins.open')
    @patch('doorstop.core.publisher.publish_lines')
    def test_publish_document_html(self, mock_lines, mock_open, mock_makedirs):
        """Verify a (mock) HTML file can be created."""
        dirpath = os.path.join('mock', 'directory')
        path = os.path.join(dirpath, 'published.custom')
        # Act
        path2 = publisher.publish(self.document, path, '.html')
        # Assert
        self.assertIs(path, path2)
        mock_makedirs.assert_called_once_with(os.path.join(dirpath, Document.ASSETS))
        mock_open.assert_called_once_with(path, 'wb')
        mock_lines.assert_called_once_with(
            self.document,
            '.html',
            template=publisher.HTMLTEMPLATE,
            toc=True,
            linkify=False,
        )

    @patch('os.path.isdir', Mock(side_effect=[True, False, False, False]))
    @patch('os.remove')
    @patch('glob.glob')
    @patch('builtins.open')
    @patch('doorstop.core.publisher.publish_lines')
    def test_publish_document_deletes_the_contents_of_assets_folder(
        self, mock_lines, mock_open, mock_glob, mock_rm
    ):
        """Verify that the contents of an assets directory next to the published file is deleted"""
        dirpath = os.path.abspath(os.path.join('mock', 'directory'))
        path = os.path.join(dirpath, 'published.custom')
        assets = [
            os.path.join(dirpath, Document.ASSETS, dir) for dir in ['css', 'logo.png']
        ]
        mock_glob.return_value = assets
        # Act
        path2 = publisher.publish(self.document, path, '.html')
        # Assert
        self.assertIs(path, path2)
        mock_open.assert_called_once_with(path, 'wb')
        mock_lines.assert_called_once_with(
            self.document,
            '.html',
            template=publisher.HTMLTEMPLATE,
            toc=True,
            linkify=False,
        )
        calls = [call(assets[0]), call(assets[1])]
        self.assertEqual(calls, mock_rm.call_args_list)

    @patch('os.path.isdir', Mock(return_value=False))
    @patch('doorstop.core.document.Document.copy_assets')
    @patch('os.makedirs')
    @patch('builtins.open')
    def test_publish_document_copies_assets(
        self, mock_open, mock_makedirs, mock_copyassets
    ):
        """Verify that assets are published"""
        dirpath = os.path.join('mock', 'directory')
        assets_path = os.path.join(dirpath, 'assets')
        path = os.path.join(dirpath, 'published.custom')
        document = MockDocument('/some/path')
        mock_open.side_effect = lambda *args, **kw: mock.mock_open(
            read_data="$body"
        ).return_value
        # Act
        path2 = publisher.publish(document, path, '.html')
        # Assert
        self.assertIs(path, path2)
        mock_makedirs.assert_called_once_with(os.path.join(dirpath, Document.ASSETS))
        mock_copyassets.assert_called_once_with(assets_path)

    def test_publish_document_unknown(self):
        """Verify an exception is raised when publishing unknown formats."""
        self.assertRaises(DoorstopError, publisher.publish, self.document, 'a.a')
        self.assertRaises(
            DoorstopError, publisher.publish, self.document, 'a.txt', '.a'
        )

    @patch('os.path.isdir', Mock(return_value=False))
    @patch('os.makedirs')
    @patch('doorstop.core.publisher._index')
    @patch('builtins.open')
    def test_publish_tree(self, mock_open, mock_index, mock_makedirs):
        """Verify a tree can be published."""
        dirpath = os.path.join('mock', 'directory')
        mock_open.side_effect = lambda *args, **kw: mock.mock_open(
            read_data="$body"
        ).return_value
        expected_calls = [call(os.path.join('mock', 'directory', 'MOCK.html'), 'wb')]
        # Act
        dirpath2 = publisher.publish(self.mock_tree, dirpath)
        # Assert
        self.assertIs(dirpath, dirpath2)
        self.assertEqual(expected_calls, mock_open.call_args_list)
        mock_index.assert_called_once_with(dirpath, tree=self.mock_tree)

    @patch('os.path.isdir', Mock(return_value=False))
    @patch('os.makedirs')
    @patch('doorstop.core.publisher._index')
    @patch('builtins.open')
    def test_publish_tree_no_index(self, mock_open, mock_index, mock_makedirs):
        """Verify a tree can be published."""
        dirpath = os.path.join('mock', 'directory')
        mock_open.side_effect = lambda *args, **kw: mock.mock_open(
            read_data="$body"
        ).return_value
        expected_calls = [call(os.path.join('mock', 'directory', 'MOCK.html'), 'wb')]
        # Act
        dirpath2 = publisher.publish(self.mock_tree, dirpath, index=False)
        # Assert
        self.assertIs(dirpath, dirpath2)
        self.assertEqual(0, mock_index.call_count)
        print(mock_open.call_args_list)
        self.assertEqual(expected_calls, mock_open.call_args_list)

    def test_index(self):
        """Verify an HTML index can be created."""
        # Arrange
        path = os.path.join(FILES, 'index.html')
        # Act
        publisher._index(FILES)
        # Assert
        self.assertTrue(os.path.isfile(path))

    def test_index_no_files(self):
        """Verify an HTML index is only created when files exist."""
        path = os.path.join(EMPTY, 'index.html')
        # Act
        publisher._index(EMPTY)
        # Assert
        self.assertFalse(os.path.isfile(path))

    def test_index_tree(self):
        """Verify an HTML index can be created with a tree."""
        path = os.path.join(FILES, 'index2.html')
        mock_tree = MagicMock()
        mock_tree.documents = []
        for prefix in ('SYS', 'HLR', 'LLR', 'HLT', 'LLT'):
            mock_document = MagicMock()
            mock_document.prefix = prefix
            mock_tree.documents.append(mock_document)
        mock_tree.draw = lambda: "(mock tree structure)"
        mock_item = Mock()
        mock_item.uid = 'KNOWN-001'
        mock_item.document = Mock()
        mock_item.document.prefix = 'KNOWN'
        mock_item.header = None
        mock_item_unknown = Mock(spec=['uid'])
        mock_item_unknown.uid = 'UNKNOWN-002'
        mock_trace = [
            (None, mock_item, None, None, None),
            (None, None, None, mock_item_unknown, None),
            (None, None, None, None, None),
        ]
        mock_tree.get_traceability = lambda: mock_trace
        # Act
        publisher._index(FILES, index="index2.html", tree=mock_tree)
        # Assert
        self.assertTrue(os.path.isfile(path))

    def test_lines_text_item(self):
        """Verify text can be published from an item."""
        with patch.object(
            self.item5, 'find_ref', Mock(return_value=('path/to/mock/file', 42))
        ):
            lines = publisher.publish_lines(self.item5, '.txt')
            text = ''.join(line + '\n' for line in lines)
        self.assertIn("Reference: path/to/mock/file (line 42)", text)

    def test_lines_text_item_references(self):
        """Verify references can be published to a text file from an item."""
        mock_value = [('path/to/mock/file1', 3), ('path/to/mock/file2', None)]
        with patch.object(self.item6, 'find_references', Mock(return_value=mock_value)):
            lines = publisher.publish_lines(self.item6, '.txt')
            text = ''.join(line + '\n' for line in lines)
        self.assertIn(
            "Reference: path/to/mock/file1 (line 3), path/to/mock/file2", text
        )

    def test_lines_text_item_heading(self):
        """Verify text can be published from an item (heading)."""
        expected = "1.1     Heading\n\n"
        lines = publisher.publish_lines(self.item, '.txt')
        # Act
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertEqual(expected, text)

    @patch('doorstop.settings.PUBLISH_HEADING_LEVELS', False)
    def test_lines_text_item_heading_no_heading_levels(self):
        """Verify an item heading level can be ommitted."""
        expected = "Heading\n\n"
        lines = publisher.publish_lines(self.item, '.txt')
        # Act
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertEqual(expected, text)

    def test_single_line_heading_to_markdown(self):
        """Verify a single line heading is published as a heading with an attribute equal to the item id"""
        expected = "## 1.1 Heading {#req3 }\n\n"
        lines = publisher.publish_lines(self.item, '.md', linkify=True)
        # Act
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertEqual(expected, text)

    def test_multi_line_heading_to_markdown(self):
        """Verify a multi line heading is published as a heading with an attribute equal to the item id"""
        item = MockItemAndVCS(
            'path/to/req3.yml',
            _file=(
                "links: [sys3]" + '\n'
                "text: 'Heading\n\nThis section describes publishing.'" + '\n'
                "level: 1.1.0" + '\n'
                "normative: false"
            ),
        )
        expected = "## 1.1 Heading {#req3 }\nThis section describes publishing.\n\n"
        lines = publisher.publish_lines(item, '.md', linkify=True)
        # Act
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertEqual(expected, text)

    @patch('doorstop.settings.PUBLISH_HEADING_LEVELS', False)
    def test_multi_line_heading_to_markdown_no_heading_levels(self):
        """Verify a multi line heading is published as a heading, without level, with an attribute equal to the item id"""
        item = MockItemAndVCS(
            'path/to/req3.yml',
            _file=(
                "links: [sys3]" + '\n'
                "text: 'Heading\n\nThis section describes publishing.'" + '\n'
                "level: 1.1.0" + '\n'
                "normative: false"
            ),
        )
        expected = "## Heading {#req3 }\nThis section describes publishing.\n\n"
        lines = publisher.publish_lines(item, '.md', linkify=True)
        # Act
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertEqual(expected, text)

    @patch('doorstop.settings.PUBLISH_CHILD_LINKS', False)
    def test_lines_text_item_normative(self):
        """Verify text can be published from an item (normative)."""
        expected = (
            "1.2     req4" + '\n\n'
            "        This shall..." + '\n\n'
            "        Reference: Doorstop.sublime-project" + '\n\n'
            "        Links: sys4" + '\n\n'
        )
        lines = publisher.publish_lines(self.item3, '.txt')
        # Act
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertEqual(expected, text)

    @patch('doorstop.settings.CHECK_REF', False)
    def test_lines_text_item_no_ref_check(self):
        """Verify text can be published without checking references."""
        lines = publisher.publish_lines(self.item5, '.txt')
        text = ''.join(line + '\n' for line in lines)
        self.assertIn("Reference: 'abc123'", text)

    @patch('doorstop.settings.CHECK_REF', False)
    def test_lines_text_item_no_references_check(self):
        """Verify text can be published without checking references."""
        lines = publisher.publish_lines(self.item6, '.txt')
        text = ''.join(line + '\n' for line in lines)
        self.assertIn("Reference: 'abc1', 'abc2'", text)

    @patch('doorstop.settings.PUBLISH_CHILD_LINKS', True)
    def test_lines_text_item_with_child_links(self):
        """Verify text can be published with child links."""
        # Act
        lines = publisher.publish_lines(self.item2, '.txt')
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertIn("Child links: tst1", text)

    def test_lines_markdown_item(self):
        """Verify Markdown can be published from an item."""
        with patch.object(
            self.item5, 'find_ref', Mock(return_value=('path/to/mock/file', 42))
        ):
            lines = publisher.publish_lines(self.item5, '.md')
            text = ''.join(line + '\n' for line in lines)
        self.assertIn("> `path/to/mock/file` (line 42)", text)

    def test_lines_markdown_item_references(self):
        """Verify Markdown can be published from an item."""
        references_mock = [('path/to/mock/file1', 3), ('path/to/mock/file2', None)]

        with patch.object(
            self.item6, 'find_references', Mock(return_value=references_mock)
        ):
            lines = publisher.publish_lines(self.item6, '.md')
            text = ''.join(line + '\n' for line in lines)
        self.assertIn("> `path/to/mock/file1` (line 3)\n> `path/to/mock/file2`", text)

    def test_lines_markdown_item_heading(self):
        """Verify Markdown can be published from an item (heading)."""
        expected = "## 1.1 Heading {#req3 }\n\n"
        # Act
        lines = publisher.publish_lines(self.item, '.md', linkify=True)
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertEqual(expected, text)

    @patch('doorstop.settings.PUBLISH_HEADING_LEVELS', False)
    def test_lines_markdown_item_heading_no_heading_levels(self):
        """Verify an item heading level can be ommitted."""
        expected = "## Heading {#req3 }\n\n"
        # Act
        lines = publisher.publish_lines(self.item, '.md', linkify=True)
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertEqual(expected, text)

    @patch('doorstop.settings.PUBLISH_CHILD_LINKS', False)
    def test_lines_markdown_item_normative(self):
        """Verify Markdown can be published from an item (normative)."""
        expected = (
            "## 1.2 req4 {#req4 }" + '\n\n'
            "This shall..." + '\n\n'
            "> `Doorstop.sublime-project`" + '\n\n'
            "*Links: sys4*" + '\n\n'
        )
        # Act
        lines = publisher.publish_lines(self.item3, '.md', linkify=False)
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertEqual(expected, text)

    @patch('doorstop.settings.PUBLISH_CHILD_LINKS', True)
    def test_lines_markdown_item_with_child_links(self):
        """Verify Markdown can be published from an item w/ child links."""
        # Act
        lines = publisher.publish_lines(self.item2, '.md')
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertIn("Child links: tst1", text)

    @patch('doorstop.settings.PUBLISH_CHILD_LINKS', False)
    def test_lines_markdown_item_without_child_links(self):
        """Verify Markdown can be published from an item w/o child links."""
        # Act
        lines = publisher.publish_lines(self.item2, '.md')
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertNotIn("Child links", text)

    @patch('doorstop.settings.PUBLISH_BODY_LEVELS', False)
    @patch('doorstop.settings.PUBLISH_CHILD_LINKS', False)
    def test_lines_markdown_item_without_body_levels(self):
        """Verify Markdown can be published from an item (no body levels)."""
        expected = (
            "## req4 {#req4 }" + '\n\n'
            "This shall..." + '\n\n'
            "> `Doorstop.sublime-project`" + '\n\n'
            "*Links: sys4*" + '\n\n'
        )
        # Act
        lines = publisher.publish_lines(self.item3, '.md', linkify=False)
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertEqual(expected, text)

    @patch('doorstop.settings.CHECK_REF', False)
    def test_lines_markdown_item_no_ref_check(self):
        """Verify Markdown can be published without checking references."""
        lines = publisher.publish_lines(self.item5, '.md')
        text = ''.join(line + '\n' for line in lines)
        self.assertIn("> 'abc123'", text)

    @patch('doorstop.settings.CHECK_REF', False)
    def test_lines_markdown_item_no_references_check(self):
        """Verify Markdown can be published without checking references."""
        lines = publisher.publish_lines(self.item6, '.md')
        text = ''.join(line + '\n' for line in lines)
        self.assertIn("> 'abc1'\n> 'abc2'", text)

    def test_lines_html_item(self):
        """Verify HTML can be published from an item."""
        expected = '<h2 id="req3">1.1 Heading</h2>\n'
        # Act
        lines = publisher.publish_lines(self.item, '.html')
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertEqual(expected, text)

    @patch('doorstop.settings.PUBLISH_HEADING_LEVELS', False)
    def test_lines_html_item_no_heading_levels(self):
        """Verify an item heading level can be omitted."""
        expected = '<h2 id="req3">Heading</h2>\n'
        # Act
        lines = publisher.publish_lines(self.item, '.html')
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertEqual(expected, text)

    def test_lines_html_item_linkify(self):
        """Verify HTML (hyper) can be published from an item."""
        expected = '<h2 id="req3">1.1 Heading</h2>\n'
        # Act
        lines = publisher.publish_lines(self.item, '.html', linkify=True)
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertEqual(expected, text)

    @patch('doorstop.settings.PUBLISH_CHILD_LINKS', True)
    def test_lines_html_item_with_child_links(self):
        """Verify HTML can be published from an item w/ child links."""
        # Act
        lines = publisher.publish_lines(self.item2, '.html')
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertIn("Child links: tst1", text)

    @patch('doorstop.settings.PUBLISH_CHILD_LINKS', False)
    def test_lines_html_item_without_child_links(self):
        """Verify HTML can be published from an item w/o child links."""
        # Act
        lines = publisher.publish_lines(self.item2, '.html')
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertNotIn("Child links", text)

    @patch('doorstop.settings.PUBLISH_CHILD_LINKS', True)
    def test_lines_html_item_with_child_links_linkify(self):
        """Verify HTML (hyper) can be published from an item w/ child links."""
        # Act
        lines = publisher.publish_lines(self.item2, '.html', linkify=True)
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertIn("Child links:", text)
        self.assertIn("tst.html#tst1", text)

    def test_lines_unknown(self):
        """Verify an exception is raised when iterating an unknown format."""
        # Act
        gen = publisher.publish_lines(self.document, '.a')
        # Assert
        self.assertRaises(DoorstopError, list, gen)


@patch('doorstop.core.item.Item', MockItem)
class TestTableOfContents(unittest.TestCase):
    """Unit tests for the Document class."""

    def setUp(self):
        self.document = MockDocument(FILES, root=ROOT)

    def test_toc_no_links_or_heading_levels(self):
        """Verify the table of contents is generated with heading levels"""
        expected = '''### Table of Contents

        * 1.2.3 REQ001
    * 1.4 REQ003
    * 1.5 REQ006
    * 1.6 REQ004
    * 2.1 Plantuml
    * 2.1 REQ2-001\n'''
        toc = publisher._table_of_contents_md(self.document, linkify=None)
        print(toc)
        self.assertEqual(expected, toc)

    @patch('doorstop.settings.PUBLISH_HEADING_LEVELS', False)
    def test_toc_no_links(self):
        """Verify the table of contents is generated without heading levels"""
        expected = '''### Table of Contents

        * REQ001
    * REQ003
    * REQ006
    * REQ004
    * Plantuml
    * REQ2-001\n'''
        toc = publisher._table_of_contents_md(self.document, linkify=None)
        print(toc)
        self.assertEqual(expected, toc)

    def test_toc(self):
        """Verify the table of contents is generated with an ID for the heading"""
        expected = '''### Table of Contents

        * [1.2.3 REQ001](#REQ001)
    * [1.4 REQ003](#REQ003)
    * [1.5 REQ006](#REQ006)
    * [1.6 REQ004](#REQ004)
    * [2.1 Plantuml](#REQ002)
    * [2.1 REQ2-001](#REQ2-001)\n'''
        toc = publisher._table_of_contents_md(self.document, linkify=True)
        self.assertEqual(expected, toc)
