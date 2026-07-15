"""Unit tests for HTML list handling."""

import unittest

from doorstop.core import publisher
from doorstop.core.tests import MockItemAndVCS


# Helper function like in other tests
def getLines(gen):
    """Get lines from a generator."""
    return "\n".join(gen)


class TestHtmlListHandling(unittest.TestCase):
    """Tests for HTML list generation with nested lists."""

    def test_nested_list_2_spaces(self):
        """Verify that 2-space nested lists render correctly in HTML."""
        # Setup
        generated_data = (
            r"text: |" + "\n"
            r"  Test list:" + "\n"
            r"  " + "\n"
            r"  - Item 1" + "\n"
            r"    - Nested" + "\n"
            r"  - Item 2"
        )
        item = MockItemAndVCS("TEST-001.yml", _file=generated_data)

        # Act
        result = getLines(publisher.publish_lines(item, ".html"))

        # Assert
        self.assertIn("<ul>", result)
        self.assertIn("<li>Item 1", result)
        self.assertIn("<li>Nested", result)
        self.assertIn("</ul>", result)

    def test_multiple_nesting_levels(self):
        """Verify that multiple nesting levels work correctly."""
        # Setup
        generated_data = (
            r"text: |" + "\n"
            r"  Multi-level:" + "\n"
            r"  " + "\n"
            r"  - Level 1" + "\n"
            r"    - Level 2" + "\n"
            r"      - Level 3" + "\n"
            r"  - Back to 1"
        )
        item = MockItemAndVCS("TEST-002.yml", _file=generated_data)

        # Act
        result = getLines(publisher.publish_lines(item, ".html"))

        # Assert
        self.assertGreaterEqual(result.count("<ul>"), 2)
        self.assertGreaterEqual(result.count("</ul>"), 2)

    def test_ordered_list_nesting(self):
        """Verify that ordered lists with nesting work."""
        # Setup
        generated_data = (
            r"text: |" + "\n"
            r"  Ordered:" + "\n"
            r"  " + "\n"
            r"  1. First" + "\n"
            r"     1. Nested" + "\n"
            r"  2. Second"
        )
        item = MockItemAndVCS("TEST-003.yml", _file=generated_data)

        # Act
        result = getLines(publisher.publish_lines(item, ".html"))

        # Assert
        self.assertIn("<ol>", result)
        self.assertIn("</ol>", result)

    def test_list_without_blank_line(self):
        """Verify that lists without leading blank line still work."""
        # Setup
        generated_data = (
            r"text: |" + "\n"
            r"  Text before:" + "\n"
            r"  - Item 1" + "\n"
            r"    - Nested" + "\n"
            r"  - Item 2"
        )
        item = MockItemAndVCS("TEST-004.yml", _file=generated_data)

        # Act
        result = getLines(publisher.publish_lines(item, ".html"))

        # Assert
        self.assertIn("<ul>", result)
        self.assertIn("<li>", result)

    def test_normalize_inconsistent_indentation(self):
        """Verify that inconsistent indentation is normalized."""
        # Setup
        generated_data = (
            r"text: |" + "\n"
            r"  List:" + "\n"
            r"  " + "\n"
            r"  - Item 1" + "\n"
            r"   - One space" + "\n"
            r"    - Two spaces" + "\n"
            r"      - Four spaces" + "\n"
            r"  - Back"
        )
        item = MockItemAndVCS("TEST-005.yml", _file=generated_data)

        # Act
        result = getLines(publisher.publish_lines(item, ".html"))

        # Assert
        self.assertIn("<ul>", result)
        ul_count = result.count("<ul>")
        self.assertGreaterEqual(ul_count, 2, "Should have multiple nesting levels")

    def test_mixed_list_types(self):
        """Verify that mixed ordered and unordered lists work."""
        # Setup
        generated_data = (
            r"text: |" + "\n"
            r"  Mixed:" + "\n"
            r"  " + "\n"
            r"  - Unordered" + "\n"
            r"    1. Ordered nested" + "\n"
            r"  - Unordered again"
        )
        item = MockItemAndVCS("TEST-006.yml", _file=generated_data)

        # Act
        result = getLines(publisher.publish_lines(item, ".html"))

        # Assert
        self.assertIn("<ul>", result)
        self.assertIn("<ol>", result)


class TestListNormalizationInHtml(unittest.TestCase):
    """Tests specifically for the normalization pipeline in HTML."""

    def setUp(self):
        """Setup test fixtures."""
        from doorstop.core.publishers.html import HtmlPublisher

        self.publisher = HtmlPublisher(None, ".html")

    def test_normalization_called(self):
        """Verify that normalization is applied during HTML generation."""
        # 2 spaces before second item
        text = "- Item\n  - Nested"

        normalized = self.publisher._normalize_list_indentation(text)

        # Should convert 2 spaces to 4 spaces
        self.assertIn("    - Nested", normalized)
        # Original 2-space indent should be gone
        lines = normalized.split("\n")
        self.assertEqual(lines[1], "    - Nested")

    def test_spacing_fix_called(self):
        """Verify that spacing fix is applied."""
        text = "Text\n- Item\nMore text"

        fixed = self.publisher._fix_list_spacing(text)

        # Should add blank lines around list
        self.assertIn("Text\n\n-", fixed)
        self.assertIn("Item\n\nMore", fixed)

    def test_combined_normalization_and_spacing(self):
        """Verify that both normalization and spacing work together."""
        text = "Text\n- Item\n  - Nested\nMore text"

        # Apply both transformations
        normalized = self.publisher._normalize_list_indentation(text)
        fixed = self.publisher._fix_list_spacing(normalized)

        # Check results
        self.assertIn("    - Nested", fixed)  # Normalized to 4 spaces
        self.assertIn("Text\n\n-", fixed)  # Spacing added before list
        self.assertIn("Nested\n\nMore", fixed)  # Spacing added after list

    def test_normalization_preserves_content(self):
        """Verify that normalization doesn't change list item content."""
        text = "- First item\n  - Second item with 2 spaces"

        normalized = self.publisher._normalize_list_indentation(text)

        # Content should be preserved
        self.assertIn("First item", normalized)
        self.assertIn("Second item with 2 spaces", normalized)
        # But indentation should change
        self.assertIn("    - Second", normalized)

    def test_normalization_multiple_levels(self):
        """Verify that multiple nesting levels are all normalized."""
        text = "- L1\n  - L2\n    - L3"

        normalized = self.publisher._normalize_list_indentation(text)

        lines = normalized.split("\n")
        self.assertEqual(lines[0], "- L1")
        self.assertEqual(lines[1], "    - L2")
        self.assertEqual(lines[2], "        - L3")


if __name__ == "__main__":
    unittest.main()
