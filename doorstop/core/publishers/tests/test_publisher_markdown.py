# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.core.publishers.markdown module."""

# pylint: disable=unused-argument,protected-access

import os
import unittest
from secrets import token_hex
from shutil import rmtree
from unittest.mock import MagicMock, Mock, patch

from doorstop.core import publisher
from doorstop.core.publishers.markdown import MarkdownPublisher
from doorstop.core.publishers.tests.helpers import (
    YAML_COMBINED_LABEL_ATTRIBUTES,
    YAML_CUSTOM_ATTRIBUTES,
    YAML_INVALID_PUBLISH_ENTRY,
    YAML_LIST_ATTRIBUTE,
    YAML_SINGLE_ATTRIBUTE,
    YAML_STRUCTURED_ATTRIBUTES,
    getLines,
)
from doorstop.core.tests import (
    EMPTY,
    FILES,
    ROOT,
    MockDataMixIn,
    MockDocument,
    MockItem,
    MockItemAndVCS,
)
from doorstop.core.tests.helpers import on_error_with_retry
from doorstop.core.types import UID


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
            rmtree("mock_%s" % __name__, onerror=on_error_with_retry)

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

        * 1.2.3 Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod (REQ001)
    * 1.4 Unicode: -40° ±1% (REQ003)
    * 1.5 Hello, world! (REQ006)
    * 1.6 Hello, world! (REQ004)
    * 2.1 Plantuml (REQ002)
    * 2.1 Hello, world! (REQ2-001)
 * 3.0 My Heading\n"""
        md_publisher = publisher.check(".md", self.document)
        toc = md_publisher.table_of_contents(linkify=None, obj=self.document)
        self.assertEqual(expected, toc)

    @patch("doorstop.settings.PUBLISH_HEADING_LEVELS", False)
    def test_toc_no_links(self):
        """Verify the table of contents is generated without heading levels"""
        expected = """### Table of Contents

        * Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod (REQ001)
    * Unicode: -40° ±1% (REQ003)
    * Hello, world! (REQ006)
    * Hello, world! (REQ004)
    * Plantuml (REQ002)
    * Hello, world! (REQ2-001)
 * My Heading
"""
        md_publisher = publisher.check(".md", self.document)
        toc = md_publisher.table_of_contents(linkify=None, obj=self.document)
        self.assertEqual(expected, toc)

    def test_toc(self):
        """Verify the table of contents is generated with an ID for the heading"""
        expected = """### Table of Contents

        * [1.2.3 Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod (REQ001)](#123-req001-req001)
    * [1.4 Unicode: -40° ±1% (REQ003)](#14-req003-req003)
    * [1.5 Hello, world! (REQ006)](#15-req006-req006)
    * [1.6 Hello, world! (REQ004)](#16-req004-req004)
    * [2.1 Plantuml (REQ002)](#21-plantuml-req002-req002)
    * [2.1 Hello, world! (REQ2-001)](#21-req2-001-req2-001)
 * [3.0 My Heading](#30-my-heading-req007)\n"""
        self.maxDiff = None
        md_publisher = publisher.check(".md", self.document)
        toc = md_publisher.table_of_contents(linkify=True, obj=self.document)
        self.assertEqual(expected, toc)

    def test_index(self):
        """Verify an Markdown index can be created."""
        # Arrange
        path = os.path.join(FILES, "index.md")
        md_publisher = publisher.check(".md")
        # Act
        md_publisher.create_index(FILES)
        # Assert
        self.assertTrue(os.path.isfile(path))

    def test_index_no_files(self):
        """Verify an Markdown index is only created when files exist."""
        path = os.path.join(EMPTY, "index.md")
        md_publisher = publisher.check(".md")
        # Act
        md_publisher.create_index(EMPTY)
        # Assert
        self.assertFalse(os.path.isfile(path))

    def test_index_tree(self):
        """Verify an Markdown index can be created with a tree."""
        path = os.path.join(FILES, "index2.md")
        all_documents = []
        all_trees = []
        for prefix in ("SYS", "HLR", "LLR", "HLT", "LLT"):
            mock_document = MagicMock()
            mock_document._attribute_defaults = {
                "doc": {"title": f"The {prefix} document for Doorstop"}
            }
            mock_document.prefix = prefix
            all_documents.append(mock_document)

            tree = MagicMock()
            tree.document = mock_document
            tree.children = []
            all_trees.append(tree)

        mock_tree = all_trees[0]  # pick "SYS" as top-level tree
        mock_tree.children = all_trees[1:]
        mock_tree.documents = all_documents
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
        mock_tree.get_traceability = lambda **_: mock_trace
        md_publisher = publisher.check(".md")
        # Act
        md_publisher.create_index(FILES, index="index2.md", tree=mock_tree)
        # Assert
        self.assertTrue(os.path.isfile(path))


class TestParsePublishEntry(unittest.TestCase):
    """Unit tests for MarkdownPublisher._parse_publish_entry()."""

    def test_string_entry(self):
        """Simple string entry returns attr with no fields."""
        result = MarkdownPublisher._parse_publish_entry("invented-by")
        self.assertEqual(result, {"attr": "invented-by", "fields": None})

    def test_dict_entry_with_fields(self):
        """Dict entry with attribute name as key and fields is parsed correctly."""
        entry = {"spec-refs-from": {"fields": [{"url": "section"}]}}
        result = MarkdownPublisher._parse_publish_entry(entry)
        self.assertEqual(
            result, {"attr": "spec-refs-from", "fields": [{"url": "section"}]}
        )

    def test_dict_entry_without_fields(self):
        """Dict entry without fields returns fields=None."""
        entry = {"spec-refs-from": {}}
        result = MarkdownPublisher._parse_publish_entry(entry)
        self.assertEqual(result, {"attr": "spec-refs-from", "fields": None})

    def test_dict_entry_missing_attr(self):
        """Dict entry with None config returns fields=None."""
        entry = {"spec-refs-from": None}
        result = MarkdownPublisher._parse_publish_entry(entry)
        self.assertEqual(result, {"attr": "spec-refs-from", "fields": None})

    def test_invalid_entry_returns_none(self):
        """Non-string, non-dict entry returns None."""
        self.assertIsNone(MarkdownPublisher._parse_publish_entry(42))
        self.assertIsNone(MarkdownPublisher._parse_publish_entry(None))
        self.assertIsNone(MarkdownPublisher._parse_publish_entry(["list"]))


class TestRenderFields(unittest.TestCase):
    """Unit tests for MarkdownPublisher._render_fields()."""

    def setUp(self):
        self.refs = [
            {
                "file": "specs/login.md",
                "section": "3.1 Login Process",
                "anchor": "31-login-process",
                "url": "https://gitlab.com/group/project/-/blob/main/specs/login.md#31-login-process",
            },
            {
                "file": "specs/session.md",
                "section": "3.2 Session Management",
                "anchor": "32-session-management",
                "url": "https://gitlab.com/group/project/-/blob/main/specs/session.md#32-session-management",
            },
        ]

    def test_single_ref_link(self):
        """Single ref with url:section renders as Markdown link."""
        fields = [{"url": "section"}]
        result = MarkdownPublisher._render_fields(self.refs[:1], fields)
        self.assertEqual(
            result,
            "[3.1 Login Process](https://gitlab.com/group/project/-/blob/main/specs/login.md#31-login-process)",
        )

    def test_multiple_refs_joined_with_br(self):
        """Multiple refs are joined with <br>."""
        fields = [{"url": "section"}]
        result = MarkdownPublisher._render_fields(self.refs, fields)
        self.assertIn("<br>", result)
        parts = result.split("<br>")
        self.assertEqual(len(parts), 2)
        self.assertIn("3.1 Login Process", parts[0])
        self.assertIn("3.2 Session Management", parts[1])

    def test_plain_text_field(self):
        """Plain string field renders as plain text value."""
        fields = ["section"]
        result = MarkdownPublisher._render_fields(self.refs[:1], fields)
        self.assertEqual(result, "3.1 Login Process")

    def test_missing_url_renders_label_only(self):
        """Missing url field renders label text without link."""
        refs = [{"section": "3.1 Login Process"}]
        fields = [{"url": "section"}]
        result = MarkdownPublisher._render_fields(refs, fields)
        self.assertEqual(result, "3.1 Login Process")

    def test_missing_field_renders_empty_string(self):
        """Missing plain field renders empty string."""
        refs = [{"section": "3.1 Login Process"}]
        fields = ["nonexistent"]
        result = MarkdownPublisher._render_fields(refs, fields)
        self.assertEqual(result, "")

    def test_url_stripped_of_whitespace(self):
        """URL with trailing newline (YAML literal block) is stripped."""
        refs = [
            {
                "section": "Stop Functions",
                "url": "https://gitlab.com/group/project#stop-functions\n",
            }
        ]
        fields = [{"url": "section"}]
        result = MarkdownPublisher._render_fields(refs, fields)
        self.assertNotIn("\n", result)
        self.assertIn("https://gitlab.com/group/project#stop-functions", result)

    def test_empty_refs_returns_empty_string(self):
        """Empty refs list returns empty string."""
        result = MarkdownPublisher._render_fields([], [{"url": "section"}])
        self.assertEqual(result, "")

    def test_multiple_fields_per_ref(self):
        """Multiple fields per ref are joined with space."""
        fields = ["section", "anchor"]
        result = MarkdownPublisher._render_fields(self.refs[:1], fields)
        self.assertEqual(result, "3.1 Login Process 31-login-process")

    def test_combined_label_default_separator(self):
        """Combined label with default separator ': '."""
        refs = [
            {
                "file": "System_Safety_Concept.md",
                "section": "Stop Functions",
                "url": "https://gitlab.com/group/project/-/blob/main/specs/safety.md#stop-functions",
            }
        ]
        fields = [{"url": {"label": ["file", "section"], "separator": ": "}}]
        result = MarkdownPublisher._render_fields(refs, fields)
        self.assertEqual(
            result,
            "[System_Safety_Concept.md: Stop Functions](https://gitlab.com/group/project/-/blob/main/specs/safety.md#stop-functions)",
        )

    def test_combined_label_custom_separator(self):
        """Combined label with custom separator ' § '."""
        refs = [
            {
                "section": "Stop Functions",
                "anchor": "stop-functions",
                "url": "https://gitlab.com/group/project/-/blob/main/specs/safety.md#stop-functions",
            }
        ]
        fields = [{"url": {"label": ["section", "anchor"], "separator": " § "}}]
        result = MarkdownPublisher._render_fields(refs, fields)
        self.assertEqual(
            result,
            "[Stop Functions § stop-functions](https://gitlab.com/group/project/-/blob/main/specs/safety.md#stop-functions)",
        )

    def test_combined_label_missing_field_skipped(self):
        """Missing field in combined label is skipped gracefully."""
        refs = [
            {
                "section": "Stop Functions",
                "url": "https://gitlab.com/group/project/-/blob/main/specs/safety.md#stop-functions",
            }
        ]
        # 'file' fehlt – nur 'section' soll im Label erscheinen
        fields = [{"url": {"label": ["file", "section"], "separator": ": "}}]
        result = MarkdownPublisher._render_fields(refs, fields)
        self.assertEqual(
            result,
            "[Stop Functions](https://gitlab.com/group/project/-/blob/main/specs/safety.md#stop-functions)",
        )

    def test_combined_label_single_field_in_list(self):
        """Single field in label list behaves like simple label."""
        refs = [
            {
                "section": "Stop Functions",
                "url": "https://gitlab.com/group/project/-/blob/main/specs/safety.md#stop-functions",
            }
        ]
        fields = [{"url": {"label": ["section"], "separator": ": "}}]
        result = MarkdownPublisher._render_fields(refs, fields)
        self.assertEqual(
            result,
            "[Stop Functions](https://gitlab.com/group/project/-/blob/main/specs/safety.md#stop-functions)",
        )

    def test_combined_label_no_url_renders_text_only(self):
        """Combined label without URL renders plain text."""
        refs = [
            {
                "file": "System_Safety_Concept.md",
                "section": "Stop Functions",
            }
        ]
        fields = [{"url": {"label": ["file", "section"], "separator": ": "}}]
        result = MarkdownPublisher._render_fields(refs, fields)
        self.assertEqual(result, "System_Safety_Concept.md: Stop Functions")

    def test_combined_label_multiple_refs_joined_with_br(self):
        """Multiple refs with combined labels are joined with <br>."""
        fields = [{"url": {"label": ["file", "section"], "separator": ": "}}]
        result = MarkdownPublisher._render_fields(self.refs, fields)
        parts = result.split("<br>")
        self.assertEqual(len(parts), 2)
        self.assertIn("specs/login.md: 3.1 Login Process", parts[0])
        self.assertIn("specs/session.md: 3.2 Session Management", parts[1])

    def test_label_spec_invalid_type_uses_url_key(self):
        """label_spec neither str nor dict → label falls back to url_key."""
        refs = [
            {
                "url": "https://gitlab.com/group/project/-/blob/main/specs/safety.md#stop-functions",
            }
        ]
        # label_spec is an int – neither str nor dict → else branch → label = url_key
        fields = [{"url": 42}]
        result = MarkdownPublisher._render_fields(refs, fields)
        self.assertEqual(
            result,
            "[url](https://gitlab.com/group/project/-/blob/main/specs/safety.md#stop-functions)",
        )

    def test_combined_label_no_url_appends_label_without_link(self):
        """url empty with combined label → plain text, no link tag."""
        refs = [
            {
                "file": "System_Safety_Concept.md",
                "section": "Stop Functions",
                # url intentionally missing → empty string after .get()
            }
        ]
        fields = [{"url": {"label": ["file", "section"], "separator": ": "}}]
        result = MarkdownPublisher._render_fields(refs, fields)
        # No link – only combined label text
        self.assertEqual(result, "System_Safety_Concept.md: Stop Functions")
        self.assertNotIn("](", result)


class TestPublishLinesCustomAttributesExtended(unittest.TestCase):
    """Integration tests for modified _lines_markdown() custom attribute handling."""

    def _make_item(self, document_yaml: str, item_data: str) -> tuple:
        """Helper: create MockDocument + MockItem from YAML strings."""
        document = MockDocument("/some/path")
        document._file = document_yaml
        document.load(reload=True)
        item_path = os.path.join("path", "to", "REQ-001.yml")
        item = MockItem(document, item_path)
        item._file = item_data
        item.load(reload=True)
        document._items.append(item)
        return document, item

    def test_invalid_publish_entry_attr_none_is_skipped(self):
        """entry with attr=None is skipped gracefully."""
        # attr is None → _parse_publish_entry returns {'attr': None, ...}
        # → 'if not attr: continue' must be hit
        item_data = r"type: functional" + "\n" r"text: |" + "\n" r"  Some text."
        document, item = self._make_item(YAML_INVALID_PUBLISH_ENTRY, item_data)
        # Must not raise, must not produce attribute table
        result = getLines(publisher.publish_lines(document, ".md"))
        self.assertNotIn("| Attribute | Value |", result)

    def test_structured_attribute_renders_as_link(self):
        """list-of-dicts with fields renders via _render_fields()."""
        item_data = (
            r"type: functional" + "\n"
            r"spec-refs-from:" + "\n"
            r"  - file: specs/login.md" + "\n"
            r"    section: '3.1 Login Process'" + "\n"
            r"    anchor: 31-login-process" + "\n"
            r"    url: https://gitlab.com/group/project/-/blob/main/specs/login.md#31-login-process"
            + "\n"
            r"text: |" + "\n"
            r"  Some text."
        )
        document, item = self._make_item(YAML_STRUCTURED_ATTRIBUTES, item_data)
        result = getLines(publisher.publish_lines(document, ".md"))
        # Table header present
        self.assertIn("| Attribute | Value |", result)
        # Rendered as Markdown link via _render_fields()
        self.assertIn(
            "| spec-refs-from | [3.1 Login Process](https://gitlab.com/group/project/-/blob/main/specs/login.md#31-login-process) |",
            result,
        )
        # Must NOT contain raw dict dump
        self.assertNotIn("'file'", result)

    def test_structured_attribute_multiple_entries_joined_with_br(self):
        """multiple list-of-dicts entries joined with <br>."""
        item_data = (
            r"type: functional" + "\n"
            r"spec-refs-from:" + "\n"
            r"  - file: specs/login.md" + "\n"
            r"    section: '3.1 Login Process'" + "\n"
            r"    anchor: 31-login-process" + "\n"
            r"    url: https://gitlab.com/group/project/-/blob/main/specs/login.md#31-login-process"
            + "\n"
            r"  - file: specs/session.md" + "\n"
            r"    section: '3.2 Session Management'" + "\n"
            r"    anchor: 32-session-management" + "\n"
            r"    url: https://gitlab.com/group/project/-/blob/main/specs/session.md#32-session-management"
            + "\n"
            r"text: |" + "\n"
            r"  Some text."
        )
        document, item = self._make_item(YAML_STRUCTURED_ATTRIBUTES, item_data)
        result = getLines(publisher.publish_lines(document, ".md"))
        self.assertIn("<br>", result)
        self.assertIn("3.1 Login Process", result)
        self.assertIn("3.2 Session Management", result)

    def test_list_attribute_joined_with_br(self):
        """plain list attribute joined with <br>."""
        item_data = (
            r"verification-method:" + "\n"
            r"  - system test" + "\n"
            r"  - analysis" + "\n"
            r"text: |" + "\n"
            r"  Some text."
        )
        document, item = self._make_item(YAML_LIST_ATTRIBUTE, item_data)
        result = getLines(publisher.publish_lines(document, ".md"))
        self.assertIn("| Attribute | Value |", result)
        self.assertIn("| verification-method | system test<br>analysis |", result)

    def test_empty_attribute_value_skipped(self):
        """Verify 'if not value: continue' - empty attribute produces no table."""
        item_data = r"type: ''" + "\n" r"text: |" + "\n" r"  Some text."
        document, item = self._make_item(YAML_SINGLE_ATTRIBUTE, item_data)
        result = getLines(publisher.publish_lines(document, ".md"))
        self.assertNotIn("| Attribute | Value |", result)

    def test_structured_attribute_combined_label_renders_as_link(self):
        """Verify combined label {label: [...]} renders correctly."""
        item_data = (
            r"spec-refs-from:" + "\n"
            r"  - file: System_Safety_Concept.md" + "\n"
            r"    section: 'Stop Functions'" + "\n"
            r"    anchor: stop-functions" + "\n"
            r"    url: https://gitlab.com/group/project/-/blob/main/specs/safety.md#stop-functions"
            + "\n"
            r"text: |" + "\n"
            r"  Some text."
        )
        document, item = self._make_item(YAML_COMBINED_LABEL_ATTRIBUTES, item_data)
        result = getLines(publisher.publish_lines(document, ".md"))
        self.assertIn("| Attribute | Value |", result)
        # Combined label: file + ": " + section
        self.assertIn(
            "[System_Safety_Concept.md: Stop Functions]"
            "(https://gitlab.com/group/project/-/blob/main/specs/safety.md#stop-functions)",
            result,
        )

    def test_structured_attribute_no_url_renders_label_only(self):
        """Verify missing url → label appended without link tag."""
        item_data = (
            r"spec-refs-from:" + "\n"
            r"  - file: System_Safety_Concept.md" + "\n"
            r"    section: 'Stop Functions'" + "\n"
            r"    anchor: stop-functions" + "\n"
            # url intentionally missing
            r"text: |" + "\n"
            r"  Some text."
        )
        document, item = self._make_item(YAML_COMBINED_LABEL_ATTRIBUTES, item_data)
        result = getLines(publisher.publish_lines(document, ".md"))
        self.assertIn("| Attribute | Value |", result)
        # No link – only label text
        self.assertIn("System_Safety_Concept.md: Stop Functions", result)
        self.assertNotIn("href", result)
        self.assertNotIn("](", result)
