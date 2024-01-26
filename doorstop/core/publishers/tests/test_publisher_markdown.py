# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.core.publishers.markdown module."""

# pylint: disable=unused-argument,protected-access

import os
import unittest
from secrets import token_hex
from shutil import rmtree
from unittest.mock import Mock, patch

from doorstop.core import publisher
from doorstop.core.publishers.tests.helpers import YAML_CUSTOM_ATTRIBUTES, getLines
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

    @patch("doorstop.settings.PUBLISH_CHILD_LINKS", False)
    def test_lines_markdown_item_normative(self):
        """Verify Markdown can be published from an item (normative)."""
        expected = (
            "## 1.2 req4 {#req4}" + "\n\n"
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
            "## req4 {#req4}" + "\n\n"
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
            "# 1.0 Header name {#REQ-001}"
            + "\n\n"
            + "Test of a single text line."
            + "\n\n"
        )
        # Act
        result = getLines(publisher.publish_lines(item, ".md"))
        # Assert
        self.assertEqual(expected, result)

    @patch("doorstop.settings.ENABLE_HEADERS", False)
    def test_setting_enable_headers_false(self):
        """Verify that the settings.ENABLE_HEADERS changes the output appropriately when False."""
        generated_data = (
            r"active: true" + "\n"
            r"derived: false" + "\n"
            r"header: 'Header name'" + "\n"
            r"level: 1.0" + "\n"
            r"normative: true" + "\n"
            r"reviewed:" + "\n"
            r"text: |" + "\n"
            r"  Test of a single text line."
        )
        item = MockItemAndVCS(
            "path/to/REQ-001.yml",
            _file=generated_data,
        )
        expected = (
            "# 1.0 REQ-001 {#REQ-001}" + "\n\n" + "Test of a single text line." + "\n\n"
        )
        # Act
        result = getLines(publisher.publish_lines(item, ".md"))
        # Assert
        self.assertEqual(expected, result)

    def test_custom_attributes(self):
        """Verify that custom attributes are published correctly."""
        # Setup
        generated_data = (
            r"CUSTOM-ATTRIB: true" + "\n"
            r"invented-by: jane@example.com" + "\n"
            r"text: |" + "\n"
            r"  Test of custom attributes."
        )
        document = MockDocument("/some/path")
        document._file = YAML_CUSTOM_ATTRIBUTES
        document.load(reload=True)
        itemPath = os.path.join("path", "to", "REQ-001.yml")
        item = MockItem(document, itemPath)
        item._file = generated_data
        item.load(reload=True)
        document._items.append(item)
        expected = (
            "# 1.0 REQ-001 {#REQ-001}"
            + "\n\n"
            + "Test of custom attributes."
            + "\n\n"
            + "| Attribute | Value |"
            + "\n"
            + "| --------- | ----- |"
            + "\n"
            + "| CUSTOM-ATTRIB | True |"
            + "\n"
            + "| invented-by | jane@example.com |"
            + "\n"
            + "\n\n"
        )
        # Act
        result = getLines(publisher.publish_lines(document, ".md"))
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
        toc = md_publisher.table_of_contents(linkify=None, obj=self.document)
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
        toc = md_publisher.table_of_contents(linkify=None, obj=self.document)
        self.assertEqual(expected, toc)

    def test_toc(self):
        """Verify the table of contents is generated with an ID for the heading"""
        expected = """### Table of Contents

        * [1.2.3 REQ001](#123-req001-req001)
    * [1.4 REQ003](#14-req003-req003)
    * [1.5 REQ006](#15-req006-req006)
    * [1.6 REQ004](#16-req004-req004)
    * [2.1 Plantuml](#21-plantuml-req002-req002)
    * [2.1 REQ2-001](#21-req2-001-req2-001)\n"""
        self.maxDiff = None
        md_publisher = publisher.check(".md", self.document)
        toc = md_publisher.table_of_contents(linkify=True, obj=self.document)
        self.assertEqual(expected, toc)
