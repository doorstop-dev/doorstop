# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.core.publishers.text module."""

# pylint: disable=unused-argument,protected-access

import os
import unittest
from secrets import token_hex
from shutil import rmtree
from unittest.mock import Mock, patch

from doorstop.core import publisher
from doorstop.core.publishers.tests.helpers import getLines
from doorstop.core.tests import MockDataMixIn, MockItemAndVCS


class TestModule(MockDataMixIn, unittest.TestCase):
    """Unit tests for the doorstop.core.publishers.text module."""

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

    def test_lines_text_item(self):
        """Verify text can be published from an item."""
        with patch.object(
            self.item5, "find_ref", Mock(return_value=("path/to/mock/file", 42))
        ):
            lines = publisher.publish_lines(self.item5, ".txt")
            text = "".join(line + "\n" for line in lines)
        self.assertIn("Reference: path/to/mock/file (line 42)", text)

    def test_lines_text_item_references(self):
        """Verify references can be published to a text file from an item."""
        mock_value = [("path/to/mock/file1", 3), ("path/to/mock/file2", None)]
        with patch.object(self.item6, "find_references", Mock(return_value=mock_value)):
            lines = publisher.publish_lines(self.item6, ".txt")
            text = "".join(line + "\n" for line in lines)
        self.assertIn(
            "Reference: path/to/mock/file1 (line 3), path/to/mock/file2", text
        )

    def test_lines_text_item_heading(self):
        """Verify text can be published from an item (heading)."""
        expected = "1.1     Heading\n\n"
        lines = publisher.publish_lines(self.item, ".txt")
        # Act
        text = "".join(line + "\n" for line in lines)
        # Assert
        self.assertEqual(expected, text)

    @patch("doorstop.settings.PUBLISH_HEADING_LEVELS", False)
    def test_lines_text_item_heading_no_heading_levels(self):
        """Verify an item heading level can be ommitted."""
        expected = "Heading\n\n"
        lines = publisher.publish_lines(self.item, ".txt")
        # Act
        text = "".join(line + "\n" for line in lines)
        # Assert
        self.assertEqual(expected, text)

    @patch("doorstop.settings.PUBLISH_CHILD_LINKS", False)
    def test_lines_text_item_normative(self):
        """Verify text can be published from an item (normative)."""
        expected = (
            "1.2     req4" + "\n\n"
            "        This shall..." + "\n\n"
            "        Reference: Doorstop.sublime-project" + "\n\n"
            "        Links: sys4" + "\n\n"
        )
        lines = publisher.publish_lines(self.item3, ".txt")
        # Act
        text = "".join(line + "\n" for line in lines)
        # Assert
        self.assertEqual(expected, text)

    @patch("doorstop.settings.CHECK_REF", False)
    def test_lines_text_item_no_ref_check(self):
        """Verify text can be published without checking references."""
        lines = publisher.publish_lines(self.item5, ".txt")
        text = "".join(line + "\n" for line in lines)
        self.assertIn("Reference: 'abc123'", text)

    @patch("doorstop.settings.CHECK_REF", False)
    def test_lines_text_item_no_references_check(self):
        """Verify text can be published without checking references."""
        lines = publisher.publish_lines(self.item6, ".txt")
        text = "".join(line + "\n" for line in lines)
        self.assertIn("Reference: 'abc1', 'abc2'", text)

    @patch("doorstop.settings.PUBLISH_CHILD_LINKS", True)
    def test_lines_text_item_with_child_links(self):
        """Verify text can be published with child links."""
        # Act
        lines = publisher.publish_lines(self.item2, ".txt")
        text = "".join(line + "\n" for line in lines)
        # Assert
        self.assertIn("Child links: tst1", text)

    def test_lines_text_item(self):
        """Verify text can be published from an item."""
        with patch.object(
            self.item5, "find_ref", Mock(return_value=("path/to/mock/file", 42))
        ):
            lines = publisher.publish_lines(self.item5, ".txt")
            text = "".join(line + "\n" for line in lines)
        self.assertIn("Reference: path/to/mock/file (line 42)", text)

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
        expected = os.linesep.join(
            ["1.0     Header name", "Test of a single text line." + "\n\n"]
        )
        # Act
        result = getLines(publisher.publish_lines(item, ".txt"))
        # Assert
        self.assertEqual(expected, result)
