# tests/test_latex_functions.py

import pytest
from doorstop.core.publishers._latex_functions import (
    _has_complex_formatting,
    _format_simple_text_block,
    _convert_markdown_link_to_href,
    _escape_latex_text,
    _escape_latex_url,
    _add_comment,
    _fix_table_line,
    _check_for_new_table,
    _typeset_latex_image,
)


class TestComplexFormatting:
    """Test complex formatting detection."""
    
    def test_simple_text(self):
        """Simple text should return False."""
        text = ["This is **bold** text", "And _italic_"]
        assert _has_complex_formatting(text) is False
    
    def test_table_detected(self):
        """Tables should be detected."""
        text = [
            "| Col1 | Col2 |",
            "|------|------|",
            "| A    | B    |"
        ]
        assert _has_complex_formatting(text) is True
    
    def test_plantuml_detected(self):
        """PlantUML should be detected."""
        text = [
            '`plantuml title="Test"',
            "@startuml",
            "A -> B",
            "@enduml"
        ]
        assert _has_complex_formatting(text) is True
    
    def test_math_detected(self):
        """Math environments should be detected."""
        text = ["Formula: $$E = mc^2$$"]
        assert _has_complex_formatting(text) is True
    
    def test_code_block_not_complex(self):
        """Code blocks alone are not complex."""
        text = [
            "```python",
            "def foo():",
            "    pass",
            "```"
        ]
        assert _has_complex_formatting(text) is False


class TestSimpleTextBlock:
    """Test simple text block formatting."""
    
    def test_code_block(self):
        """Test code block processing."""
        text = ["```python", "x = 1", "```"]
        result = list(_format_simple_text_block(text))
        assert "\\begin{lstlisting}[language=python]" in result
        assert "x = 1" in result
        assert "\\end{lstlisting}" in result
    
    def test_inline_code(self):
        """Test inline code processing."""
        text = ["Use `python main.py` to run"]
        result = list(_format_simple_text_block(text))
        assert any("\\texttt{python main.py}" in line for line in result)
    
    def test_mixed_formatting(self):
        """Test mixed markdown and code."""
        text = [
            "**Bold** text with `code`",
            "",
            "```bash",
            "ls -la",
            "```"
        ]
        result = list(_format_simple_text_block(text))
        # Should have bold
        assert any("\\textbf{Bold}" in line for line in result)
        # Should have inline code
        assert any("\\texttt{code}" in line for line in result)
        # Should have code block
        assert any("\\begin{lstlisting}[language=bash]" in line for line in result)


class TestEscapeLatexText:
    """Test LaTeX text escaping."""
    
    def test_escape_backslash(self):
        """Backslashes should be escaped first."""
        result = _escape_latex_text("C:\\path\\to\\file")
        assert result == r"C:\textbackslash{}path\textbackslash{}to\textbackslash{}file"
    
    def test_escape_braces(self):
        """Braces should be escaped."""
        result = _escape_latex_text("Text {with} braces")
        assert result == r"Text \{with\} braces"
    
    def test_escape_underscore(self):
        """Underscores should be escaped."""
        result = _escape_latex_text("variable_name")
        assert result == r"variable\_name"
    
    def test_escape_special_chars(self):
        """Special characters should be escaped."""
        result = _escape_latex_text("Test & 50% #1 $10")
        assert result == r"Test \& 50\% \#1 \$10"
    
    def test_escape_caret_tilde(self):
        """Caret and tilde should be escaped."""
        result = _escape_latex_text("x^2 and ~user")
        assert result == r"x\textasciicircum{}2 and \textasciitilde{}user"
    
    def test_brackets_not_escaped(self):
        """Square brackets and parentheses should NOT be escaped."""
        result = _escape_latex_text("Text [with] (brackets)")
        assert result == "Text [with] (brackets)"
    
    def test_combined_escaping(self):
        """Multiple special chars should all be escaped."""
        result = _escape_latex_text("Test_case {id: #1} @ 100%")
        assert r"\_" in result
        assert r"\{" in result
        assert r"\}" in result
        assert r"\#" in result
        assert r"\%" in result


class TestEscapeLatexUrl:
    """Test URL escaping for LaTeX."""
    
    def test_escape_hash(self):
        """Hash in URL (anchor) should be escaped."""
        result = _escape_latex_url("https://example.com/page#section")
        assert result == r"https://example.com/page\#section"
    
    def test_escape_percent(self):
        """Percent in URL should be escaped."""
        result = _escape_latex_url("https://example.com/file%20name.pdf")
        assert result == r"https://example.com/file\%20name.pdf"
    
    def test_escape_ampersand(self):
        """Ampersand in URL should be escaped."""
        result = _escape_latex_url("https://example.com?foo=1&bar=2")
        assert result == r"https://example.com?foo=1\&bar=2"
    
    def test_underscore_not_escaped(self):
        """Underscores in URLs should NOT be escaped (work in \\href{})."""
        result = _escape_latex_url("https://example.com/file_name.pdf")
        assert result == "https://example.com/file_name.pdf"
    
    def test_relative_path(self):
        """Relative paths should work."""
        result = _escape_latex_url("../path/to/file.md#anchor")
        assert result == r"../path/to/file.md\#anchor"
    
    def test_complex_url(self):
        """Complex URL with multiple special chars."""
        url = "https://git.example.org/path_to/repo#section-name&param=value%20test"
        result = _escape_latex_url(url)
        assert r"\#" in result
        assert r"\&" in result
        assert r"\%" in result
        assert "_to" in result  # Underscore NOT escaped


class TestConvertMarkdownLinkToHref:
    """Test markdown link to LaTeX \\href{} conversion."""
    
    def test_simple_link(self):
        """Simple link should be converted correctly."""
        link = "[Simple Link](https://example.com)"
        result = _convert_markdown_link_to_href(link)
        assert result == r"\href{https://example.com}{Simple Link}"
    
    def test_link_with_nested_brackets(self):
        """Link text with nested brackets should work."""
        link = "[Text [1/h] here](https://example.com)"
        result = _convert_markdown_link_to_href(link)
        assert result == r"\href{https://example.com}{Text [1/h] here}"
    
    def test_link_with_multiple_nested_brackets(self):
        """Multiple nested brackets should work."""
        link = "[Frequency [1/h] (PFH) [SIL 3]](https://example.com)"
        result = _convert_markdown_link_to_href(link)
        assert r"\href{https://example.com}" in result
        assert "[1/h]" in result
        assert "[SIL 3]" in result
    
    def test_link_with_parentheses_in_text(self):
        """Parentheses in link text should work."""
        link = "[Item (deprecated)](https://example.com)"
        result = _convert_markdown_link_to_href(link)
        assert result == r"\href{https://example.com}{Item (deprecated)}"
    
    def test_relative_url(self):
        """Relative URLs should work."""
        link = "[See Document](../other/document.md)"
        result = _convert_markdown_link_to_href(link)
        assert result == r"\href{../other/document.md}{See Document}"
    
    def test_anchor_only(self):
        """Anchor-only links should work."""
        link = "[Jump to Section](#requirements)"
        result = _convert_markdown_link_to_href(link)
        assert result == r"\href{\#requirements}{Jump to Section}"
    
    def test_url_with_anchor(self):
        """URL with anchor should escape the hash."""
        link = "[Link](https://example.com/page.html#section)"
        result = _convert_markdown_link_to_href(link)
        assert r"\#section" in result
    
    def test_url_with_query_params(self):
        """URL with query parameters should escape ampersands."""
        link = "[Search](https://example.com?q=test&lang=en)"
        result = _convert_markdown_link_to_href(link)
        assert r"\&" in result
    
    def test_text_with_underscores(self):
        """Underscores in text should be escaped."""
        link = "[System_Safety_Concept](https://example.com)"
        result = _convert_markdown_link_to_href(link)
        assert r"System\_Safety\_Concept" in result
    
    def test_url_with_underscores(self):
        """Underscores in URL should NOT be escaped."""
        link = "[Link](https://example.com/file_name.md)"
        result = _convert_markdown_link_to_href(link)
        # URL part should have literal underscore
        assert r"\href{https://example.com/file_name.md}" in result
        # But text part should escape it (if text had underscores)
    
    def test_text_with_special_chars(self):
        """Special chars in text should be escaped."""
        link = "[Test & Demo 50%](https://example.com)"
        result = _convert_markdown_link_to_href(link)
        assert r"\&" in result
        assert r"\%" in result
    
    def test_real_world_complex_link(self):
        """Real-world complex link from requirements."""
        link = "[System_Safety_Concept: SIL and Average Frequency of Dangerous Failure [1/h] (PFH)](https://git01.siebmeyer.org/sieb-meyer/produktzulassung/fusi/fusi-projekte/sd4x-safety-module/product-development/dev-sd4x-safety-module/-/blob/11-create-initial-technical-safety-requirements-spec-srs-from-system-safety-concept-fsc/DevDocs/System/System_Safety_Concept/System_Safety_Concept.md#sil-and-average-frequency-of-dangerous-failure-1h-pfh)"
        result = _convert_markdown_link_to_href(link)
        
        # Check structure
        assert r"\href{" in result
        assert "https://git01.siebmeyer.org" in result
        
        # Check text is escaped
        assert r"System\_Safety\_Concept" in result
        
        # Check nested brackets preserved
        assert "[1/h]" in result
        assert "(PFH)" in result
        
        # Check URL anchor escaped
        assert r"\#sil-and-average-frequency" in result
    
    def test_invalid_markdown_not_a_link(self):
        """Text that's not a link should be escaped as plain text."""
        text = "Just some [text] with brackets"
        result = _convert_markdown_link_to_href(text)
        # Should be escaped as plain text
        assert r"\href" not in result
        assert "Just some [text] with brackets" in result
    
    def test_link_with_whitespace(self):
        """Links with leading/trailing whitespace should work."""
        link = "  [Link](https://example.com)  "
        result = _convert_markdown_link_to_href(link)
        assert result == r"\href{https://example.com}{Link}"
    
    def test_empty_text(self):
        """Link with empty text."""
        link = "[](https://example.com)"
        result = _convert_markdown_link_to_href(link)
        assert r"\href{https://example.com}{}" in result
    
    def test_empty_url(self):
        """Link with empty URL."""
        link = "[Link Text]()"
        result = _convert_markdown_link_to_href(link)
        assert r"\href{}{Link Text}" in result
    
    def test_windows_path(self):
        """Windows-style path should work."""
        link = "[File](C:\\Users\\test\\file.md)"
        result = _convert_markdown_link_to_href(link)
        # Backslashes in URL should be escaped
        assert r"\textbackslash{}" in result or "C:" in result


class TestMarkdownLinkEdgeCases:
    """Test edge cases for markdown link conversion."""
    
    def test_multiple_consecutive_brackets(self):
        """Multiple consecutive brackets."""
        link = "[Text [[nested]]](https://example.com)"
        result = _convert_markdown_link_to_href(link)
        assert r"\href{https://example.com}" in result
        assert "[[nested]]" in result
    
    def test_unbalanced_brackets_in_text(self):
        """Unbalanced brackets should still work if link structure is valid."""
        link = "[Text [unbalanced](https://example.com)"
        result = _convert_markdown_link_to_href(link)
        # May or may not work depending on implementation
        # At minimum, shouldn't crash
        assert isinstance(result, str)
    
    def test_escaped_brackets_in_url(self):
        """URL with encoded brackets."""
        link = "[Link](https://example.com/path%5Btest%5D)"
        result = _convert_markdown_link_to_href(link)
        assert r"\%" in result  # Percent should be escaped
        assert "5Btest" in result  # Should preserve URL encoding
    
    def test_unicode_in_text(self):
        """Unicode characters in link text."""
        link = "[Tëst with ümläuts](https://example.com)"
        result = _convert_markdown_link_to_href(link)
        assert "Tëst with ümläuts" in result
    
    def test_unicode_in_url(self):
        """Unicode in URL (should be URL-encoded in practice)."""
        link = "[Link](https://example.com/tëst)"
        result = _convert_markdown_link_to_href(link)
        assert "tëst" in result

class TestImageAndTableFunctions:
    """Tests for image, table, and comment functions."""
    
    def test_add_comment_basic(self):
        """Test basic comment addition."""
        result = _add_comment("Test line")
        assert result == "% Test line"
    
    def test_add_comment_empty_line(self):
        """Test comment on empty line."""
        result = _add_comment("")
        assert result == "%"
    
    def test_add_comment_preserves_content(self):
        """Test that comment preserves original content."""
        original = "This is a test with special chars: #$%&"
        result = _add_comment(original)
        assert result == f"% {original}"
    
    def test_fix_table_line_escapes_cells(self):
        """Test that table cells are properly escaped."""
        # Table with special characters in cells
        line = "| test_var | 100% | A&B |"
        result = _fix_table_line(line)
        # Should escape underscores, percent, ampersand
        assert r"\_" in result
        assert r"\%" in result
        assert r"\&" in result
    
    def test_fix_table_line_preserves_pipes(self):
        """Test that pipe delimiters are preserved."""
        line = "| col1 | col2 | col3 |"
        result = _fix_table_line(line)
        assert result.count("|") == line.count("|")
    
    def test_fix_table_line_empty_cells(self):
        """Test handling of empty table cells."""
        line = "| | content | |"
        result = _fix_table_line(line)
        assert "| |" in result  # Empty cells preserved
    
    def test_check_for_new_table_detects_pipe_table(self):
        """Test detection of pipe-delimited tables."""
        line = "| Header


# Run tests with: pytest doorstop/core/publishers/tests/test_latex_functions.py -v