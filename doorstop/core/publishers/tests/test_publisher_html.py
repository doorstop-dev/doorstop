# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.core.publishers.html module."""

# pylint: disable=unused-argument,protected-access

import os
import unittest
from secrets import token_hex
from shutil import rmtree
from unittest import mock
from unittest.mock import ANY, MagicMock, Mock, call, patch

from doorstop.core import publisher
from doorstop.core.document import Document
from doorstop.core.template import HTMLTEMPLATE
from doorstop.core.tests import (
    EMPTY,
    FILES,
    ROOT,
    MockDataMixIn,
    MockDocument,
    MockItem,
)
from doorstop.core.types import UID


class TestModule(MockDataMixIn, unittest.TestCase):
    """Unit tests for the doorstop.core.publishers.html module."""

    # pylint: disable=no-value-for-parameter
    def setUp(self):
        """Setup test folder."""
        self.hex = token_hex()
        self.dirpath = os.path.abspath(os.path.join("mock_%s" % __name__, self.hex))

    @classmethod
    def tearDownClass(cls):
        """Remove test folder."""
        rmtree("mock_%s" % __name__)

    @patch("os.path.isdir", Mock(side_effect=[False, False, False, False]))
    @patch("os.makedirs")
    @patch("builtins.open")
    def test_publish_document(self, mock_open, mock_makedirs):
        """Verify a document can be published."""
        path = os.path.join(self.dirpath, "published.html")
        self.document.items = []
        # Act
        path2 = publisher.publish(self.document, path)
        # Assert
        self.assertIs(path, path2)
        mock_makedirs.assert_called_once_with(self.dirpath)
        mock_open.assert_called_once_with(path, "wb")

    @patch("os.path.isdir", Mock(return_value=False))
    @patch("os.makedirs")
    @patch("builtins.open")
    @patch("doorstop.core.publisher.publish_lines")
    def test_publish_document_html(self, mock_lines, mock_open, mock_makedirs):
        """Verify a (mock) HTML file can be created."""
        path = os.path.join(self.dirpath, "published.custom")
        # Act
        path2 = publisher.publish(self.document, path, ".html")
        # Assert
        self.assertIs(path, path2)
        mock_makedirs.assert_called_with(
            os.sep.join([self.dirpath, "published.custom", "documents"])
        )
        mock_open.assert_called_once_with(
            os.sep.join([path, "documents", "REQ.html"]), "wb"
        )
        mock_lines.assert_called_once_with(
            self.document,
            ".html",
            publisher=ANY,
            linkify=False,
            template=HTMLTEMPLATE,
            toc=True,
        )

    @patch("os.path.isdir", Mock(side_effect=[True, False, False, False, False, False]))
    @patch("os.remove")
    @patch("glob.glob")
    @patch("builtins.open")
    @patch("doorstop.core.publisher.publish_lines")
    def test_publish_document_deletes_the_contents_of_assets_folder(
        self, mock_lines, mock_open, mock_glob, mock_rm
    ):
        """Verify that the contents of an assets directory next to the published file is deleted"""
        path = os.path.join(self.dirpath, "published.custom")
        assets = [
            os.path.join(self.dirpath, Document.ASSETS, dir)
            for dir in ["css", "logo.png"]
        ]
        mock_glob.return_value = assets
        # Act
        path2 = publisher.publish(self.document, path, ".html")
        # Assert
        self.assertIs(path, path2)
        mock_open.assert_called_once_with(
            os.sep.join([path, "documents", "REQ.html"]), "wb"
        )
        mock_lines.assert_called_once_with(
            self.document,
            ".html",
            publisher=ANY,
            template=HTMLTEMPLATE,
            toc=True,
            linkify=False,
        )
        calls = [call(assets[0]), call(assets[1])]
        self.assertEqual(calls, mock_rm.call_args_list)

    @patch("os.path.isdir", Mock(return_value=False))
    @patch("doorstop.core.document.Document.copy_assets")
    @patch("os.makedirs")
    @patch("builtins.open")
    def test_publish_document_copies_assets(
        self, mock_open, mock_makedirs, mock_copyassets
    ):
        """Verify that assets are published"""
        assets_path = os.path.join(
            self.dirpath, "published.custom", "documents", "assets"
        )
        path = os.path.join(self.dirpath, "published.custom")
        document = MockDocument(os.sep.join(["some", "path"]))
        mock_open.side_effect = lambda *args, **kw: mock.mock_open(
            read_data="$body"
        ).return_value
        # Act
        path2 = publisher.publish(document, path, ".html")
        # Assert
        self.assertIs(path, path2)
        mock_makedirs.assert_called_with(
            os.sep.join([self.dirpath, "published.custom", "documents"])
        )
        mock_copyassets.assert_called_once_with(assets_path)

    def test_index(self):
        """Verify an HTML index can be created."""
        # Arrange
        path = os.path.join(FILES, "index.html")
        html_publisher = publisher.check(".html")
        # Act
        html_publisher.create_index(FILES)
        # Assert
        self.assertTrue(os.path.isfile(path))

    def test_index_no_files(self):
        """Verify an HTML index is only created when files exist."""
        path = os.path.join(EMPTY, "index.html")
        html_publisher = publisher.check(".html")
        # Act
        html_publisher.create_index(EMPTY)
        # Assert
        self.assertFalse(os.path.isfile(path))

    def test_index_tree(self):
        """Verify an HTML index can be created with a tree."""
        path = os.path.join(FILES, "index2.html")
        mock_tree = MagicMock()
        mock_tree.documents = []
        for prefix in ("SYS", "HLR", "LLR", "HLT", "LLT"):
            mock_document = MagicMock()
            mock_document.prefix = prefix
            mock_tree.documents.append(mock_document)
        mock_tree.draw = lambda: "(mock tree structure)"
        mock_item = Mock()
        mock_item.uid = "KNOWN-001"
        mock_item.document = Mock()
        mock_item.document.prefix = "KNOWN"
        mock_item.header = None
        mock_item_unknown = Mock(spec=["uid"])
        mock_item_unknown.uid = "UNKNOWN-002"
        mock_trace = [
            (None, mock_item, None, None, None),
            (None, None, None, mock_item_unknown, None),
            (None, None, None, None, None),
        ]
        mock_tree.get_traceability = lambda: mock_trace
        html_publisher = publisher.check(".html")
        # Act
        html_publisher.create_index(FILES, index="index2.html", tree=mock_tree)
        # Assert
        self.assertTrue(os.path.isfile(path))

    def test_matrix_tree(self):
        """Verify a traceability matrix can be created with a tree."""
        path = os.path.join(FILES, "testmatrix.csv")
        mock_tree = MagicMock()
        mock_tree.documents = []
        for prefix in ("SYS", "HLR", "LLR", "HLT", "LLT"):
            mock_document = MagicMock()
            mock_document.prefix = prefix
            mock_tree.documents.append(mock_document)
        mock_tree.draw = lambda: "(mock tree structure)"
        mock_item = Mock()
        mock_item.uid = "KNOWN-001"
        mock_item.document = Mock()
        mock_item.document.prefix = "KNOWN"
        mock_item.header = None
        mock_item_unknown = Mock(spec=["uid"])
        mock_item_unknown.uid = "UNKNOWN-002"
        mock_trace = [
            (None, mock_item, None, None, None),
            (None, None, None, mock_item_unknown, None),
            (None, None, None, None, None),
        ]
        mock_tree.get_traceability = lambda: mock_trace
        html_publisher = publisher.check(".html", obj=mock_tree)
        # Create the self.dirpath first.
        os.makedirs(self.dirpath)
        # Act
        html_publisher.create_matrix(self.dirpath)
        # Assert
        result_file = os.path.join(self.dirpath, "traceability.csv")
        self.assertTrue(os.path.isfile(result_file))
        # Assert contents of FILES and traceability.csv
        with open(result_file, "r") as file:
            result_content = file.read()
        with open(path, "r") as file:
            expected_content = file.read()
        self.assertEqual(expected_content, result_content)

    def test_lines_html_item(self):
        """Verify HTML can be published from an item."""
        expected = """<h2 id="req3">1.1 Heading</h2>
<p>Heading</p>
<p><em>Parent links: {}</em></p>
""".format(
            self.item.parent_items[0].uid
        )
        # Act
        lines = publisher.publish_lines(self.item, ".html")
        text = "".join(line + "\n" for line in lines)
        # Assert
        self.assertEqual(expected, text)

    @patch("doorstop.settings.PUBLISH_HEADING_LEVELS", False)
    def test_lines_html_item_no_heading_levels(self):
        """Verify an item heading level can be omitted."""
        expected = """<h2 id="req3">Heading</h2>
<p>Heading</p>
<p><em>Parent links: {}</em></p>
""".format(
            self.item.parent_items[0].uid
        )

        # Act
        lines = publisher.publish_lines(self.item, ".html")
        text = "".join(line + "\n" for line in lines)
        # Assert
        self.assertEqual(expected, text)

    def test_lines_html_item_linkify(self):
        """Verify HTML (hyper) can be published from an item."""
        expected = """<h2 id="req3">1.1 Heading</h2>
<p>Heading</p>
<p><em>Parent links:</em> <a href="\\{p}.html#\\{u}">{u} {h}</a></p>
""".format(
            u=self.item.parent_items[0].uid,
            h=self.item.parent_items[0].header,
            p=self.item.parent_items[0].document.prefix,
        )
        # Act
        lines = publisher.publish_lines(self.item, ".html", linkify=True)
        text = "".join(line + "\n" for line in lines)
        # Assert
        self.assertEqual(expected, text)

    @patch("doorstop.settings.PUBLISH_CHILD_LINKS", True)
    def test_lines_html_item_with_child_links(self):
        """Verify HTML can be published from an item w/ child links."""
        # Act
        lines = publisher.publish_lines(self.item2, ".html")
        text = "".join(line + "\n" for line in lines)
        # Assert
        self.assertIn("Child links: tst1", text)

    @patch("doorstop.settings.PUBLISH_CHILD_LINKS", False)
    def test_lines_html_item_without_child_links(self):
        """Verify HTML can be published from an item w/o child links."""
        # Act
        lines = publisher.publish_lines(self.item2, ".html")
        text = "".join(line + "\n" for line in lines)
        # Assert
        self.assertNotIn("Child links", text)

    @patch("doorstop.settings.PUBLISH_CHILD_LINKS", True)
    def test_lines_html_item_with_child_links_linkify(self):
        """Verify HTML (hyper) can be published from an item w/ child links."""
        # Act
        lines = publisher.publish_lines(self.item2, ".html", linkify=True)
        text = "".join(line + "\n" for line in lines)
        # Assert
        self.assertIn("Child links:", text)
        self.assertIn("tst.html#tst1", text)

    @patch("os.path.isdir", Mock(side_effect=[False, False, False, False]))
    @patch("os.makedirs")
    @patch("builtins.open")
    def test_publish_document(self, mock_open, mock_makedirs):
        """Verify a document can be published."""
        path = os.path.join(self.dirpath, "published.html")
        self.document.items = []
        # Act
        path2 = publisher.publish(self.document, path)
        # Assert
        self.assertIs(path, path2)
        mock_makedirs.assert_called_with(os.sep.join([self.dirpath, "documents"]))
        mock_open.assert_called_once_with(
            os.sep.join([os.path.dirname(path), "documents", "published.html"]), "wb"
        )


@patch("doorstop.core.item.Item", MockItem)
class TestTableOfContents(unittest.TestCase):
    """Unit tests for the Document class."""

    def setUp(self):
        self.document = MockDocument(FILES, root=ROOT)

    def test_toc_no_links_or_heading_levels(self):
        """Verify the table of contents is generated with heading levels"""
        expected = [
            {"depth": 0, "text": "Table of Contents", "uid": "toc"},
            {"depth": 3, "text": "1.2.3 REQ001", "uid": ""},
            {"depth": 2, "text": "1.4 REQ003", "uid": ""},
            {"depth": 2, "text": "1.5 REQ006", "uid": ""},
            {"depth": 2, "text": "1.6 REQ004", "uid": ""},
            {"depth": 2, "text": "2.1 Plantuml", "uid": ""},
            {"depth": 2, "text": "2.1 REQ2-001", "uid": ""},
        ]
        html_publisher = publisher.check(".html", self.document)
        toc = html_publisher.table_of_contents(linkify=None, obj=self.document)
        self.assertEqual(expected, toc)

    @patch("doorstop.settings.PUBLISH_HEADING_LEVELS", False)
    def test_toc_no_links(self):
        """Verify the table of contents is generated without heading levels"""
        expected = [
            {"depth": 0, "text": "Table of Contents", "uid": "toc"},
            {"depth": 3, "text": UID("REQ001"), "uid": ""},
            {"depth": 2, "text": UID("REQ003"), "uid": ""},
            {"depth": 2, "text": UID("REQ006"), "uid": ""},
            {"depth": 2, "text": UID("REQ004"), "uid": ""},
            {"depth": 2, "text": "Plantuml", "uid": ""},
            {"depth": 2, "text": UID("REQ2-001"), "uid": ""},
        ]

        html_publisher = publisher.check(".html", self.document)
        toc = html_publisher.table_of_contents(linkify=None, obj=self.document)
        self.assertEqual(expected, toc)

    def test_toc(self):
        """Verify the table of contents is generated with an ID for the heading"""
        expected = [
            {"depth": 0, "text": "Table of Contents", "uid": "toc"},
            {"depth": 3, "text": "1.2.3 REQ001", "uid": UID("REQ001")},
            {"depth": 2, "text": "1.4 REQ003", "uid": UID("REQ003")},
            {"depth": 2, "text": "1.5 REQ006", "uid": UID("REQ006")},
            {"depth": 2, "text": "1.6 REQ004", "uid": UID("REQ004")},
            {"depth": 2, "text": "2.1 Plantuml", "uid": UID("REQ002")},
            {"depth": 2, "text": "2.1 REQ2-001", "uid": UID("REQ2-001")},
        ]
        html_publisher = publisher.check(".html", self.document)
        toc = html_publisher.table_of_contents(linkify=True, obj=self.document)
        self.assertEqual(expected, toc)
