"""Unit tests for list normalization in BasePublisher."""

import unittest

from doorstop.core.publishers.markdown import MarkdownPublisher


class TestListNormalization(unittest.TestCase):
    """Tests for list indentation normalization."""

    def setUp(self):
        """Setup test fixtures."""
        # Use MarkdownPublisher instead of BasePublisher (it's concrete)
        self.publisher = MarkdownPublisher(None, ".md")

    def test_normalize_2_to_4_spaces(self):
        """Verify that 2-space indentation is normalized to 4 spaces."""
        text = """- Item 1
  - Nested with 2 spaces
- Item 2"""

        expected = """- Item 1
    - Nested with 2 spaces
- Item 2"""

        result = self.publisher._normalize_list_indentation(text)
        self.assertEqual(expected, result)

    def test_normalize_mixed_indentation(self):
        """Verify that mixed indentation (1, 2, 4, 6 spaces) is normalized."""
        text = """- Item 1
 - One space
  - Two spaces
      - Six spaces
- Back to root"""

        expected = """- Item 1
    - One space
        - Two spaces
            - Six spaces
- Back to root"""

        result = self.publisher._normalize_list_indentation(text)
        self.assertEqual(expected, result)

    def test_normalize_already_correct(self):
        """Verify that already-correct indentation is unchanged."""
        text = """- Item 1
    - Nested with 4 spaces
        - Double nested with 8 spaces
- Item 2"""

        result = self.publisher._normalize_list_indentation(text)
        self.assertEqual(text, result)

    def test_normalize_no_lists(self):
        """Verify that text without lists is unchanged."""
        text = """Just some text
Without any lists
At all"""

        result = self.publisher._normalize_list_indentation(text)
        self.assertEqual(text, result)

    def test_normalize_ordered_lists(self):
        """Verify that ordered lists are normalized correctly."""
        text = """1. First item
  2. Nested item
    3. Double nested
1. Second item"""

        expected = """1. First item
    2. Nested item
        3. Double nested
1. Second item"""

        result = self.publisher._normalize_list_indentation(text)
        self.assertEqual(expected, result)

    def test_normalize_separate_list_blocks(self):
        """Verify that separate list blocks are normalized independently."""
        text = """First list:
- Item 1
  - Nested

Some text in between

Second list:
- Item A
  - Nested A"""

        expected = """First list:
- Item 1
    - Nested

Some text in between

Second list:
- Item A
    - Nested A"""

        result = self.publisher._normalize_list_indentation(text)
        self.assertEqual(expected, result)

    def test_normalize_with_headings(self):
        """Verify that lists separated by headings are handled correctly."""
        text = """# Heading 1
- Item 1
  - Nested

## Heading 2
- Item 2
  - Nested"""

        expected = """# Heading 1
- Item 1
    - Nested

## Heading 2
- Item 2
    - Nested"""

        result = self.publisher._normalize_list_indentation(text)
        self.assertEqual(expected, result)

    def test_normalize_asterisk_lists(self):
        """Verify that asterisk-style lists are normalized."""
        text = """* Item 1
  * Nested with 2 spaces
* Item 2"""

        expected = """* Item 1
    * Nested with 2 spaces
* Item 2"""

        result = self.publisher._normalize_list_indentation(text)
        self.assertEqual(expected, result)

    def test_normalize_triple_nested(self):
        """Verify that three levels of nesting work correctly."""
        text = """- Level 1
  - Level 2
    - Level 3
- Back to 1"""

        expected = """- Level 1
    - Level 2
        - Level 3
- Back to 1"""

        result = self.publisher._normalize_list_indentation(text)
        self.assertEqual(expected, result)


class TestListSpacing(unittest.TestCase):
    """Tests for list spacing fixes."""

    def setUp(self):
        """Setup test fixtures."""
        self.publisher = MarkdownPublisher(None, ".md")

    def test_add_blank_line_before_list(self):
        """Verify that blank line is added before list."""
        text = """Some text before
- List item
- Another item"""

        expected = """Some text before

- List item
- Another item"""

        result = self.publisher._fix_list_spacing(text)
        self.assertEqual(expected, result)

    def test_add_blank_line_after_list(self):
        """Verify that blank line is added after list."""
        text = """- List item
- Another item
Text after"""

        expected = """- List item
- Another item

Text after"""

        result = self.publisher._fix_list_spacing(text)
        self.assertEqual(expected, result)

    def test_no_double_blank_lines(self):
        """Verify that existing blank lines are not duplicated."""
        text = """Some text

- List item
- Another item

More text"""

        result = self.publisher._fix_list_spacing(text)
        self.assertEqual(text, result)

    def test_list_at_start(self):
        """Verify that list at document start has no leading blank line."""
        text = """- List item
- Another item"""

        result = self.publisher._fix_list_spacing(text)
        self.assertEqual(text, result)

    def test_consecutive_lists(self):
        """Verify that consecutive list items are not separated."""
        text = """- Item 1
- Item 2
- Item 3"""

        result = self.publisher._fix_list_spacing(text)
        self.assertEqual(text, result)

    def test_nested_lists_not_separated(self):
        """Verify that nested list items are not separated from parent."""
        text = """- Item 1
  - Nested
  - More nested
- Item 2"""

        result = self.publisher._fix_list_spacing(text)
        self.assertEqual(text, result)

    def test_both_before_and_after(self):
        """Verify that blank lines are added both before and after."""
        text = """Text before
- List item
Text after"""

        expected = """Text before

- List item

Text after"""

        result = self.publisher._fix_list_spacing(text)
        self.assertEqual(expected, result)


class TestCombinedNormalizationAndSpacing(unittest.TestCase):
    """Tests for combined normalization and spacing."""

    def setUp(self):
        """Setup test fixtures."""
        self.publisher = MarkdownPublisher(None, ".md")

    def test_full_pipeline(self):
        """Verify that normalization and spacing work together."""
        text = """Text before list:
- Item 1
  - Nested with 2 spaces
- Item 2
Text after list"""

        # First normalize
        text = self.publisher._normalize_list_indentation(text)
        # Then fix spacing
        result = self.publisher._fix_list_spacing(text)

        expected = """Text before list:

- Item 1
    - Nested with 2 spaces
- Item 2

Text after list"""

        self.assertEqual(expected, result)

    def test_complex_document_structure(self):
        """Verify complex document with multiple lists."""
        text = """# Title
Some intro text
- List 1 item 1
  - Nested
- List 1 item 2

Middle text

- List 2 item 1
  - Nested
- List 2 item 2
End text"""

        # Apply both transformations
        text = self.publisher._normalize_list_indentation(text)
        result = self.publisher._fix_list_spacing(text)

        # Verify normalization (2 -> 4 spaces)
        self.assertIn("    - Nested", result)
        # Verify spacing around first list
        self.assertIn("text\n\n- List 1", result)
        # Verify spacing around second list
        self.assertIn("item 2\n\nEnd", result)


if __name__ == "__main__":
    unittest.main()
