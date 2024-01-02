# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.core.publishers.markdown module."""

# pylint: disable=unused-argument,protected-access

import os
import unittest
from secrets import token_hex
from shutil import rmtree
from unittest.mock import Mock, patch

from doorstop.core import publisher
from doorstop.core.publishers.tests.helpers import getLines
from doorstop.core.tests import (
    FILES,
    ROOT,
    MockDataMixIn,
    MockDocument,
    MockItem,
    MockItemAndVCS,
)


class TestModule(MockDataMixIn, unittest.TestCase):
    """Unit tests for the doorstop.core.publishers.markdown module."""

    # pylint: disable=no-value-for-parameter
    def setUp(self):
        """Setup test folder."""
        self.hex = token_hex()
        self.dirpath = os.path.abspath(os.path.join("mock_%s" % __name__, self.hex))

    @classmethod
    def tearDownClass(cls):
        """Remove test folder."""
        if os.path.exists("mock_%s" % __name__):
            rmtree("mock_%s" % __name__)

    def test_single_line_heading_to_markdown(self):
        """Verify a single line heading is published as a heading with an attribute equal to the item id"""
        expected = "## 1.1 Heading {#req3 }\n\n"
        lines = publisher.publish_lines(self.item, ".md", linkify=True)
        # Act
        text = "".join(line + "\n" for line in lines)
        # Assert
        self.assertEqual(expected, text)

    def test_multi_line_heading_to_markdown(self):
        """Verify a multi line heading is published as a heading with an attribute equal to the item id"""
        item = MockItemAndVCS(
            "path/to/req3.yml",
            _file=(
                "links: [sys3]" + "\n"
                "text: 'Heading\n\nThis section describes publishing.'" + "\n"
                "level: 1.1.0" + "\n"
                "normative: false"
            ),
        )
        expected = "## 1.1 Heading {#req3 }\nThis section describes publishing.\n\n"
        lines = publisher.publish_lines(item, ".md", linkify=True)
        # Act
        text = "".join(line + "\n" for line in lines)
        # Assert
        self.assertEqual(expected, text)

    @patch("doorstop.settings.PUBLISH_HEADING_LEVELS", False)
    def test_multi_line_heading_to_markdown_no_heading_levels(self):
        """Verify a multi line heading is published as a heading, without level, with an attribute equal to the item id"""
        item = MockItemAndVCS(
            "path/to/req3.yml",
            _file=(
                "links: [sys3]" + "\n"
                "text: 'Heading\n\nThis section describes publishing.'" + "\n"
                "level: 1.1.0" + "\n"
                "normative: false"
            ),
        )
        expected = "## Heading {#req3 }\nThis section describes publishing.\n\n"
        lines = publisher.publish_lines(item, ".md", linkify=True)
        # Act
        text = "".join(line + "\n" for line in lines)
        # Assert
        self.assertEqual(expected, text)

    def test_lines_markdown_item(self):
        """Verify Markdown can be published from an item."""
        with patch.object(
            self.item5, "find_ref", Mock(return_value=("path/to/mock/file", 42))
        ):
            lines = publisher.publish_lines(self.item5, ".md")
            text = "".join(line + "\n" for line in lines)
        self.assertIn("> `path/to/mock/file` (line 42)", text)

    def test_lines_markdown_item_references(self):
        """Verify Markdown can be published from an item."""
        references_mock = [("path/to/mock/file1", 3), ("path/to/mock/file2", None)]

        with patch.object(
            self.item6, "find_references", Mock(return_value=references_mock)
        ):
            lines = publisher.publish_lines(self.item6, ".md")
            text = "".join(line + "\n" for line in lines)
        self.assertIn("> `path/to/mock/file1` (line 3)\n> `path/to/mock/file2`", text)

    def test_lines_markdown_item_heading(self):
        """Verify Markdown can be published from an item (heading)."""
        expected = "## 1.1 Heading {#req3 }\n\n"
        # Act
        lines = publisher.publish_lines(self.item, ".md", linkify=True)
        text = "".join(line + "\n" for line in lines)
        # Assert
        self.assertEqual(expected, text)

    @patch("doorstop.settings.PUBLISH_HEADING_LEVELS", False)
    def test_lines_markdown_item_heading_no_heading_levels(self):
        """Verify an item heading level can be ommitted."""
        expected = "## Heading {#req3 }\n\n"
        # Act
        lines = publisher.publish_lines(self.item, ".md", linkify=True)
        text = "".join(line + "\n" for line in lines)
        # Assert
        self.assertEqual(expected, text)

    @patch("doorstop.settings.PUBLISH_CHILD_LINKS", False)
    def test_lines_markdown_item_normative(self):
        """Verify Markdown can be published from an item (normative)."""
        expected = (
            "## 1.2 req4 {#req4 }" + "\n\n"
            "This shall..." + "\n\n"
            "> `Doorstop.sublime-project`" + "\n\n"
            "*Links: sys4*" + "\n\n"
        )
        # Act
        lines = publisher.publish_lines(self.item3, ".md", linkify=False)
        text = "".join(line + "\n" for line in lines)
        # Assert
        self.assertEqual(expected, text)

    @patch("doorstop.settings.PUBLISH_CHILD_LINKS", True)
    def test_lines_markdown_item_with_child_links(self):
        """Verify Markdown can be published from an item w/ child links."""
        # Act
        lines = publisher.publish_lines(self.item2, ".md")
        text = "".join(line + "\n" for line in lines)
        # Assert
        self.assertIn("Child links: tst1", text)

    @patch("doorstop.settings.PUBLISH_CHILD_LINKS", False)
    def test_lines_markdown_item_without_child_links(self):
        """Verify Markdown can be published from an item w/o child links."""
        # Act
        lines = publisher.publish_lines(self.item2, ".md")
        text = "".join(line + "\n" for line in lines)
        # Assert
        self.assertNotIn("Child links", text)

    @patch("doorstop.settings.PUBLISH_BODY_LEVELS", False)
    @patch("doorstop.settings.PUBLISH_CHILD_LINKS", False)
    def test_lines_markdown_item_without_body_levels(self):
        """Verify Markdown can be published from an item (no body levels)."""
        expected = (
            "## req4 {#req4 }" + "\n\n"
            "This shall..." + "\n\n"
            "> `Doorstop.sublime-project`" + "\n\n"
            "*Links: sys4*" + "\n\n"
        )
        # Act
        lines = publisher.publish_lines(self.item3, ".md", linkify=False)
        text = "".join(line + "\n" for line in lines)
        # Assert
        self.assertEqual(expected, text)

    @patch("doorstop.settings.CHECK_REF", False)
    def test_lines_markdown_item_no_ref_check(self):
        """Verify Markdown can be published without checking references."""
        lines = publisher.publish_lines(self.item5, ".md")
        text = "".join(line + "\n" for line in lines)
        self.assertIn("> 'abc123'", text)

    @patch("doorstop.settings.CHECK_REF", False)
    def test_lines_markdown_item_no_references_check(self):
        """Verify Markdown can be published without checking references."""
        lines = publisher.publish_lines(self.item6, ".md")
        text = "".join(line + "\n" for line in lines)
        self.assertIn("> 'abc1'\n> 'abc2'", text)

    @patch("doorstop.settings.ENABLE_HEADERS", True)
    def test_setting_enable_headers_true(self):
        """Verify that the settings.ENABLE_HEADERS changes the output appropriately when True."""
        generated_data = (
            r"active: true" + "\n"
            r"derived: false" + "\n"
            r"header: 'Header name'" + "\n"
            r"level: 1.0" + "\n"
            r"normative: false" + "\n"
            r"reviewed:" + "\n"
            r"text: |" + "\n"
            r"  Test of a single text line."
        )
        item = MockItemAndVCS(
            "path/to/REQ-001.yml",
            _file=generated_data,
        )
        expected = (
            "# 1.0 Header name {#REQ-001 }"
            + "\n"
            + "Test of a single text line."
            + "\n\n"
        )
        # Act
        result = getLines(publisher.publish_lines(item, ".md"))
        # Assert
        self.assertEqual(expected, result)


@patch("doorstop.core.item.Item", MockItem)
class TestTableOfContents(unittest.TestCase):
    """Unit tests for the Document class."""

    def setUp(self):
        self.document = MockDocument(FILES, root=ROOT)

    def test_toc_no_links_or_heading_levels(self):
        """Verify the table of contents is generated with heading levels"""
        expected = """### Table of Contents

        * 1.2.3 REQ001
    * 1.4 REQ003
    * 1.5 REQ006
    * 1.6 REQ004
    * 2.1 Plantuml
    * 2.1 REQ2-001\n"""
        md_publisher = publisher.check(".md", self.document)
        toc = md_publisher.table_of_contents(linkify=None)
        self.assertEqual(expected, toc)

    @patch("doorstop.settings.PUBLISH_HEADING_LEVELS", False)
    def test_toc_no_links(self):
        """Verify the table of contents is generated without heading levels"""
        expected = """### Table of Contents

        * REQ001
    * REQ003
    * REQ006
    * REQ004
    * Plantuml
    * REQ2-001\n"""
        md_publisher = publisher.check(".md", self.document)
        toc = md_publisher.table_of_contents(linkify=None)
        self.assertEqual(expected, toc)

    def test_toc(self):
        """Verify the table of contents is generated with an ID for the heading"""
        expected = """### Table of Contents

        * [1.2.3 REQ001](#REQ001)
    * [1.4 REQ003](#REQ003)
    * [1.5 REQ006](#REQ006)
    * [1.6 REQ004](#REQ004)
    * [2.1 Plantuml](#REQ002)
    * [2.1 REQ2-001](#REQ2-001)\n"""
        md_publisher = publisher.check(".md", self.document)
        toc = md_publisher.table_of_contents(linkify=True)
        self.assertEqual(expected, toc)
