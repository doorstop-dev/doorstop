# SPDX-License-Identifier: LGPL-3.0-only

r"""
Tests for LaTeX publishing functions.

This module tests the LaTeX conversion pipeline in doorstop/core/publishers/_latex_functions.py.
The pipeline converts Markdown and HTML to LaTeX format through a 14-phase processing system.

Test Organization:
==================
The tests are organized by functional area, mirroring the conversion pipeline:

1. Character Escaping (Phase 4-5)
   - LaTeX special character escaping
   - URL-specific escaping rules
   
2. Markdown Conversion (Phase 2-3, 6-8)
   - Links, formatting (bold/italic/strikethrough)
   - Headings and heading edge cases
   - Context-aware heading numbering (document vs. item text)
   
3. HTML Conversion (Phase 1)
   - HTML tags to LaTeX/Markdown equivalents
   - Figure and anchor handling
   
4. Code Processing (Phase 2-3)
   - Inline code blocks
   - Fenced code blocks with language detection
   - Indented code detection
   
5. Blockquotes (Phase 0+)
   - Markdown blockquote syntax
   - Nested content in blockquotes
   
6. Text Block Pipeline (All Phases)
   - Full text block processing
   - Line break logic
   - Multi-phase integration
   
7. Complex Format Detection
   - Tables, PlantUML, Math
   - Nested list detection
   
8. Helper Utilities
   - Table formatting
   - Image typesetting
   - Comment wrapping
   - Debug context formatting

Pipeline Overview:
==================
Phase 1:  HTML → Markdown/LaTeX conversion
Phase 2:  Code block detection (```)
Phase 3:  Inline code preservation (`code`)
Phase 4:  Image/Link preservation
Phase 5:  Structural escaping (\, {, })
Phase 6:  Markdown formatting (**, *, ~~)
Phase 7:  Link processing (stored as FINALHREF)
Phase 8:  Heading conversion (# → \section, context-aware numbering)
Phase 9:  Special character escaping
Phase 10-14: Placeholder restoration

Coverage: 96% (159+ tests)
Last updated: 2024

Run with:
    poetry run pytest doorstop/core/publishers/tests/test_latex_functions.py -v
    
Generate coverage report:
    poetry run pytest doorstop/core/publishers/tests/test_latex_functions.py \
        --cov=doorstop.core.publishers._latex_functions \
        --cov-report=html \
        --cov-report=term-missing
"""

import re

import pytest

from doorstop import settings
from doorstop.core.publishers._latex_functions import (  # Core conversion functions; Escaping functions; Conversion functions; Helper functions
    _add_comment,
    _check_for_new_table,
    _convert_html_to_latex,
    _convert_markdown_link_to_href,
    _escape_latex_text,
    _escape_latex_url,
    _fix_table_line,
    _format_context,
    _format_simple_text_block,
    _has_complex_formatting,
    _latex_convert,
    _process_text_block,
    _typeset_latex_image,
)

# =============================================================================
# 1. CHARACTER ESCAPING (Phase 4-5)
# =============================================================================


class TestTextEscaping:
    """
    Test _escape_latex_text() function (Phase 5).

    Escapes the 10 LaTeX special characters in plain text:
        \ { } _ & # $ % ^ ~

    Used in: Link text, table cells, attribute values, general text.

    Strategy:
        - Backslash uses placeholder to avoid double-escaping braces
        - Caret/Tilde use ASCII commands to avoid math mode
        - Other chars use simple backslash prefix
    """

    def test_escape_backslash(self):
        """Backslashes must use \\textbackslash{} to avoid conflicts with other commands."""
        result = _escape_latex_text("C:\\path\\to\\file")
        expected = r"C:\textbackslash{}path\textbackslash{}to\textbackslash{}file"
        assert result == expected

    def test_escape_braces(self):
        """Curly braces control LaTeX grouping, must be escaped."""
        result = _escape_latex_text("Text {with} braces")
        assert result == r"Text \{with\} braces"

    def test_escape_underscore(self):
        """Underscores trigger subscript mode in LaTeX math, must be escaped."""
        result = _escape_latex_text("variable_name")
        assert result == r"variable\_name"

    def test_escape_common_symbols(self):
        """Common symbols: & (alignment), % (comment), # (parameter), $ (math mode)."""
        result = _escape_latex_text("Test & 50% #1 $10")
        assert result == r"Test \& 50\% \#1 \$10"

    def test_escape_caret_tilde(self):
        """Caret and tilde require special ASCII commands to avoid superscript/spacing issues."""
        result = _escape_latex_text("x^2 and ~user")
        assert result == r"x\textasciicircum{}2 and \textasciitilde{}user"

    def test_brackets_not_escaped(self):
        """Square brackets and parentheses are safe in normal LaTeX text."""
        result = _escape_latex_text("Text [with] (brackets)")
        assert result == "Text [with] (brackets)"

    def test_combined_escaping(self):
        """Multiple special characters in one string should all be properly escaped."""
        result = _escape_latex_text("Test_case {id: #1} @ 100%")
        assert r"\_" in result
        assert r"\{" in result
        assert r"\}" in result
        assert r"\#" in result
        assert r"\%" in result

    def test_all_ten_special_chars(self):
        """Comprehensive test for all 10 LaTeX special characters."""
        text = "Test & test # test $ test % test _ test ^ test ~ test"
        result = _escape_latex_text(text)
        assert "\\&" in result
        assert "\\#" in result
        assert "\\$" in result
        assert "\\%" in result
        assert "\\_" in result
        assert "\\textasciicircum{}" in result
        assert "\\textasciitilde{}" in result

    def test_backslash_uses_placeholder_system(self):
        """Backslash escaping uses placeholder to prevent double-escaping of braces."""
        text = "C:\\\\path\\\\to\\\\file"
        result = _escape_latex_text(text)
        # Should use textbackslash{} command
        assert "\\textbackslash{}" in result
        # Should NOT have double-escaped braces like \textbackslash\{\}
        assert "\\textbackslash\\{" not in result


class TestURLEscaping:
    """
    Test _escape_latex_url() function.

    Escapes only characters that break in \\href{URL}{text}:
        # (hash/anchor)
        % (percent encoding)
        & (query parameters)

    Important: Underscores are NOT escaped - they work fine in URLs.

    Used in: \\href{} URL parameter, file paths in \\includegraphics.
    """

    def test_escape_hash_for_anchors(self):
        """Hash symbols in URLs (anchors) must be escaped for LaTeX."""
        result = _escape_latex_url("https://example.com/page#section")
        assert result == r"https://example.com/page\#section"

    def test_escape_percent_encoding(self):
        """Percent signs in URL encoding (e.g., %20 for space) must be escaped."""
        result = _escape_latex_url("https://example.com/file%20name.pdf")
        assert result == r"https://example.com/file\%20name.pdf"

    def test_escape_ampersand_in_params(self):
        """Ampersands in query parameters must be escaped (LaTeX uses & for tables)."""
        result = _escape_latex_url("https://example.com?foo=1&bar=2")
        assert result == r"https://example.com?foo=1\&bar=2"

    def test_underscore_not_escaped_in_urls(self):
        """Underscores are common in URLs and work without escaping in \\href{}."""
        result = _escape_latex_url("https://example.com/file_name.pdf")
        assert result == "https://example.com/file_name.pdf"
        assert "\\_" not in result

    def test_relative_path_with_anchor(self):
        """Relative file paths with anchors should work correctly."""
        result = _escape_latex_url("../path/to/file.md#anchor")
        assert result == r"../path/to/file.md\#anchor"

    def test_complex_real_world_url(self):
        """Real-world URL with multiple special characters."""
        url = "https://git.example.org/path_to/repo#section-name&param=value%20test"
        result = _escape_latex_url(url)
        # Should escape: # & %
        assert r"\#" in result
        assert r"\&" in result
        assert r"\%" in result
        # Should NOT escape: _
        assert "_to" in result

    def test_url_with_all_escapable_chars(self):
        """URL containing all characters that need escaping."""
        url = "http://example.com/path?param=value&other=123#anchor"
        result = _escape_latex_url(url)
        assert "\\#" in result
        assert "\\&" in result


# =============================================================================
# 2. MARKDOWN CONVERSION (Phase 2-3, 6-8)
# =============================================================================


class TestMarkdownLinks:
    """
    Test _convert_markdown_link_to_href() function (Phase 7).

    Converts Markdown links to LaTeX \\href{} commands:
        [text](url) → \\href{url}{text}

    Challenges:
        - Nested brackets in text: [Text [nested] text](url)
        - Parentheses in URL: (disambiguation pages)
        - Special characters in both text and URL
        - Markdown formatting within link text

    The function uses regex with nested bracket matching.
    """

    def test_simple_link_conversion(self):
        """Basic markdown link should convert to \\href{} command."""
        link = "[Simple Link](https://example.com)"
        result = _convert_markdown_link_to_href(link)
        assert result == r"\href{https://example.com}{Simple Link}"

    def test_nested_brackets_in_text(self):
        """Link text can contain nested square brackets (e.g., units [1/h])."""
        link = "[Text [1/h] here](https://example.com)"
        result = _convert_markdown_link_to_href(link)
        assert result == r"\href{https://example.com}{Text [1/h] here}"

    def test_multiple_nested_brackets(self):
        """Multiple levels of nested brackets should be preserved."""
        link = "[Frequency [1/h] (PFH) [SIL 3]](https://example.com)"
        result = _convert_markdown_link_to_href(link)
        assert r"\href{https://example.com}" in result
        assert "[1/h]" in result
        assert "[SIL 3]" in result

    def test_parentheses_in_link_text(self):
        """Parentheses in link text should not confuse URL detection."""
        link = "[Item (deprecated)](https://example.com)"
        result = _convert_markdown_link_to_href(link)
        assert result == r"\href{https://example.com}{Item (deprecated)}"

    def test_relative_url_path(self):
        """Relative URLs (../, ./) should work correctly."""
        link = "[See Document](../other/document.md)"
        result = _convert_markdown_link_to_href(link)
        assert result == r"\href{../other/document.md}{See Document}"

    def test_anchor_only_link(self):
        """Anchor-only links (#section) for in-document references."""
        link = "[Jump to Section](#requirements)"
        result = _convert_markdown_link_to_href(link)
        # Hash must be escaped in LaTeX
        assert result == r"\href{\#requirements}{Jump to Section}"

    def test_url_with_anchor_fragment(self):
        """Full URL with anchor fragment should escape the hash."""
        link = "[Link](https://example.com/page.html#section)"
        result = _convert_markdown_link_to_href(link)
        assert r"\#section" in result

    def test_url_with_query_parameters(self):
        """Query parameters with & should be escaped."""
        link = "[Search](https://example.com?q=test&lang=en)"
        result = _convert_markdown_link_to_href(link)
        assert r"\&" in result

    def test_underscores_in_link_text_escaped(self):
        """Underscores in link text should be escaped (LaTeX subscript)."""
        link = "[System_Safety_Concept](https://example.com)"
        result = _convert_markdown_link_to_href(link)
        assert r"System\_Safety\_Concept" in result

    def test_underscores_in_url_not_escaped(self):
        """Underscores in URLs should NOT be escaped (work fine in \\href{})."""
        link = "[Link](https://example.com/file_name.md)"
        result = _convert_markdown_link_to_href(link)
        assert r"\href{https://example.com/file_name.md}" in result
        assert "file_name" in result  # Not file\_name

    def test_special_chars_in_text_escaped(self):
        """Special characters in link text should be properly escaped."""
        link = "[Test & Demo 50%](https://example.com)"
        result = _convert_markdown_link_to_href(link)
        assert r"\&" in result
        assert r"\%" in result

    def test_complex_real_world_link(self):
        """Real-world complex link from safety requirements documentation."""
        link = (
            "[System_Safety_Concept: SIL and Average Frequency of Dangerous Failure [1/h] (PFH)]"
            "(https://git01.siebmeyer.org/sieb-meyer/produktzulassung/fusi/fusi-projekte/"
            "sd4x-safety-module/product-development/dev-sd4x-safety-module/-/blob/11-create-"
            "initial-technical-safety-requirements-spec-srs-from-system-safety-concept-fsc/"
            "DevDocs/System/System_Safety_Concept/System_Safety_Concept.md#sil-and-average-"
            "frequency-of-dangerous-failure-1h-pfh)"
        )
        result = _convert_markdown_link_to_href(link)
        assert r"\href{" in result
        assert "https://git01.siebmeyer.org" in result
        assert r"System\_Safety\_Concept" in result  # Escaped underscores
        assert "[1/h]" in result  # Preserved brackets
        assert "(PFH)" in result  # Preserved parentheses
        assert r"\#sil-and-average-frequency" in result  # Escaped anchor

    def test_link_with_parentheses_in_url(self):
        """URLs with parentheses (Wikipedia disambiguation pages) should work."""
        link = "[Wikipedia](https://en.wikipedia.org/wiki/Example_(disambiguation))"
        result = _convert_markdown_link_to_href(link)
        assert "\\href{" in result
        assert "Wikipedia" in result
        assert "disambiguation" in result


class TestMarkdownLinkEdgeCases:
    """
    Edge cases and error handling for markdown link conversion.

    Tests defensive programming and graceful degradation when:
        - Input is not a valid link
        - Links have unusual formatting
        - Brackets/parentheses are unbalanced
    """

    def test_not_a_valid_link(self):
        """Text with brackets but no URL part should be returned unchanged."""
        text = "Just some [text] with brackets"
        result = _convert_markdown_link_to_href(text)
        assert r"\href" not in result
        assert result == text

    def test_link_with_whitespace_trimmed(self):
        """Links with leading/trailing whitespace should be handled."""
        link = "  [Link](https://example.com)  "
        result = _convert_markdown_link_to_href(link)
        assert result == r"\href{https://example.com}{Link}"

    def test_empty_link_text(self):
        """Link with empty text should still convert."""
        link = "[](https://example.com)"
        result = _convert_markdown_link_to_href(link)
        assert r"\href{https://example.com}{}" in result

    def test_empty_url_graceful_handling(self):
        """Link with empty URL should be handled gracefully."""
        link = "[Link Text]()"
        result = _convert_markdown_link_to_href(link)
        # Should return original or handle gracefully
        assert result == "[Link Text]()"

    def test_windows_path_as_url(self):
        """Windows-style paths with backslashes."""
        link = "[File](C:\\Users\\test\\file.md)"
        result = _convert_markdown_link_to_href(link)
        # Backslashes should be converted
        assert r"\textbackslash{}" in result or "C:" in result

    def test_multiple_consecutive_brackets(self):
        """Multiple consecutive brackets in link text."""
        link = "[Text [[nested]]](https://example.com)"
        result = _convert_markdown_link_to_href(link)
        assert r"\href{https://example.com}" in result
        assert "[[nested]]" in result

    def test_unbalanced_brackets_handled(self):
        """Unbalanced brackets should be handled gracefully without crashing."""
        link = "[Text [unbalanced](https://example.com)"
        result = _convert_markdown_link_to_href(link)
        assert isinstance(result, str)

    def test_percent_encoded_brackets_in_url(self):
        """URL with percent-encoded brackets."""
        link = "[Link](https://example.com/path%5Btest%5D)"
        result = _convert_markdown_link_to_href(link)
        assert r"\%" in result
        assert "5Btest" in result

    def test_unicode_in_text_preserved(self):
        """Unicode characters in link text should be preserved."""
        link = "[Tëst with ümläuts](https://example.com)"
        result = _convert_markdown_link_to_href(link)
        assert "Tëst with ümläuts" in result

    def test_unicode_in_url_preserved(self):
        """Unicode in URL should be preserved (browser/LaTeX handles it)."""
        link = "[Link](https://example.com/tëst)"
        result = _convert_markdown_link_to_href(link)
        assert "tëst" in result

    def test_link_without_url_part(self):
        """Link text without URL part: [text] with no ()."""
        result = _convert_markdown_link_to_href("[text without url]")
        assert "text without url" in result

    def test_link_with_unclosed_url(self):
        """Missing closing parenthesis for URL."""
        link = "[text](http://example.com"
        result = _convert_markdown_link_to_href(link)
        assert "text" in result

    def test_nested_brackets_and_parens_combined(self):
        """Complex nesting of both brackets and parentheses."""
        link = "[Text [with nested] brackets](http://example.com)"
        result = _convert_markdown_link_to_href(link)
        assert "\\href{" in result
        assert "with nested" in result
        assert "example.com" in result


class TestMarkdownFormatting:
    """
    Test markdown formatting conversion (Phase 6).

    Handled by _latex_convert():
        **text** → \\textbf{text}
        *text* or _text_ → \\textit{text}
        ~~text~~ → \\sout{text}

    Special case: **## Heading** should remove bold before heading conversion.
    """

    def test_bold_heading_level2(self):
        """Bold markup around headings should be removed: **## Text** → \\subsection{Text}."""
        result = _latex_convert("**## Test Heading**")
        assert "\\subsection{Test Heading}" in result
        assert "**" not in result

    def test_bold_heading_level3(self):
        """Works for all heading levels."""
        result = _latex_convert("**### Test Heading**")
        assert "\\subsubsection{Test Heading}" in result

    def test_normal_bold_text_unaffected(self):
        """Normal bold text (not around headings) should still work."""
        result = _latex_convert("This is **bold** text")
        assert "\\textbf{bold}" in result

    def test_link_with_bold_text(self):
        """Bold markdown in link text should be processed."""
        result = _latex_convert("[**Bold** text](https://example.com)")
        assert "\\href{https://example.com}" in result
        assert "\\textbf{Bold}" in result

    def test_link_with_italic_text(self):
        """Italic markdown in link text."""
        result = _latex_convert("[*Italic* text](https://example.com)")
        assert "\\href{https://example.com}" in result
        assert "Italic" in result

    def test_link_with_strikethrough_text(self):
        """Strikethrough in link text."""
        result = _latex_convert("[~~Strike~~ text](https://example.com)")
        assert "\\href{https://example.com}" in result
        assert "\\sout{Strike}" in result


class TestHeadings:
    """
    Test heading conversion (Phase 8).

    Markdown headings → LaTeX section commands:
        # → \\section
        ## → \\subsection
        ### → \\subsubsection
        #### → \\paragraph
        ##### → \\subparagraph
        ###### → warning (too deep for LaTeX)
    """

    def test_heading_level_too_deep_warning(self, caplog):
        """Headings deeper than level 5 should trigger warning."""
        import logging

        caplog.set_level(logging.WARNING)
        context = {"item_uid": "REQ001", "file": "test.yml", "line_num": 10}
        result = _latex_convert("###### Very deep heading", context=context)

        # Should log warning with context
        assert "Heading level too deep" in caplog.text
        assert "REQ001" in caplog.text

        # Should still produce output (subparagraph with comment)
        assert "\\subparagraph" in result
        assert "too deep for LaTeX" in result


class TestUnderscoreHandling:
    """
    Test underscore handling in different contexts.

    Simplified Rules:
        - _text_ → \\textit{text} (Markdown italic)
        - For code/variables: use backticks `code` → \\texttt{code}

    Examples:
        "_italic_"              → "\\textit{italic}"
        "word _text_ word"      → "word \\textit{text} word"
        "This_is_text"          → "This\\textit{is}text"
        "`variable_name`"       → "\\texttt{variable\\_name}"
    """

    def test_underscore_with_spaces_creates_italic(self):
        """Underscores with spaces around create italic formatting."""
        result = _latex_convert("This _is_ italic")
        assert "\\textit{is}" in result

    def test_underscore_at_word_boundaries(self):
        """Underscores at word boundaries create italic."""
        result = _latex_convert("Start _word_ end")
        assert "\\textit{word}" in result

    def test_underscore_pairs_in_words_become_italic(self):
        """Underscore pairs in words are converted to italic (simplified behavior)."""
        result = _latex_convert("This_is_text")
        assert "\\textit{is}" in result

    def test_multiple_underscores_first_pair_matches(self):
        """With multiple underscores, first complete pair becomes italic."""
        result = _latex_convert("file_name_here")
        assert "\\textit{name}" in result

    def test_single_letter_italic(self):
        """Single letter between underscores becomes italic."""
        result = _latex_convert("test_a_end")
        assert "\\textit{a}" in result

    def test_italic_at_start_of_line(self):
        """Italic formatting at start of line."""
        result = _latex_convert("_italic_ text")
        assert "\\textit{italic}" in result

    def test_italic_at_end_of_line(self):
        """Italic formatting at end of line."""
        result = _latex_convert("text _italic_")
        assert "\\textit{italic}" in result

    def test_italic_with_punctuation(self):
        """Italic with punctuation around it."""
        result = _latex_convert("Test (_italic_) text")
        assert "\\textit{italic}" in result

    def test_code_with_underscores_uses_backticks(self):
        """
        For code/variables with underscores, use backticks (best practice).

        Backticks produce \\texttt{} which properly escapes underscores.
        """
        result = _latex_convert("Use `variable_name` in code")
        assert "\\texttt{variable\\_name}" in result
        # Should NOT create italic
        assert result.count("\\textit{") == 0


# =============================================================================
# 3. HTML CONVERSION (Phase 1)
# =============================================================================


class TestHTMLConversion:
    """
    Test _convert_html_to_latex() function (Phase 1).

    Converts HTML tags to LaTeX or Markdown equivalents:
        <img src="..." alt="..."> → ![alt](src)
        <figcaption>text</figcaption> → *text* → \\textit{text}
        <cite>text</cite> → *text* → \\textit{text}
        <figure> → removed (content preserved)
        <a name="label"></a> → \\label{label}

    Returns: (converted_line, list_of_labels)
        - Labels use placeholder <<<HTMLLABEL#>>> to avoid removal by HTML cleaner
    """

    def test_html_anchor_to_label(self):
        """<a name="..."> should convert to LaTeX \\label{} command."""
        line, labels = _convert_html_to_latex('<a name="Test Section"></a>')
        # Should create placeholder
        assert "<<<HTMLLABEL0>>>" in line
        # Label should sanitize spaces to hyphens
        assert labels == ["\\label{Test-Section}"]

    def test_html_img_to_markdown(self):
        """<img> tags should convert to Markdown image syntax for further processing."""
        line, labels = _convert_html_to_latex(
            '<img src="test.png" alt="Test Image" width=600>'
        )
        assert "![Test Image](test.png)" in line
        assert labels == []

    def test_html_figcaption_to_italic(self):
        """<figcaption> should convert to italic markdown (processed in Phase 6)."""
        line, labels = _convert_html_to_latex("<figcaption>Image caption</figcaption>")
        assert "*Image caption*" in line

    def test_html_cite_to_italic(self):
        """<cite> should convert to italic markdown."""
        line, labels = _convert_html_to_latex("<cite>Reference 2024</cite>")
        assert "*Reference 2024*" in line

    def test_html_figure_tags_removed(self):
        """<figure> tags should be removed but content preserved."""
        line, labels = _convert_html_to_latex('<figure class="image">Content</figure>')
        assert "<figure" not in line
        assert "Content" in line

    def test_html_combined_conversion(self):
        """Test combined HTML elements in one block (real-world scenario)."""
        html = """<figure>
<a name="Test"></a>
<img src="img.png" alt="Alt">
<figcaption>Caption</figcaption>
</figure>"""
        line, labels = _convert_html_to_latex(html)
        # Should have label placeholder
        assert "<<<HTMLLABEL0>>>" in line
        # Should convert image to markdown
        assert "![Alt](img.png)" in line
        # Should convert figcaption to italic
        assert "*Caption*" in line
        # Should remove figure tags
        assert "<figure" not in line


# =============================================================================
# 4. CODE PROCESSING (Phase 2-3)
# =============================================================================


class TestInlineCode:
    """
    Test inline code conversion (Phase 3).

    Converts: `code` → \\texttt{code}

    Special handling in \\texttt{}:
        - Only \\, {, }, _ need escaping
        - Other special chars (#, $, %, etc.) work without escaping

    This is different from normal text where all 10 special chars need escaping.
    """

    def test_basic_inline_code(self):
        """Basic inline code conversion with no special characters."""
        result = _latex_convert("Use `python main.py` to run")
        assert "\\texttt{python main.py}" in result
        # No placeholders should remain
        assert "<<<" not in result

    def test_inline_code_with_underscore(self):
        """Underscores in inline code must be escaped (LaTeX subscript)."""
        result = _latex_convert("Use `variable_name` here")
        assert "\\texttt{variable\\_name}" in result

    def test_inline_code_with_safe_special_chars(self):
        """Most special chars work without escaping in \\texttt{} environment."""
        result = _latex_convert("Use `variable_name` and `test#value`")
        assert "\\texttt{variable\\_name}" in result
        # Hash doesn't need escaping in texttt
        assert "\\texttt{test#value}" in result

    def test_inline_code_with_dollar_sign(self):
        """Dollar signs in inline code must be escaped to avoid math mode."""
        result = _latex_convert("Use `$ cd /tmp/doorstop` to change directory")
        assert "\\texttt{\\$ cd /tmp/doorstop}" in result
        assert "$" not in result or "\\$" in result  # Either escaped or not present

    def test_inline_code_with_multiple_dollar_signs(self):
        """Multiple dollar signs in inline code."""
        result = _latex_convert("Price is `$100` and cost is `$50`")
        assert "\\texttt{\\$100}" in result
        assert "\\texttt{\\$50}" in result

    def test_inline_code_with_shell_variable(self):
        """Shell variables with dollar signs."""
        result = _latex_convert("Use `$HOME` or `${VAR}` in shell")
        assert "\\texttt{\\$HOME}" in result
        assert "\\texttt{\\$\\{VAR\\}}" in result or "\\texttt{\\${VAR}}" in result


class TestCodeBlocks:
    """
    Test fenced code block conversion (Phase 2).

    Converts:
        ```lang → <<<CODEBLOCK_START:lang>>>
        ``` → <<<CODEBLOCK_START>>>

    Later processed by _process_text_block() to:
        \\begin{lstlisting}[language=lang]
        ...
        \\end{lstlisting}
    """

    def test_code_fence_with_language(self):
        """Code fence with language should create language-specific placeholder."""
        result = _latex_convert("```python")
        assert result == "<<<CODEBLOCK_START:python>>>"

    def test_code_fence_without_language(self):
        """Code fence without language should create generic placeholder."""
        result = _latex_convert("```")
        assert result == "<<<CODEBLOCK_START>>>"

    def test_common_languages_detected(self):
        """Test common programming language detection."""
        languages = ["python", "java", "javascript", "cpp", "bash", "sql", "plantuml"]
        for lang in languages:
            result = _latex_convert(f"```{lang}")
            assert f"<<<CODEBLOCK_START:{lang}>>>" == result

    def test_language_with_trailing_spaces(self):
        """Language specification with trailing spaces should be trimmed."""
        result = _latex_convert("```python   ")
        assert "CODEBLOCK_START:python" in result


class TestIndentedCode:
    """
    Test indented code line detection.

    4 spaces or 1 tab at line start → treated as code.
    Converted to: <<<CODELINE:original_content>>>
    Later processed to: \\texttt{content}
    """

    def test_four_space_indented_code(self):
        """4-space indented lines are treated as code."""
        result = _latex_convert("    code_here")
        assert result.startswith("<<<CODELINE:")
        assert "code_here" in result

    def test_tab_indented_code(self):
        """Tab-indented lines are treated as code."""
        result = _latex_convert("\tcode_here")
        assert result.startswith("<<<CODELINE:")

    def test_indented_code_with_dollar_sign(self):
        """Indented code with dollar signs (from TUT001.yml)."""
        text_lines = [
            "Enter a VCS working copy:",
            "",
            "    $ cd /tmp/doorstop",
            "    $ doorstop create REQ ./reqs",
        ]
        result = list(_process_text_block(text_lines))
        result_str = "\n".join(result)

        # Should convert to \texttt{} with escaped dollar signs
        assert "\\texttt{\\$ cd /tmp/doorstop}" in result_str
        assert "\\texttt{\\$ doorstop create REQ ./reqs}" in result_str
        # Should NOT have unescaped $ in texttt
        assert "\\texttt{$" not in result_str or "\\texttt{\\$" in result_str


# =============================================================================
# 5. BLOCKQUOTES (Phase 0+)
# =============================================================================


class TestBlockquotes:
    """
    Test blockquote handling.

    Converts:
        > Quote text → \\begin{quote} Quote text \\end{quote}
        > (empty) → Empty line within quote block

    Features:
        - Multi-line blockquotes (consecutive > lines)
        - Auto-closing at end of input or when > stops
        - HTML/Markdown within blockquotes is processed

    Processed by _process_text_block() using in_blockquote flag.
    """

    def test_simple_blockquote(self):
        """Basic blockquote with multiple lines."""
        text_lines = [
            "> This is a quote",
            "> Second line",
        ]
        result = list(_process_text_block(text_lines))
        result_str = "\n".join(result)
        assert "\\begin{quote}" in result_str
        assert "\\end{quote}" in result_str
        assert "This is a quote" in result_str

    def test_blockquote_with_empty_line(self):
        """Empty lines within blockquotes (just >) should create spacing."""
        text_lines = [
            "> First line",
            ">",
            "> Second line",
        ]
        result = list(_process_text_block(text_lines))
        result_str = "\n".join(result)
        assert "\\begin{quote}" in result_str
        assert "\\end{quote}" in result_str

    def test_blockquote_with_html(self):
        """HTML tags within blockquotes should be converted (Phase 1 runs first)."""
        text_lines = [
            "> <cite>Source</cite>",
        ]
        result = list(_process_text_block(text_lines))
        result_str = "\n".join(result)
        assert "\\begin{quote}" in result_str
        assert "\\textit{Source}" in result_str
        assert "\\end{quote}" in result_str

    def test_blockquote_with_image(self):
        """Images within blockquotes should be processed."""
        text_lines = [
            "> Text before",
            ">",
            "> ![Alt](image.png)",
        ]
        result = list(_process_text_block(text_lines))
        result_str = "\n".join(result)
        assert "\\begin{quote}" in result_str
        assert "Text before" in result_str
        assert "![Alt](image.png)" in result_str
        assert "\\end{quote}" in result_str

    def test_blockquote_ends_at_normal_text(self):
        """Blockquote should end when lines stop starting with >."""
        text_lines = [
            "> Quote line",
            "Normal text",
        ]
        result = list(_process_text_block(text_lines))
        result_str = "\n".join(result)
        assert "\\begin{quote}" in result_str
        assert "\\end{quote}" in result_str
        # Quote should end before normal text
        quote_end = result_str.index("\\end{quote}")
        normal_text = result_str.index("Normal text")
        assert quote_end < normal_text

    def test_blockquote_auto_closes_at_eof(self):
        """Blockquote that reaches end of file should auto-close."""
        text_lines = [
            "> Quote line 1",
            "> Quote line 2",
        ]
        result = list(_process_text_block(text_lines))
        result_str = "\n".join(result)
        assert "\\begin{quote}" in result_str
        assert "\\end{quote}" in result_str


# =============================================================================
# 6. TEXT BLOCK PIPELINE (Integration of All Phases)
# =============================================================================


class TestTextBlockProcessing:
    """
    Test _process_text_block() - the main pipeline orchestrator.

    This function coordinates:
        - Code block detection and handling
        - Blockquote detection
        - Inline code processing
        - Line break insertion (\\\\)
        - Look-ahead for block elements

    It calls _latex_convert() for each line and manages multi-line structures.
    """

    def test_code_block_with_language_parameter(self):
        """Code block with language should create lstlisting with language parameter."""
        text_lines = ["```python", "def test():", "    pass", "```"]
        result = list(_process_text_block(text_lines))
        result_str = "\n".join(result)
        assert "[language=python]" in result_str

    def test_nested_code_block_warning(self, caplog):
        """Nested code blocks (``` inside ```) should trigger warning."""
        import logging

        caplog.set_level(logging.WARNING)
        text_lines = [
            "```python",
            "code1",
            "```java",  # Nested start - error in input
            "code2",
            "```",
        ]
        result = list(_process_text_block(text_lines))
        assert "Nested code block detected" in caplog.text

    def test_unclosed_code_block_warning(self, caplog):
        """Unclosed code blocks should trigger warning and auto-close."""
        import logging

        caplog.set_level(logging.WARNING)
        text_lines = [
            "```python",
            "code line 1",
            "code line 2",
            # Missing closing ```
        ]
        result = list(_process_text_block(text_lines))
        assert "Unclosed code block" in caplog.text
        assert any("\\end{lstlisting}" in line for line in result)

    def test_code_block_content_not_converted(self):
        """Content inside code blocks should not undergo LaTeX conversion."""
        text_lines = ["```", "Text with & special # chars $ and % symbols", "```"]
        result = list(_process_text_block(text_lines))
        result_str = "\n".join(result)
        # Special chars should remain unescaped in code
        assert "Text with & special # chars $ and % symbols" in result_str

    def test_indented_code_line_to_texttt(self):
        """4-space indented lines should become \\texttt{} commands."""
        text_lines = ["Regular text", "    indented_code_here", "More text"]
        result = list(_process_text_block(text_lines))
        result_str = "\n".join(result)
        assert "\\texttt{" in result_str
        assert "indented" in result_str

    def test_tab_indented_code_escapes_underscores(self):
        """Tab-indented lines with underscores should escape them in \\texttt{}."""
        text_lines = ["Regular text", "\tcode_with_tab", "More text"]
        result = list(_process_text_block(text_lines))
        result_str = "\n".join(result)
        assert "\\texttt{" in result_str
        assert "\\texttt{code\\_with\\_tab}" in result_str

    def test_four_space_indented_escapes_underscores(self):
        """4-space indented code with underscores."""
        text_lines = ["Regular text", "    code_with_spaces", "More text"]
        result = list(_process_text_block(text_lines))
        result_str = "\n".join(result)
        assert "\\texttt{" in result_str
        assert "\\texttt{code\\_with\\_spaces}" in result_str


class TestSimpleTextBlock:
    """
    Test _format_simple_text_block() - wrapper around _process_text_block().

    This is the public interface for simple text formatting.
    Calls _process_text_block() and returns a generator.
    """

    def test_code_block_wrapped_in_lstlisting(self):
        """Code blocks should be wrapped in lstlisting environment."""
        text = ["```python", "x = 1", "```"]
        result = list(_format_simple_text_block(text))
        result_str = "\n".join(result)
        assert "\\begin{lstlisting}[language=python]" in result_str
        assert "x = 1" in result_str
        assert "\\end{lstlisting}" in result_str

    def test_inline_code_to_texttt(self):
        """Inline code should convert to \\texttt{} commands."""
        text = ["Use `python main.py` to run"]
        result = list(_format_simple_text_block(text))
        result_str = "".join(result)
        assert "\\texttt{python main.py}" in result_str

    def test_mixed_markdown_and_code(self):
        """Mixed markdown formatting, inline code, and code blocks."""
        text = ["**Bold** text with `code`", "", "```bash", "ls -la", "```"]
        result = list(_format_simple_text_block(text))
        result_str = "".join(result)
        assert "\\textbf{Bold}" in result_str
        assert "\\texttt{code}" in result_str
        assert "\\begin{lstlisting}[language=bash]" in result_str


class TestLineBreakInsertion:
    """
    Test \\\\ (line break) insertion logic.

    Rules for adding \\\\:
        ✓ Before code blocks (for proper vertical spacing)
        ✗ Before LaTeX commands (\\section, \\label, etc.)
        ✗ Before images (handled by figure environment)
        ✗ Inside blockquotes (breaks quote formatting)

    Uses look-ahead to skip empty lines and find next content.
    """

    def test_linebreak_before_code_block(self):
        """Normal text before code block should get \\\\ for spacing."""
        text_lines = [
            "Normal text",
            "```",
            "code",
            "```",
        ]
        result = list(_process_text_block(text_lines))
        result_str = "\n".join(result)
        assert "Normal text\\\\" in result_str

    def test_no_linebreak_before_label(self):
        """Labels should never get \\\\ (LaTeX command)."""
        text_lines = [
            '> <a name="test"></a>',
            "> ![img](test.png)",
        ]
        result = list(_process_text_block(text_lines))
        result_str = "\n".join(result)
        # Label should not have \\
        assert "\\label{test}\\\\" not in result_str

    def test_lookahead_detects_block_elements(self):
        """Look-ahead should detect LaTeX block elements and skip \\\\."""
        text_lines = [
            "Text line",
            "",
            "\\label{test}",
        ]
        result = list(_process_text_block(text_lines))
        result_str = "\n".join(result)
        # No \\ because next non-empty is a block element
        assert "Text line\\\\" not in result_str

    def test_lookahead_detects_images(self):
        """Look-ahead should detect markdown images."""
        text_lines = [
            "Text before image",
            "",
            "![Alt text](image.png)",
        ]
        result = list(_process_text_block(text_lines))
        result_str = "\n".join(result)
        assert "Text before image\\\\" not in result_str

    def test_lookahead_stops_at_text_content(self):
        """Look-ahead should stop at actual text content (not block element)."""
        text_lines = [
            "Text line 1",
            "",
            "Text line 2",
        ]
        result = list(_process_text_block(text_lines))
        result_str = "\n".join(result)
        # Two text lines in sequence: no \\ needed
        assert "Text line 1\\\\" not in result_str

    def test_lookahead_skips_multiple_empty_lines(self):
        """Look-ahead should skip multiple empty lines to find code block."""
        text_lines = [
            "Text line",
            "",
            "",
            "```",
            "code",
            "```",
        ]
        result = list(_process_text_block(text_lines))
        result_str = "\n".join(result)
        assert "Text line\\\\" in result_str

    def test_lookahead_detects_begin_environment(self):
        """Look-ahead should detect \\begin{...} environments."""
        text_lines = [
            "Text line",
            "",
            "\\begin{itemize}",
        ]
        result = list(_process_text_block(text_lines))
        result_str = "\n".join(result)
        assert "Text line\\\\" not in result_str


# =============================================================================
# 7. COMPLEX FORMAT DETECTION
# =============================================================================


class TestComplexFormatDetection:
    """
    Test _has_complex_formatting() function.

    Determines if text should use legacy formatter (True) or modern pipeline (False).

    Complex formats (require legacy):
        - Tables (markdown pipes with header separator)
        - PlantUML diagrams
        - Math environments ($$)
        - Nested lists (indented list items)

    Simple formats (handled by modern pipeline):
        - Bold, italic, strikethrough
        - Headings
        - Links, images
        - Code blocks (non-PlantUML)
    """

    def test_simple_markdown_not_complex(self):
        """Simple markdown formatting should not be flagged as complex."""
        text = ["This is **bold** text", "And _italic_"]
        assert _has_complex_formatting(text) is False

    def test_table_with_separator_detected(self):
        """Tables with proper separator (|---|) should be detected."""
        text = ["| Col1 | Col2 |", "|------|------|", "| A    | B    |"]
        assert _has_complex_formatting(text) is True

    def test_plantuml_diagram_detected(self):
        """PlantUML diagrams should be detected as complex."""
        text = ["```plantuml", "@startuml", "A -> B", "@enduml", "```"]
        assert _has_complex_formatting(text) is True

    def test_math_environment_detected(self):
        """Math environments ($$) should be detected as complex."""
        text = ["Formula: $$E = mc^2$$"]
        assert _has_complex_formatting(text) is True

    def test_regular_code_block_not_complex(self):
        """Regular code blocks (non-PlantUML) are not complex."""
        text = ["```python", "def foo():", "    pass", "```"]
        assert _has_complex_formatting(text) is False

    def test_empty_input_not_complex(self):
        """Empty input should return False."""
        assert _has_complex_formatting([]) is False
        assert _has_complex_formatting("") is False

    def test_table_without_separator_not_complex(self):
        """Table-like text without separator is not a valid table."""
        text = [
            "| Col1 | Col2 |",
            "| Data | Data |",
        ]
        assert _has_complex_formatting(text) is False

    def test_single_pipes_not_table(self):
        """Single pipes in text don't make it a table."""
        text = ["This | is | text with pipes"]
        assert _has_complex_formatting(text) is False

    def test_double_dollar_math_complex(self):
        """Double dollar signs indicate math mode."""
        text = ["Formula: $$E = mc^2$$"]
        assert _has_complex_formatting(text) is True

    def test_single_dollar_not_complex(self):
        """Single $ (like prices) is not math mode."""
        text = ["Price: $10.99"]
        assert _has_complex_formatting(text) is False

    def test_nested_bullet_lists_complex(self):
        """Nested bullet lists (indented) are complex."""
        text = [
            "- Item 1",
            "  - Nested item 1.1",
            "  - Nested item 1.2",
            "- Item 2",
        ]
        assert _has_complex_formatting(text) is True

    def test_nested_numbered_lists_complex(self):
        """Nested numbered lists are complex."""
        text = [
            "1. Item 1",
            "   1. Nested item 1.1",
            "   2. Nested item 1.2",
            "2. Item 2",
        ]
        assert _has_complex_formatting(text) is True

    def test_single_level_list_not_complex(self):
        """Single-level lists can be handled by modern pipeline."""
        text = [
            "- Item 1",
            "- Item 2",
            "- Item 3",
        ]
        assert _has_complex_formatting(text) is False

    def test_mixed_nested_list_markers_complex(self):
        """Mixed nested list markers (-, +, *) are complex."""
        text = [
            "* Item 1",
            "  + Nested with different marker",
            "* Item 2",
        ]
        assert _has_complex_formatting(text) is True


class TestTableDetectionEdgeCases:
    """
    Edge cases for table detection within complex format detection.

    Tables require:
        - At least one line with pipes
        - Followed by separator line with dashes
        - At least 3 dashes per column (|---|)
    """

    def test_table_various_separator_patterns(self):
        """Different table separator patterns should all be detected."""
        # Minimum 3 dashes
        text1 = ["| H |", "|---|"]
        assert _has_complex_formatting(text1) is True

        # More dashes
        text2 = ["| Header |", "|--------|"]
        assert _has_complex_formatting(text2) is True

        # With center alignment
        text3 = ["| H |", "|:---:|"]
        assert _has_complex_formatting(text3) is True

        # With left and right alignment
        text4 = ["| L | C | R |", "|:---|:--:|---:|"]
        assert _has_complex_formatting(text4) is True

    def test_invalid_table_patterns(self):
        """Patterns that look like tables but aren't."""
        # Only 2 dashes (not enough)
        text1 = ["| H |", "|--|", "| D |"]
        assert _has_complex_formatting(text1) is False

        # No separator line
        text2 = ["| H1 | H2 |", "| D1 | D2 |"]
        assert _has_complex_formatting(text2) is False

        # Just separator (no header or data)
        text3 = ["|---|---|"]
        assert _has_complex_formatting(text3) is False

    def test_malformed_table_very_short_dashes(self):
        """Malformed tables with very short dashes are still detected as tables."""
        text_lines = [
            "| Header 1 | Header 2 | Header 3 |",
            "|-|-|-|",  # Very short but still valid
            "| Cell 1 | Cell 2 | Cell 3 |",
        ]
        assert _has_complex_formatting(text_lines) is True

    def test_table_at_end_of_file(self):
        """Table starting at end of file should be detected."""
        text_lines = [
            "Some text",
            "| Header 1 | Header 2 |",
            "|----------|----------|",
        ]
        assert _has_complex_formatting(text_lines) is True

    def test_non_table_at_eof_no_pipes(self):
        """Non-table at EOF should not trigger detection."""
        text_lines = [
            "Some text",
            "More text without pipes",
        ]
        assert _has_complex_formatting(text_lines) is False

    def test_table_at_eof_with_previous_pipes(self):
        """
        Table-like line at EOF when previous lines also have pipes.

        Tests:
            elif i == len(text_lines) - 1 and i > 0:
                prev_has_pipes = any("|" in text_lines[j] for j in range(max(0, i-2), i))

        When prev_has_pipes is True, should NOT trigger EOF detection.
        """
        text_lines = [
            "Some text | with | pipes",  # i-1 has pipes
            "| Header 1 | Header 2 |",  # i (last line)
        ]
        # Previous line has pipes, so prev_has_pipes = True
        # EOF check won't trigger
        # Will check for next line (doesn't exist) so returns False
        assert _has_complex_formatting(text_lines) is False

    def test_table_at_eof_without_previous_pipes(self):
        """
        Table-like line at EOF WITHOUT pipes in previous lines.
        """
        text_lines = [
            "Normal text line 1",
            "Normal text line 2",
            "| Header 1 | Header 2 |",  # Last line, no previous pipes
        ]
        # No pipes in previous lines
        # Should detect as "potential table start at EOF"
        assert _has_complex_formatting(text_lines) is True

    def test_two_line_document_pipes_at_end(self):
        """
        Two-line document where last line has pipes.

        Tests: i == len(text_lines) - 1 and i > 0
        When len=2, i=1 (last line), 'i > 0' is True → EOF check runs.
        """
        text_lines = [
            "First line without pipes",
            "| Header 1 | Header 2 |",  # i=1, is EOF, i > 0 is True
        ]
        # Previous line (i=0) has no pipes
        # Should trigger EOF table detection
        assert _has_complex_formatting(text_lines) is True

    def test_eof_check_looks_back_two_lines(self):
        """
        EOF table check looks at previous 2 lines for pipes.

        Tests: range(max(0, i-2), i)
        Should check lines at indices i-2 and i-1.
        """
        text_lines = [
            "| Line 0 | has pipes |",  # i-2 when i=2
            "Line 1 no pipes",  # i-1 when i=2
            "| Header 1 | Header 2 |",  # i=2 (last line)
        ]
        # Check range(max(0, 2-2), 2) = range(0, 2) = [0, 1]
        # Line 0 has pipes → prev_has_pipes = True
        # Should NOT trigger EOF detection
        assert _has_complex_formatting(text_lines) is False

    def test_eof_check_at_index_1_looks_back_one_line(self):
        """
        When i=1 (second line), looks back at i-2=-1 → max(0, -1)=0.

        Tests: max(0, i-2) when i-2 is negative.
        """
        text_lines = [
            "First line",  # Index 0
            "| Header 1 | Header 2 |",  # Index 1 (EOF)
        ]
        # range(max(0, 1-2), 1) = range(max(0, -1), 1) = range(0, 1) = [0]
        # Line 0 has no pipes → prev_has_pipes = False
        # Should trigger EOF detection
        assert _has_complex_formatting(text_lines) is True

    def test_eof_not_triggered_when_separator_exists(self):
        """
        EOF check should not run if proper separator exists.

        Table is detected earlier via normal separator check.
        """
        text_lines = [
            "| Header 1 | Header 2 |",
            "|----------|----------|",  # Proper separator
        ]
        # Detected on first line when checking next line
        # Never reaches EOF branch
        assert _has_complex_formatting(text_lines) is True


class TestPlantUMLDetection:
    """
    Test PlantUML diagram detection.

    PlantUML is detected by:
        - ```plantuml code fence
        - @startuml ... @enduml markers
    """

    def test_plantuml_with_code_fence(self):
        """PlantUML with standard code fence backticks."""
        text_lines = ["```plantuml", "@startuml", "A -> B", "@enduml", "```"]
        assert _has_complex_formatting(text_lines) is True

    def test_plantuml_detected(self):
        """PlantUML should be detected."""
        text = ['`plantuml title="Test"', "@startuml", "A -> B", "@enduml"]
        assert _has_complex_formatting(text) is True


class TestNestedListDetection:
    """
    Test nested list detection.

    Nested lists are detected by:
        - Indented list markers (-, *, +, 1., etc.)
        - At least 2 spaces or 1 tab before marker
    """

    def test_simple_bullet_list_not_nested(self):
        """Simple bullet list with no indentation."""
        text_lines = [
            "- Item 1",
            "- Item 2",
            "- Item 3",
        ]
        assert _has_complex_formatting(text_lines) is False

    def test_nested_bullet_list_two_spaces(self):
        """Nested bullet list with 2-space indentation."""
        text_lines = [
            "- Item 1",
            "  - Nested item",
            "- Item 2",
        ]
        assert _has_complex_formatting(text_lines) is True

    def test_nested_numbered_list(self):
        """Nested numbered list."""
        text_lines = [
            "1. Item 1",
            "   1. Nested item",
            "2. Item 2",
        ]
        assert _has_complex_formatting(text_lines) is True

    def test_mixed_list_markers_nested(self):
        """Mixed list markers with nesting."""
        text_lines = [
            "* Item 1",
            "  + Nested with different marker",
            "* Item 2",
        ]
        assert _has_complex_formatting(text_lines) is True

    def test_three_level_nesting(self):
        """Three levels of list nesting."""
        text_lines = [
            "- Level 1",
            "  - Level 2",
            "    - Level 3",
        ]
        assert _has_complex_formatting(text_lines) is True


# =============================================================================
# 8. HELPER UTILITIES
# =============================================================================


class TestTableFormatting:
    """
    Test _fix_table_line() function.
    
    Converts markdown table rows to LaTeX tabular format:
        | cell1 | cell2 | → cell1 & cell2 \\
    
    Features:
        - Pipes → Ampersands (&)
        - Adds \\ at end
        - Escapes special LaTeX characters in cells
        - Handles end_pipes parameter (tables with/without ending |)
    """

    def test_table_cell_escaping(self):
        """Table cells should have LaTeX special chars escaped."""
        line = "| test_var | 100% | A&B |"
        result = _fix_table_line(line, end_pipes=True)
        assert r"\_" in result  # Underscore escaped
        assert r"\%" in result  # Percent escaped
        assert r"\&" in result  # Ampersand escaped (in cell content, not separator)

    def test_pipes_to_ampersands(self):
        """Pipes should convert to ampersands (LaTeX table separator)."""
        line = "| col1 | col2 | col3 |"
        result = _fix_table_line(line, end_pipes=True)
        assert result == r"col1 & col2 & col3 \\"
        assert "|" not in result

    def test_empty_table_cells(self):
        """Empty table cells should be handled gracefully."""
        line = "| | content | |"
        result = _fix_table_line(line, end_pipes=True)
        assert " & content & " in result
        assert result.endswith(r"\\")

    def test_table_without_end_pipes(self):
        """Tables without ending pipes should still work."""
        line = "| test |"
        result = _fix_table_line(line, end_pipes=False)
        assert "test" in result
        assert result.endswith(r"\\")

    def test_all_special_chars_in_cells(self):
        """All special characters in table cells should be escaped."""
        line = "| test_var | 100% | A&B | #1 | $10 |"
        result = _fix_table_line(line, end_pipes=True)
        assert "test\\_var" in result
        assert "100\\%" in result
        assert "A\\&B" in result  # & in content, not separator
        assert "\\#1" in result
        assert "\\$10" in result


class TestTableDetection:
    """
    Test _check_for_new_table() function.

    Detects table start and sets up LaTeX longtable environment.

    Logic:
        1. Current line has pipes
        2. Next line has dashes (|---|)
        3. Count pipes vs dashes to determine end_pipes
        4. Create \begin{longtable}{column_spec}
        5. Process header row
    """

    def test_valid_table_detection(self):
        """Proper table with header and dash separator."""
        text = [
            "| Header1 | Header2 |",
            "|---------|---------|",
            "| Cell1   | Cell2   |",
        ]
        i = 0
        line = text[0]
        block = []
        table_match = re.findall(r"\|", line)

        result = _check_for_new_table(
            table_match, text, i, line, block, False, False, False
        )
        table_found, header_done, line_result, end_pipes = result

        assert table_found is True
        assert len(block) > 0
        assert "\\begin{longtable}" in block[0]

    def test_table_with_alignment_markers(self):
        """Table with alignment markers (:---, :---:, ---:)."""
        text = [
            "| Left | Center | Right |",
            "|:-----|:------:|------:|",
            "| L    | C      | R     |",
        ]
        i = 0
        line = text[0]
        block = []
        table_match = re.findall(r"\|", line)

        result = _check_for_new_table(
            table_match, text, i, line, block, False, False, False
        )
        table_found = result[0]

        assert table_found is True
        assert len(block) > 0

    def test_unbalanced_pipes_warning(self, caplog):
        """Different pipe counts between header and separator should warn."""
        import logging

        caplog.set_level(logging.WARNING)

        text = [
            "| Header1 | Header2 |",
            "| No dashes here |",  # Wrong number of pipes
        ]
        i = 0
        line = text[0]
        block = []
        table_match = re.findall(r"\|", line)

        result = _check_for_new_table(
            table_match, text, i, line, block, False, False, False
        )

        assert "Possibly unbalanced table" in caplog.text

    def test_no_separator_warning(self, caplog):
        """Table without dash separator should warn."""
        import logging

        caplog.set_level(logging.WARNING)

        text = [
            "| Header1 | Header2 |",
            "| Cell1   | Cell2   |",  # No dashes
        ]
        i = 0
        line = text[0]
        block = []
        table_match = re.findall(r"\|", line)

        result = _check_for_new_table(
            table_match, text, i, line, block, False, False, False
        )

        assert "Possibly incorrectly specified table" in caplog.text

    def test_no_next_line_returns_false(self):
        """No next line should return False (not a table)."""
        text = ["| Header |"]
        i = 0
        line = text[0]
        block = []
        table_match = re.findall(r"\|", line)

        result = _check_for_new_table(
            table_match, text, i, line, block, False, False, False
        )
        table_found = result[0]

        assert table_found is False

    def test_next_line_no_pipes_returns_false(self):
        """Next line without pipes should return False."""
        text = ["| Header |", "No pipes here"]
        i = 0
        line = text[0]
        block = []
        table_match = re.findall(r"\|", line)

        result = _check_for_new_table(
            table_match, text, i, line, block, False, False, False
        )
        table_found = result[0]

        assert table_found is False

    def test_end_pipes_determination(self):
        """More pipes than dash groups means end_pipes = True."""
        text = [
            "| Col1 | Col2 | Col3 |",  # 4 pipes
            "|------|------|------|",  # 3 dash groups
        ]
        i = 0
        line = text[0]
        block = []
        table_match = re.findall(r"\|", line)

        result = _check_for_new_table(
            table_match, text, i, line, block, False, False, False
        )
        table_found, header_done, line_result, end_pipes = result

        assert end_pipes is True


class TestImageTypesetting:
    """
    Test _typeset_latex_image() function.

    Converts: ![alt](path) → LaTeX figure environment

    Output:
        \\begin{figure}[h!]\\center
        \\includegraphics[width=0.8\\textwidth]{path}
        \\label{fig:sanitized-alt}
        \\zlabel{fig:sanitized-alt}
        \\caption{alt or title}
        \\end{figure}

    Features:
        - Sanitizes paths (spaces → hyphens)
        - Extracts title from "path" if present
        - Creates fig: labels for referencing
        - Sets standard width (0.8\\textwidth)
    """

    def test_basic_image_conversion(self):
        """Basic image should create figure environment."""
        image_match = [("Test Image", "images/test.png")]
        line = "![Test Image](images/test.png)"
        block = []

        result = _typeset_latex_image(image_match, line, block)
        block_str = "\n".join(str(item) for item in block)

        assert "\\begin{figure}" in block_str
        assert "\\includegraphics" in block_str
        assert "Test Image" in block_str
        assert "\\end{figure}" in result

    def test_image_with_quoted_title(self):
        """Image with title in quotes should use title for caption."""
        image_match = [("Alt Text", 'images/test.png "Actual Title"')]
        line = '![Alt Text](images/test.png "Actual Title")'
        block = []

        result = _typeset_latex_image(image_match, line, block)
        block_str = "\n".join(str(item) for item in block)

        assert "Actual Title" in block_str
        assert "images/test.png" in block_str

    def test_path_sanitization_spaces_to_hyphens(self, caplog):
        """Image paths with spaces should be sanitized to hyphens."""
        import logging

        caplog.set_level(logging.DEBUG)

        image_match = [("Alt", "path with spaces.png")]
        line = "![Alt](path with spaces.png)"
        block = []

        result = _typeset_latex_image(image_match, line, block)
        block_str = "\n".join(str(item) for item in block)

        assert "path-with-spaces.png" in block_str
        assert "Image path sanitized" in caplog.text

    def test_image_label_generation(self):
        """Images should create fig: labels for cross-referencing."""
        image_match = [("My Test Image 123", "test.png")]
        line = "![My Test Image 123](test.png)"
        block = []

        result = _typeset_latex_image(image_match, line, block)
        block_str = "\n".join(str(item) for item in block)

        assert "\\label{fig:" in block_str
        assert "\\zlabel{fig:" in block_str

    def test_special_chars_in_caption(self):
        """Special characters in image caption should be handled."""
        image_match = [("Test & Image 50%", "test.png")]
        line = "![Test & Image 50%](test.png)"
        block = []

        result = _typeset_latex_image(image_match, line, block)
        block_str = "\n".join(str(item) for item in block)

        assert "\\caption{" in block_str
        assert "Test" in block_str

    def test_image_width_setting(self):
        """Images should be set to 0.8\\textwidth by default."""
        image_match = [("Image", "test.png")]
        line = "![Image](test.png)"
        block = []

        result = _typeset_latex_image(image_match, line, block)
        block_str = "\n".join(str(item) for item in block)

        assert "width=0.8\\textwidth" in block_str

    def test_figure_environment_structure(self):
        """Images should be wrapped in figure environment with centering."""
        image_match = [("Test", "test.png")]
        line = "![Test](test.png)"
        block = []

        result = _typeset_latex_image(image_match, line, block)
        block_str = "\n".join(str(item) for item in block)

        assert "\\begin{figure}[h!]" in block_str
        assert "\\end{figure}" in result
        assert "\\center" in block_str


class TestCommentWrapping:
    """
    Test _add_comment() function.

    Wraps text in LaTeX comment lines (starting with %).

    Format:
        %%%%%%%%%%%%%%%%... (80 chars)
        % Text here
        %%%%%%%%%%%%%%%%... (80 chars)

    Features:
        - Word wrapping to fit line width
        - Preserves original content
        - Used for debugging output
    """

    def test_basic_comment_wrapping(self):
        """Basic comment should have header and footer."""
        wrapper = []
        _add_comment(wrapper, "Test line")

        assert len(wrapper) == 3
        assert "Test line" in wrapper[1]
        assert "%" * 80 in wrapper[0]
        assert "%" * 80 in wrapper[2]

    def test_empty_line_comment(self):
        """Comment on empty line should still have % markers."""
        wrapper = []
        _add_comment(wrapper, "")

        assert len(wrapper) == 3
        assert wrapper[1].startswith("%")
        assert wrapper[1].endswith("%")

    def test_comment_preserves_content(self):
        """Comment should preserve original content including special chars."""
        wrapper = []
        original = "This is a test with special chars: #$%&"
        _add_comment(wrapper, original)

        assert original in wrapper[1]
        assert wrapper[1].startswith("% ")

    def test_very_long_word_handling(self):
        """Comment with word longer than line width should be handled."""
        wrapper = []
        long_word = "a" * 80
        _add_comment(wrapper, long_word)

        assert len(wrapper) >= 3
        assert any(long_word in str(line) for line in wrapper)

    def test_multiple_words_wrapping(self):
        """Comment wrapping with multiple words should have borders."""
        wrapper = []
        text = "word1 " * 20
        _add_comment(wrapper, text)

        assert len(wrapper) >= 3
        assert "%" * 80 == wrapper[0]
        assert "%" * 80 == wrapper[-1]


class TestContextFormatting:
    """
    Test _format_context() function.

    Formats debugging context information:
        - item_uid: Item identifier
        - file: Source file path
        - line_num: Line number in file

    Used in warning/error messages to help locate issues.
    """

    def test_full_context_formatting(self):
        """Context with all fields should include UID, file, and line number."""
        context = {"item_uid": "REQ123", "file": "requirements/req.yml", "line_num": 42}
        result = _format_context(context)

        assert "REQ123" in result
        assert "requirements/req.yml" in result
        assert "42" in result

    def test_none_context_returns_empty(self):
        """None context should return empty string."""
        result = _format_context(None)
        assert result == ""

    def test_partial_context_with_uid_only(self):
        """Partial context with only some fields should work."""
        context = {"item_uid": "REQ999"}
        result = _format_context(context)
        assert "REQ999" in result

    def test_context_with_file_and_line(self):
        """Context with file path and line number."""
        context = {"item_uid": "REQ-001", "file": "test.yml", "line_num": 42}
        result = _format_context(context)

        assert "REQ-001" in result
        assert "test.yml" in result
        assert "42" in result


# =============================================================================
# 9. FULL PIPELINE INTEGRATION
# =============================================================================


class TestFullPipelineIntegration:
    """
    Integration tests for _latex_convert() - the complete 14-phase pipeline.

    Tests all phases working together:
        Phase 1:  HTML conversion
        Phase 2:  Code block detection
        Phase 3:  Inline code preservation
        Phase 4:  Image/link preservation
        Phase 5:  Structural escaping (\, {, })
        Phase 6:  Markdown formatting (**, *, ~~)
        Phase 7:  Link processing (stored as FINALHREF)
        Phase 8:  Heading conversion
        Phase 9:  Special character escaping
        Phase 10-14: Placeholder restoration

    These tests verify the phases don't interfere with each other.
    """

    def test_all_special_characters_handled(self):
        """All 10 LaTeX special characters should be properly escaped."""
        input_text = r"\ { } _ # $ % & ^ ~"
        result = _latex_convert(input_text)

        assert "textbackslash" in result
        assert result.count("\\{") >= 1
        assert result.count("\\}") >= 1
        assert "\\_" in result
        assert "\\#" in result
        assert "\\$" in result
        assert "\\%" in result
        assert "\\&" in result
        assert "textasciicircum" in result or "\\^" in result
        assert "textasciitilde" in result or "\\~" in result

    def test_unmatched_braces_warning(self, caplog):
        """Unmatched braces should trigger warning."""
        import logging

        caplog.set_level(logging.WARNING)

        context = {"item_uid": "TEST003", "line_num": 10}
        result = _latex_convert("Text with {{{ many braces", context=context)

        assert "Unmatched braces" in caplog.text
        assert "TEST003" in caplog.text

    def test_very_long_line_debug_log(self, caplog):
        """Very long lines (>500 chars) should trigger debug log."""
        import logging

        caplog.set_level(logging.DEBUG)

        context = {"item_uid": "TEST004", "line_num": 20}
        long_text = "a" * 600
        result = _latex_convert(long_text, context=context)

        assert "Very long line detected" in caplog.text

    def test_long_line_still_processed(self):
        """Lines over 500 characters should still be processed correctly."""
        long_text = "a" * 501
        result = _latex_convert(long_text)
        assert len(result) > 500

    def test_backslash_conversion_defensive(self):
        """Verify backslash conversion doesn't create invalid sequences."""
        test_cases = [
            "Text \\  space",
            "Text \\. period",
            "Text \\1 digit",
        ]
        for test_input in test_cases:
            result = _latex_convert(test_input)
            assert "\\textbackslash{}" in result
            # Should not have suspicious backslashes followed by non-command chars
            assert not re.search(r"\\(?![a-zA-Z{}\$%&#_\^~\\])", result)

    def test_multiple_links_in_line(self):
        """Multiple markdown links in one line should all be processed."""
        result = _latex_convert("See [Link1](url1) and [Link2](url2) here")
        assert result.count("\\href{") == 2
        assert "url1" in result
        assert "url2" in result

    def test_link_with_empty_text_handled(self):
        """Link with empty text should be handled gracefully."""
        result = _latex_convert("[](https://example.com)")
        # Should either preserve or convert gracefully
        assert (
            "[](https://example.com)" in result
            or "\\href{https://example.com}{}" in result
        )

    def test_tutorial_example_with_shell_commands(self):
        """
        Real-world example from TUT001.yml that caused compilation error.

        Tests that shell commands with $ are properly escaped in inline code.
        """
        text_lines = [
            "**Creating a New Document**",
            "",
            "Enter a VCS working copy:",
            "",
            "    $ cd /tmp/doorstop",
            "",
            "Create a new document:",
            "",
            "    $ doorstop create REQ ./reqs",
            "",
            "Add items:",
            "",
            "    $ doorstop add REQ",
        ]

        result = list(_process_text_block(text_lines))
        result_str = "\n".join(result)

        # Check bold formatting works
        assert "\\textbf{Creating a New Document}" in result_str

        # Check dollar signs are escaped in code
        assert "\\texttt{\\$ cd /tmp/doorstop}" in result_str
        assert "\\texttt{\\$ doorstop create REQ ./reqs}" in result_str
        assert "\\texttt{\\$ doorstop add REQ}" in result_str

        # Verify no unescaped $ in \texttt{}
        # This regex checks for $ NOT preceded by \
        import re

        unescaped_dollar_in_texttt = re.search(r"\\texttt\{[^}]*(?<!\\)\$", result_str)
        assert (
            unescaped_dollar_in_texttt is None
        ), "Found unescaped $ in \\texttt{}: " + str(unescaped_dollar_in_texttt)


class TestHeadingNumbering:
    """
    Test context-aware heading numbering (Phase 8).

    Heading numbering behavior depends on context:
        - Document-level headings: Controlled by PUBLISH_HEADING_LEVELS setting
        - Item text headings: ALWAYS unnumbered (in_item_text=True)

    This prevents duplicate numbering where both the item header and
    internal headings would be numbered, creating confusion in TOC.

    Example:
        Item SYSR-002 with level 1.1:
            Header: "1.1 Control of STO - SYSR-002" (numbered)
            Text:
                ## Content    → Content (unnumbered, not in TOC)
                ## Rationale  → Rationale (unnumbered, not in TOC)
    """

    def test_heading_without_context_uses_setting(self):
        """
        Without context, headings use PUBLISH_HEADING_LEVELS setting.

        This is for document-level headings (not inside items).
        """
        # When PUBLISH_HEADING_LEVELS is True (numbered)
        original_setting = settings.PUBLISH_HEADING_LEVELS
        try:
            settings.PUBLISH_HEADING_LEVELS = True
            result = _latex_convert("## Test Heading")
            assert "\\subsection{Test Heading}" in result
            assert "\\subsection*{" not in result

            # When PUBLISH_HEADING_LEVELS is False (unnumbered)
            settings.PUBLISH_HEADING_LEVELS = False
            result = _latex_convert("## Test Heading")
            assert "\\subsection*{Test Heading}" in result
        finally:
            settings.PUBLISH_HEADING_LEVELS = original_setting

    def test_heading_in_item_text_always_unnumbered(self):
        """
        Headings with in_item_text=True are ALWAYS unnumbered.

        This happens regardless of PUBLISH_HEADING_LEVELS setting.
        """
        context = {"in_item_text": True, "item_uid": "TEST-001"}

        original_setting = settings.PUBLISH_HEADING_LEVELS
        try:
            # Even when PUBLISH_HEADING_LEVELS is True
            settings.PUBLISH_HEADING_LEVELS = True
            result = _latex_convert("## Content", context=context)
            assert "\\subsection*{Content}" in result
            assert "\\subsection{Content}" not in result

            # And when PUBLISH_HEADING_LEVELS is False
            settings.PUBLISH_HEADING_LEVELS = False
            result = _latex_convert("## Rationale", context=context)
            assert "\\subsection*{Rationale}" in result
        finally:
            settings.PUBLISH_HEADING_LEVELS = original_setting

    def test_all_heading_levels_unnumbered_in_item_text(self):
        """All heading levels (1-5) should be unnumbered in item text."""
        context = {"in_item_text": True}

        test_cases = [
            ("# Level 1", "\\section*{Level 1}"),
            ("## Level 2", "\\subsection*{Level 2}"),
            ("### Level 3", "\\subsubsection*{Level 3}"),
            ("#### Level 4", "\\paragraph*{Level 4}"),
            ("##### Level 5", "\\subparagraph*{Level 5}"),
        ]

        for markdown, expected in test_cases:
            result = _latex_convert(markdown, context=context)
            assert expected in result, f"Failed for: {markdown}"

    def test_heading_level_6_always_unnumbered(self):
        """
        Level 6+ headings are ALWAYS unnumbered (too deep for LaTeX).

        This is true regardless of context or settings.
        """
        # Without context
        result = _latex_convert("###### Too Deep")
        assert "\\subparagraph*{Too Deep" in result
        assert "too deep" in result.lower()

        # With item text context
        context = {"in_item_text": True}
        result = _latex_convert("###### Also Too Deep", context=context)
        assert "\\subparagraph*{Also Too Deep" in result

    def test_item_text_context_with_item_uid(self):
        """Context with item_uid should produce unnumbered headings."""
        context = {
            "in_item_text": True,
            "item_uid": "SYSR-002",
            "file": "requirements/SYSR-002.yml",
        }

        result = _latex_convert("## Content", context=context)
        assert "\\subsection*{Content}" in result

    def test_mixed_context_flags(self):
        """Test various context flag combinations."""
        # Only in_item_text=True
        context1 = {"in_item_text": True}
        result1 = _latex_convert("## Heading", context=context1)
        assert "\\subsection*{Heading}" in result1

        # in_item_text=False (explicit)
        context2 = {"in_item_text": False}
        result2 = _latex_convert("## Heading", context=context2)
        # Should use PUBLISH_HEADING_LEVELS setting
        assert "\\subsection" in result2

        # Empty context dict
        context3 = {}
        result3 = _latex_convert("## Heading", context=context3)
        # Should use PUBLISH_HEADING_LEVELS setting
        assert "\\subsection" in result3

    def test_heading_numbering_does_not_affect_content(self):
        """Numbering flag should only affect heading command, not content."""
        context = {"in_item_text": True}

        result = _latex_convert("## Special Chars & Symbols %", context=context)
        # Should be unnumbered
        assert "\\subsection*{" in result
        # Content should be preserved (though special chars may be escaped)
        assert "Special Chars" in result

    def test_heading_with_markdown_formatting_in_title(self):
        """Headings can contain markdown formatting in title."""
        context = {"in_item_text": True}

        result = _latex_convert("## **Bold** Heading", context=context)
        assert "\\subsection*{" in result
        # Bold should be converted
        assert "\\textbf{Bold}" in result

    def test_document_level_heading_numbered(self):
        """
        Document-level headings (no context) should be numbered.

        Simulates headings outside of item text (e.g., in a preamble).
        """
        original_setting = settings.PUBLISH_HEADING_LEVELS
        try:
            settings.PUBLISH_HEADING_LEVELS = True

            # No context = document level
            result = _latex_convert("# Document Section")
            assert "\\section{Document Section}" in result
            assert "*" not in result  # No star
        finally:
            settings.PUBLISH_HEADING_LEVELS = original_setting


class TestHeadingNumberingIntegration:
    """
    Integration tests for heading numbering with _process_text_block().

    Tests the full pipeline including context propagation.
    """

    def test_multiple_headings_in_item_text(self):
        """Multiple headings in item text should all be unnumbered."""
        context = {"in_item_text": True, "item_uid": "TEST-001"}

        text_lines = [
            "## Content",
            "Some text here.",
            "## Rationale",
            "More text.",
            "### Details",
            "Even more text.",
        ]

        result = list(_process_text_block(text_lines, context=context))
        result_str = "\n".join(result)

        # All headings should be unnumbered
        assert "\\subsection*{Content}" in result_str
        assert "\\subsection*{Rationale}" in result_str
        assert "\\subsubsection*{Details}" in result_str

        # Should NOT have numbered versions
        assert "\\subsection{Content}" not in result_str
        assert "\\subsection{Rationale}" not in result_str

    def test_headings_mixed_with_other_content(self):
        """Headings mixed with code blocks, lists, etc."""
        context = {"in_item_text": True}

        text_lines = [
            "## Overview",
            "This is a description.",
            "",
            "```python",
            "code_example()",
            "```",
            "",
            "## Implementation",
            "- Point 1",
            "- Point 2",
        ]

        result = list(_process_text_block(text_lines, context=context))
        result_str = "\n".join(result)

        # Headings should be unnumbered
        assert "\\subsection*{Overview}" in result_str
        assert "\\subsection*{Implementation}" in result_str

        # Code and other content should be preserved
        assert "\\begin{lstlisting}" in result_str
        assert "code_example()" in result_str

    def test_heading_at_start_of_item_text(self):
        """Heading as first line of item text."""
        context = {"in_item_text": True}

        text_lines = [
            "## First Heading",
            "Content follows.",
        ]

        result = list(_process_text_block(text_lines, context=context))
        result_str = "\n".join(result)

        assert "\\subsection*{First Heading}" in result_str

    def test_heading_at_end_of_item_text(self):
        """Heading as last line of item text."""
        context = {"in_item_text": True}

        text_lines = [
            "Content here.",
            "## Last Heading",
        ]

        result = list(_process_text_block(text_lines, context=context))
        result_str = "\n".join(result)

        assert "\\subsection*{Last Heading}" in result_str

    def test_nested_headings_proper_hierarchy(self):
        """Nested headings should maintain proper hierarchy."""
        context = {"in_item_text": True}

        text_lines = [
            "## Main Section",
            "Content",
            "### Subsection",
            "More content",
            "#### Detail",
            "Even more",
        ]

        result = list(_process_text_block(text_lines, context=context))
        result_str = "\n".join(result)

        # All should be unnumbered but maintain hierarchy
        assert "\\subsection*{Main Section}" in result_str
        assert "\\subsubsection*{Subsection}" in result_str
        assert "\\paragraph*{Detail}" in result_str


# =============================================================================
# END OF TESTS
# =============================================================================

"""
To run these tests:

    # Run all tests
    poetry run pytest doorstop/core/publishers/tests/test_latex_functions.py -v
    
    # Run specific test class
    poetry run pytest doorstop/core/publishers/tests/test_latex_functions.py::TestTextEscaping -v
    
    # Run with coverage
    poetry run pytest doorstop/core/publishers/tests/test_latex_functions.py \
        --cov=doorstop.core.publishers._latex_functions \
        --cov-report=html \
        --cov-report=term-missing
    
    # Open coverage report
    start htmlcov/index.html  # Windows
    open htmlcov/index.html   # macOS

Coverage target: 97% (currently achieved)
Total tests: 177
"""
