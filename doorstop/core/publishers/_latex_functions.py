# SPDX-License-Identifier: LGPL-3.0-only

"""Functions to publish LaTeX documents."""

import re

from doorstop import common, settings

log = common.logger(__name__)


def _add_comment(wrapper, text):
    """Add comments to the .tex output file in a pretty way."""
    wrapper.append("%" * 80)
    words = text.split(" ")
    line = "%"
    for word in words:
        if len(line) + len(word) <= 77:
            line += " %s" % word
        else:
            line += " " * (79 - len(line)) + "%"
            wrapper.append(line)
            line = "% " + word
    line += " " * (79 - len(line)) + "%"
    wrapper.append(line)
    wrapper.append("%" * 80)

    return wrapper

def _latex_convert(line, context=None):
    """
    Convert markdown line to LaTeX format.
    
    Processing order is CRITICAL:
    0a. Preserve inline code segments
    0b. Preserve URLs from markdown links
    1. Structural escaping (backslash, braces)
    2. Markdown formatting (bold, italic, strikethrough)
    3. Convert preserved links to \href{}
    4. Headings
    5. Remaining special characters
    6. Restore inline code
    """
    original_line = line
    
    if context:
        item_uid = context.get('item_uid', 'unknown')
        source_file = context.get('file', 'unknown')
        line_num = context.get('line_num', '?')
        context_info = f" [Item: {item_uid}, Line: {line_num}]"
    else:
        context_info = ""
    
    #############################
    ## Phase 0a: Code block detection
    #############################
    
    if line.strip().startswith("```"):
        lang_match = re.match(r"^```(\w+)?", line.strip())
        if lang_match and lang_match.group(1):
            lang = lang_match.group(1)
            return f"%%CODEBLOCK_START:{lang}%%"
        else:
            return "%%CODEBLOCK_START%%"
    
    if re.match(r"^(    |\t)", line) and line.strip():
        code_content = line.lstrip()
        return f"%%CODELINE:{code_content}%%"
    
    #############################
    ## Phase 0b: Preserve inline code AND markdown links
    #############################
    
    # Inline code: `code`
    inline_code_pattern = r"`([^`]+)`"
    code_segments = []
    
    def protect_inline_code(match):
        code_segments.append(match.group(1))
        return f"%%INLINECODE{len(code_segments)-1}%%"
    
    line = re.sub(inline_code_pattern, protect_inline_code, line)
    
    # Markdown links: [text](url)
    # MUST preserve URLs before markdown formatting!
    link_segments = []
    
    def protect_markdown_link(match):
        """Preserve entire link, process later"""
        link_text = match.group(1)
        link_url = match.group(2)
        link_segments.append((link_text, link_url))
        return f"%%MDLINK{len(link_segments)-1}%%"
    
    line = re.sub(
        r"\[([^\]]+)\]\(([^\)]+)\)",
        protect_markdown_link,
        line
    )
    
    #############################
    ## Phase 1: Structural escaping
    #############################
    
    line = re.sub(r"\\", r"\\textbackslash{}", line)
    line = re.sub(r"\{", r"\\{", line)
    line = re.sub(r"\}", r"\\}", line)
    
    #############################
    ## Phase 2: Markdown formatting
    #############################
    
    line = re.sub(r"\*\*(.*?)\*\*", r"\\textbf{\1}", line)
    line = re.sub(r"__(.*?)__", r"\\textbf{\1}", line)
    line = re.sub(r"(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)", r"\\textit{\1}", line)
    line = re.sub(r"(?<!\\)_(?!_)(.*?)(?<!\\)_(?!_)", r"\\textit{\1}", line)
    line = re.sub(r"~~(.*?)~~", r"\\sout{\1}", line)
    
    #############################
    ## Phase 2b: Restore and convert markdown links
    #############################
    
    for i, (link_text, link_url) in enumerate(link_segments):
        # Process link_text for markdown formatting (it's already been through Phase 2)
        # But we need to process it NOW because it was protected
        link_text_processed = link_text
        
        # Apply markdown formatting to link text
        link_text_processed = re.sub(r"\*\*(.*?)\*\*", r"\\textbf{\1}", link_text_processed)
        link_text_processed = re.sub(r"__(.*?)__", r"\\textbf{\1}", link_text_processed)
        link_text_processed = re.sub(r"(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)", r"\\textit{\1}", link_text_processed)
        link_text_processed = re.sub(r"(?<!\\)_(?!_)(.*?)(?<!\\)_(?!_)", r"\\textit{\1}", link_text_processed)
        link_text_processed = re.sub(r"~~(.*?)~~", r"\\sout{\1}", link_text_processed)
        
        # Escape special chars in URL (but NOT underscores - they're part of URL)
        link_url_safe = link_url.replace("#", r"\#")
        link_url_safe = link_url_safe.replace("%", r"\%")
        link_url_safe = link_url_safe.replace("&", r"\&")
        # Note: DO NOT escape _ in URLs!
        
        # Replace placeholder with \href
        line = line.replace(
            f"%%MDLINK{i}%%",
            f"\\href{{{link_url_safe}}}{{{link_text_processed}}}"
        )
    
    #############################
    ## Phase 3: Headings
    #############################
    
    if settings.PUBLISH_HEADING_LEVELS:
        star = ""
    else:
        star = "*"
    
    if re.match(r"^#{6,} ", line):
        log.warning(
            f"Heading level too deep (>5){context_info}. "
            f"Line: '{original_line[:60]}...'"
        )
    
    line = re.sub(
        r"^#{6,} (.*)$",
        r"\\subparagraph" + star + r"{\1 \\textbf{NOTE: This heading level is too deep for LaTeX.}}",
        line,
    )
    line = re.sub(r"^##### (.*)$", r"\\subparagraph" + star + r"{\1}", line)
    line = re.sub(r"^#### (.*)$", r"\\paragraph" + star + r"{\1}", line)
    line = re.sub(r"^### (.*)$", r"\\subsubsection" + star + r"{\1}", line)
    line = re.sub(r"^## (.*)$", r"\\subsection" + star + r"{\1}", line)
    line = re.sub(r"^# (.*)$", r"\\section" + star + r"{\1}", line)
    
    #############################
    ## Phase 4: Remaining special characters
    #############################
    
    line = re.sub(r"#", r"\\#", line)
    line = re.sub(r"\$", r"\\$", line)
    line = re.sub(r"%", r"\\%", line)
    line = re.sub(r"&", r"\\&", line)
    line = re.sub(r"(?<!\\)_", r"\\_", line)  # NOW safe to escape underscores
    line = re.sub(r"\^", r"\\textasciicircum{}", line)
    line = re.sub(r"~", r"\\textasciitilde{}", line)
    
    #############################
    ## Phase 5: Restore inline code
    #############################
    
    for i, code_content in enumerate(code_segments):
        code_escaped = code_content.replace("\\", r"\textbackslash{}")
        code_escaped = code_escaped.replace("{", r"\{")
        code_escaped = code_escaped.replace("}", r"\}")
        code_escaped = code_escaped.replace("_", r"\_")
        code_escaped = code_escaped.replace("^", r"\textasciicircum{}")
        code_escaped = code_escaped.replace("~", r"\textasciitilde{}")
        code_escaped = code_escaped.replace("#", r"\#")
        code_escaped = code_escaped.replace("$", r"\$")
        code_escaped = code_escaped.replace("%", r"\%")
        code_escaped = code_escaped.replace("&", r"\&")
        
        line = line.replace(
            f"%%INLINECODE{i}%%",
            r"\texttt{" + code_escaped + "}"
        )
    
    #############################
    ## Debug logging
    #############################
    
    if r"\textbackslash{}\textbackslash{}" in line:
        log.warning(
            f"Double backslash detected{context_info}. "
            f"Original: '{original_line[:60]}...' "
            f"Converted: '{line[:60]}...'"
        )
    
    open_braces = line.count(r"\{") + line.count("{")
    close_braces = line.count(r"\}") + line.count("}")
    if open_braces != close_braces:
        log.warning(
            f"Unmatched braces (open: {open_braces}, close: {close_braces}){context_info}. "
            f"Original: '{original_line[:60]}...'"
        )
    
    suspicious_backslash = re.search(r"\\(?![a-zA-Z{}\$%&#_\^~\\])", line)
    if suspicious_backslash:
        pos = suspicious_backslash.start()
        if not line[pos:].startswith(r"\textbackslash{}"):
            snippet = line[max(0, pos-5):min(len(line), pos+15)]
            log.debug(
                f"Unusual backslash pattern at position {pos}{context_info}. "
                f"Snippet: '...{snippet}...' | Original: '{original_line[:40]}...'"
            )
    
    if len(line) > 500:
        log.debug(
            f"Very long line detected ({len(line)} chars){context_info}. "
            f"Consider manual line breaks. Original: '{original_line[:60]}...'"
        )
    
    return line

def _typeset_latex_image(image_match, line, block):
    """Typeset images."""
    image_title, image_path = image_match[0]
    # Check for title. If not found, alt_text will be used as caption.
    title_match = re.findall(r'(.*)\s+"(.*)"', image_path)
    if title_match:
        image_path, image_title = title_match[0]
    # Sanitize image path (spaces → hyphens)
    image_path_safe = image_path.replace(" ", "-")
    if image_path != image_path_safe:
        log.debug(f"Image path sanitized: {image_path} -> {image_path_safe}")
    # Make a safe label.
    label = "fig:{l}".format(l=re.sub("[^0-9a-zA-Z]+", "", image_title))
    # Make the string to replace!
    replacement = (
        r"\includegraphics[width=0.8\textwidth]{"
        + image_path_safe
        + r"}}\label{{{l}}}\zlabel{{{l}}}".format(l=label)
        + r"\caption{"
        + _latex_convert(image_title)
        + r"}"
    ).replace("\\", "\\\\")
    # Replace with LaTeX format.
    line = re.sub(
        r"!\[(.*)\]\((.*)\)",
        replacement,
        line,
    )
    # Create the figure.
    block.append(r"\begin{figure}[h!]\center")
    block.append(line)
    line = r"\end{figure}"
    return line


def _fix_table_line(line, end_pipes):
    r"""Fix table line with proper escaping."""
    # Split cells by |
    cells = re.split(r"\|", line)
    
    # Escape each cell content
    escaped_cells = []
    for cell in cells:
        cell_stripped = cell.strip()
        if cell_stripped:  # Skip empty cells (from leading/trailing |)
            escaped_cells.append(_latex_convert(cell_stripped))
        else:
            escaped_cells.append("")
    
    # Join with &
    if end_pipes and escaped_cells:
        # Remove first and last empty cells (from outer pipes)
        if escaped_cells[0] == "":
            escaped_cells.pop(0)
        if escaped_cells and escaped_cells[-1] == "":
            escaped_cells.pop()
    
    line = " & ".join(escaped_cells) + " \\\\"
    
    return line

def _check_for_new_table(
    table_match, text, i, line, block, table_found, header_done, end_pipes
):
    """Check for new table.

    Check if a new table is beginning or not. If new table is detected, write
    table header and mark as found.
    """
    # Check next line for minimum 3 dashes and the same count of |.
    if i < len(text) - 1:
        next_line = text[i + 1]
        table_match_next = re.findall("\\|", next_line)
        if table_match_next:
            if len(table_match) == len(table_match_next):
                table_match_dashes = re.findall("-{3,}", next_line)
                if table_match_dashes:
                    table_found = True
                    end_pipes = bool(len(table_match) > len(table_match_dashes))
                    next_line = re.sub(":-+:", "c", next_line)
                    next_line = re.sub("-+:", "r", next_line)
                    next_line = re.sub("-+", "l", next_line)
                    table_header = "\\begin{longtable}{" + next_line + "}"
                    block.append(table_header)
                    # Fix the header.
                    line = _fix_table_line(line, end_pipes)
                else:
                    log.warning("Possibly incorrectly specified table found.")
            else:
                log.warning("Possibly unbalanced table found.")
    return table_found, header_done, line, end_pipes

def _process_text_block(text_lines, context=None):
    """
    Process a block of text lines with proper code block handling.
    
    Args:
        text_lines: List of text lines to process
        context: Optional dict with debugging info (passed to _latex_convert)
        
    Yields:
        LaTeX-formatted lines with proper code block environments
    """
    in_code_block = False
    code_language = None
    
    for line_num, line in enumerate(text_lines, start=1):
        # Update context with current line number
        if context:
            line_context = context.copy()
            line_context['line_num'] = context.get('line_num', 0) + line_num - 1
        else:
            line_context = {'line_num': line_num}
        
        converted = _latex_convert(line, context=line_context)
        
        # Handle code block start
        if converted.startswith("%%CODEBLOCK_START"):
            if in_code_block:
                log.warning(
                    f"Nested code block detected{_format_context(line_context)} "
                    f"- closing previous block"
                )
                yield "\\end{lstlisting}"
            
            in_code_block = True
            
            # Extract language if present
            lang_match = re.match(r"%%CODEBLOCK_START:(\w+)%%", converted)
            if lang_match:
                code_language = lang_match.group(1)
                yield f"\\begin{{lstlisting}}[language={code_language}]"
            else:
                code_language = None
                yield "\\begin{lstlisting}"
            
            continue
        
        # Handle code block end
        if in_code_block and line.strip() == "```":
            yield "\\end{lstlisting}"
            in_code_block = False
            code_language = None
            continue
        
        # Handle code block content (don't convert!)
        if in_code_block:
            yield line.rstrip()
            continue
        
        # Handle indented code lines
        if converted.startswith("%%CODELINE:"):
            code_content = converted[len("%%CODELINE:"):-2]
            code_escaped = code_content.replace("\\", r"\textbackslash{}")
            code_escaped = code_escaped.replace("{", r"\{")
            code_escaped = code_escaped.replace("}", r"\}")
            code_escaped = code_escaped.replace("_", r"\_")
            code_escaped = code_escaped.replace("^", r"\textasciicircum{}")
            code_escaped = code_escaped.replace("~", r"\textasciitilde{}")
            code_escaped = code_escaped.replace("#", r"\#")
            code_escaped = code_escaped.replace("$", r"\$")
            code_escaped = code_escaped.replace("%", r"\%")
            code_escaped = code_escaped.replace("&", r"\&")
            yield f"\\texttt{{{code_escaped}}}"
            continue
        
        # Regular line
        yield converted
    
    # Close unclosed code block
    if in_code_block:
        log.warning(
            f"Unclosed code block at end of text{_format_context(context)}"
        )
        yield "\\end{lstlisting}"


def _format_context(context):
    """Format context dict into readable string."""
    if not context:
        return ""
    
    parts = []
    if 'item_uid' in context:
        parts.append(f"Item: {context['item_uid']}")
    if 'file' in context:
        parts.append(f"File: {context['file']}")
    if 'line_num' in context:
        parts.append(f"Line: {context['line_num']}")
    
    return f" [{', '.join(parts)}]" if parts else ""

def _has_complex_formatting(text_lines):
    """
    Check if text contains complex formatting requiring special processing.
    
    Complex formats include:
    - Tables (markdown pipes with header separators)
    - PlantUML diagrams
    - Math environments ($$)
    
    Simple formats (handled by _process_text_block):
    - Markdown formatting (bold, italic, strikethrough)
    - Headings
    - Code blocks (fenced and indented)
    - Inline code
    - Images (basic)
    - Lists
    
    Args:
        text_lines: List of text lines to check (or single string)
        
    Returns:
        bool: True if complex formatting detected, False otherwise
    """
    # Normalize input
    if isinstance(text_lines, str):
        text_lines = text_lines.splitlines()
    
    if not text_lines:
        return False
    
    # Join for pattern matching - MUSS HIER SEIN!
    text_joined = "\n".join(text_lines)

    #############################
    ## Check for tables
    #############################
    has_tables = False
    for i, line in enumerate(text_lines):
        if "|" in line and line.count("|") >= 2:  # At least 2 pipes
            # Look for table header separator in next line
            if i + 1 < len(text_lines):
                next_line = text_lines[i + 1]
                # Match: |---|---| or | --- | --- | or :---: (alignment)
                if re.search(r"\|?\s*:?-{3,}:?\s*\|", next_line):
                    has_tables = True
                    log.debug(f"Table detected at line {i}: '{line[:50]}...'")
                    break
    
    #############################
    ## Check for PlantUML
    #############################
    # Match both legacy (`plantuml) and fenced (```plantuml) formats
    has_plantuml = bool(
        re.search(r"^`+plantuml\s", text_joined, re.MULTILINE)  # ✅ One or more backticks
    )
    if has_plantuml:
        log.debug("PlantUML diagram detected")
    
    #############################
    ## Check for math environments
    #############################
    has_math = "$$" in text_joined
    if has_math:
        log.debug("Math environment detected ($$)")
    
    # Summary logging
    if has_tables or has_plantuml or has_math:
        log.info(
            f"Complex formatting detected: "
            f"tables={has_tables}, plantuml={has_plantuml}, math={has_math}"
        )
        return True
    
    return False

def _format_simple_text_block(text_lines, context=None):
    """
    Format simple text block with modern code block handling.
    
    Args:
        text_lines: List of text lines to format
        context: Optional dict with debugging info
        
    Yields:
        Formatted LaTeX lines
    """
    # Normalize input
    if isinstance(text_lines, str):
        text_lines = text_lines.splitlines()
    
    if not text_lines:
        return
    
    # Use code block processor with context
    yield from _process_text_block(text_lines, context=context)

def _convert_markdown_link_to_href(markdown_link):
    """
    Convert a markdown link [text](url) to LaTeX \\href{url}{text}.
    
    Handles:
    - Nested brackets in text: [Text [nested] text](url)
    - Parentheses in text: [Text (with parens)](url)
    - Relative URLs: [Link](../file.md)
    - Absolute URLs: [Link](https://example.com)
    - Anchors: [Link](#section)
    - Special characters in text and URL
    
    Uses bracket counting to properly parse nested structures.
    
    Args:
        markdown_link: String in markdown link format "[text](url)"
    
    Returns:
        LaTeX \\href{url}{text} command or escaped plain text if invalid
    
    Examples:
        >>> _convert_markdown_link_to_href("[Simple](https://example.com)")
        '\\\\href{https://example.com}{Simple}'
        
        >>> _convert_markdown_link_to_href("[Text [1/h]](../doc.md)")
        '\\\\href{../doc.md}{Text [1/h]}'
    """
    text = markdown_link.strip()
    
    # Must start with [
    if not text.startswith('['):
        return _escape_latex_text(text)
    
    # Find the matching ] for the opening [ by counting brackets
    bracket_depth = 0
    i = 0
    
    for i, char in enumerate(text):
        if char == '[':
            bracket_depth += 1
        elif char == ']':
            bracket_depth -= 1
            
            # Found the closing bracket for link text
            if bracket_depth == 0:
                # Check if followed by (
                if i + 1 < len(text) and text[i + 1] == '(':
                    link_text = text[1:i]  # Extract text between [ and ]
                    
                    # Now find the closing ) for the URL
                    # The URL ends at the last ) in the string
                    # (assuming no ) in the URL, which is standard for markdown)
                    url_start = i + 2
                    
                    # Find matching closing paren
                    paren_depth = 1
                    url_end = -1
                    
                    for j in range(url_start, len(text)):
                        if text[j] == '(':
                            paren_depth += 1
                        elif text[j] == ')':
                            paren_depth -= 1
                            if paren_depth == 0:
                                url_end = j
                                break
                    
                    if url_end > url_start:
                        link_url = text[url_start:url_end]
                        
                        # Escape text for LaTeX (but keep brackets)
                        link_text_escaped = _escape_latex_text(link_text)
                        
                        # Escape URL for LaTeX (minimal escaping)
                        link_url_safe = _escape_latex_url(link_url)
                        
                        return f"\\href{{{link_url_safe}}}{{{link_text_escaped}}}"
                
                # If we get here, no valid (url) found after ]
                break
    
    # Not a valid markdown link - escape as plain text
    return _escape_latex_text(text)


def _escape_latex_url(url):
    """
    Escape a URL for use in LaTeX \\href{}.
    
    Only escapes characters that actually break LaTeX:
    - # (needs escaping unless at start for anchors)
    - % (comment character)
    - & (special character)
    
    Does NOT escape:
    - _ (common in URLs, works fine in \\href{})
    - : (needed for protocols)
    - / (path separator)
    - . (file extensions)
    - - (common in URLs)
    
    Args:
        url: URL string (absolute, relative, or anchor)
    
    Returns:
        LaTeX-safe URL string
    """
    # Escape special chars that break LaTeX
    url = url.replace("#", r"\#")
    url = url.replace("%", r"\%")
    url = url.replace("&", r"\&")
    
    # Note: _ does NOT need escaping inside \href{}
    # LaTeX treats it as literal text in URL context
    
    return url


def _escape_latex_text(text):
    """
    Escape LaTeX special characters in text.
    
    Used for link text, attribute values, table cells, etc.
    Does NOT process markdown formatting (bold, italic, etc.).
    
    Escapes:
    - Backslash: \ → \\textbackslash{}
    - Braces: { } → \\{ \\}
    - Underscore: _ → \\_
    - Ampersand: & → \\&
    - Hash: # → \\#
    - Percent: % → \\%
    - Dollar: $ → \\$
    - Caret: ^ → \\textasciicircum{}
    - Tilde: ~ → \\textasciitilde{}
    
    Does NOT escape:
    - Square brackets: [ ] (they're fine in LaTeX text)
    - Parentheses: ( ) (they're fine in LaTeX text)
    
    Args:
        text: Plain text string
    
    Returns:
        LaTeX-escaped string
    """
    # Order matters! Backslash first
    text = text.replace("\\", r"\textbackslash{}")
    text = text.replace("{", r"\{")
    text = text.replace("}", r"\}")
    text = text.replace("_", r"\_")
    text = text.replace("&", r"\&")
    text = text.replace("#", r"\#")
    text = text.replace("%", r"\%")
    text = text.replace("$", r"\$")
    text = text.replace("^", r"\textasciicircum{}")
    text = text.replace("~", r"\textasciitilde{}")
    
    # [ ] and ( ) are OK in LaTeX text, don't escape
    
    return text