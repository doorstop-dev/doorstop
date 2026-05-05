# SPDX-License-Identifier: LGPL-3.0-only

# pylint: disable=too-many-lines
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
    r"""
    Convert markdown line to LaTeX format.

    Processing order is CRITICAL:
    1. HTML to Markdown/LaTeX conversion
    2. Code block detection
    3. Preserve inline code segments
    4. Preserve URLs from markdown links
    5. Structural escaping (backslash, braces)
    6. Markdown formatting (bold, italic, strikethrough)
    7. Convert preserved links to \href{} - USE FINAL PLACEHOLDERS
    8. Headings
    9. Remaining special characters (SKIPS final placeholders)
    10. Restore inline code
    11. Restore final hrefs
    12. Restore HTML labels
    13. Restore escaped underscores
    14. Restore images
    """
    original_line = line

    if context:
        item_uid = context.get("item_uid", "unknown")
        line_num = context.get("line_num", "?")
        context_info = f" [Item: {item_uid}, Line: {line_num}]"
    else:
        context_info = ""

    #############################
    ## Phase 1: HTML and Markdown fixes
    #############################
    # Convert HTML tags to Markdown/LaTeX
    line, html_labels = _convert_html_to_latex(line)

    # Fix bold headings: **# Heading** → # Heading
    line = re.sub(r"^\*\*\s*(#{1,6})\s+(.*?)\s*\*\*\s*$", r"\1 \2", line)

    #############################
    ## Phase 2: Code block detection
    #############################
    if line.strip().startswith("```"):
        lang_match = re.match(r"^```(\w+)?", line.strip())
        if lang_match and lang_match.group(1):
            lang = lang_match.group(1)
            return f"<<<CODEBLOCK_START:{lang}>>>"
        else:
            return "<<<CODEBLOCK_START>>>"

    if re.match(r"^(    |\t)", line) and line.strip():
        code_content = line.lstrip()
        return f"<<<CODELINE:{code_content}>>>"

    #############################
    ## Phase 3: Preserve inline code AND markdown links
    #############################
    # Inline code: `code`
    inline_code_pattern = r"`([^`]+)`"
    code_segments = []

    def protect_inline_code(match):
        code_segments.append(match.group(1))
        return f"<<<INLINECODE{len(code_segments)-1}>>>"

    line = re.sub(inline_code_pattern, protect_inline_code, line)

    # Protect escaped underscores in Markdown
    # In Markdown, \_ means "literal underscore, not italic delimiter"
    ESCAPED_UNDERSCORE_PH = "<<<ESCAPEDUNDERSCORE>>>"
    line = line.replace(r"\_", ESCAPED_UNDERSCORE_PH)

    #############################
    ## Phase 4: Preserve images and links
    #############################
    # Markdown images FIRST: ![alt](url) or ![alt](url "title")
    image_segments = []

    def protect_markdown_image(match):
        """Protect markdown image syntax from conversion.

        Preserves ![alt](url) format by adding placeholders.
        """
        alt_text = match.group(1)
        image_url_and_title = match.group(2)
        image_segments.append((alt_text, image_url_and_title))
        return f"<<<MDIMAGE{len(image_segments)-1}>>>"

    # Match: ![alt](url) or ![alt](url "title")
    line = re.sub(r"!\[([^\]]*)\]\(([^\)]+)\)", protect_markdown_image, line)

    # Markdown links: [text](url)
    link_segments = []

    def protect_markdown_link(match):
        """Protect markdown link syntax from conversion.

        Preserves [text](url) format by adding placeholders.
        """
        link_text = match.group(1)
        link_url = match.group(2)
        link_segments.append((link_text, link_url))
        return f"<<<MDLINK{len(link_segments)-1}>>>"

    line = re.sub(r"\[([^\]]+)\]\(([^\)]+)\)", protect_markdown_link, line)

    #############################
    ## Phase 5: Structural escaping - USE PLACEHOLDERS!
    #############################
    BACKSLASH_PH = "<<<BACKSLASH_TEMP>>>"
    line = line.replace("\\", BACKSLASH_PH)
    line = line.replace("{", r"\{")
    line = line.replace("}", r"\}")
    line = line.replace(BACKSLASH_PH, r"\textbackslash{}")

    #############################
    ## Phase 6: Markdown formatting (bold, italic, strikethrough)
    #############################
    # Bold: **text** → \textbf{text}
    line = re.sub(r"\*\*(.*?)\*\*", r"\\textbf{\1}", line)
    line = re.sub(r"__(.*?)__", r"\\textbf{\1}", line)

    # Italic: *text* → \textit{text}
    line = re.sub(r"(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)", r"\\textit{\1}", line)

    # Italic: _text_ → \textit{text}
    # Matches any text between underscores (non-greedy, no nested underscores)
    line = re.sub(r"_([^_\n]+?)_", r"\\textit{\1}", line)

    # Strikethrough: ~~text~~ → \sout{text}
    line = re.sub(r"~~(.*?)~~", r"\\sout{\1}", line)

    #############################
    ## Phase 7: Process and store links (don't insert yet!)
    #############################
    # Store fully processed hrefs for insertion AFTER Phase 9
    final_hrefs = {}

    for i, (link_text, link_url) in enumerate(link_segments):
        # Process link text completely:
        # 1. Protect markdown markers
        # 2. Escape LaTeX special chars
        # 3. Apply markdown formatting

        # Step 1: Protect markdown markers
        link_text_temp = link_text
        link_text_temp = link_text_temp.replace("**", "<<<MDLINKBOLD>>>")
        link_text_temp = link_text_temp.replace("__", "<<<MDLINKBOLD2>>>")
        link_text_temp = link_text_temp.replace("~~", "<<<MDLINKSTRIKE>>>")
        link_text_temp = link_text_temp.replace("*", "<<<MDLINKITALIC>>>")

        # Step 2: Escape LaTeX special characters (\ { } _)
        link_text_processed = _escape_latex_text(link_text_temp)

        # Step 3: Restore markdown markers
        link_text_processed = link_text_processed.replace("<<<MDLINKBOLD>>>", "**")
        link_text_processed = link_text_processed.replace("<<<MDLINKBOLD2>>>", "__")
        link_text_processed = link_text_processed.replace("<<<MDLINKSTRIKE>>>", "~~")
        link_text_processed = link_text_processed.replace("<<<MDLINKITALIC>>>", "*")

        # Step 4: Apply markdown formatting
        link_text_processed = re.sub(
            r"\*\*(.*?)\*\*", r"\\textbf{\1}", link_text_processed
        )
        link_text_processed = re.sub(r"__(.*?)__", r"\\textbf{\1}", link_text_processed)
        link_text_processed = re.sub(r"~~(.*?)~~", r"\\sout{\1}", link_text_processed)
        link_text_processed = re.sub(
            r"(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)", r"\\textit{\1}", link_text_processed
        )

        # Escape URL
        link_url_safe = _escape_latex_url(link_url)

        # Store the final href
        final_hrefs[i] = f"\\href{{{link_url_safe}}}{{{link_text_processed}}}"

        # Replace with FINAL placeholder (will be inserted after Phase 9)
        line = line.replace(f"<<<MDLINK{i}>>>", f"<<<FINALHREF{i}>>>")

    #############################
    ## Phase 8: Headings
    #############################
    # Determine if headings should be numbered
    #
    # Logic:
    #   1. If PUBLISH_HEADING_LEVELS=True (global setting): numbered (\section{})
    #   2. If in_item_text=True (context): unnumbered (\section*{})
    #   3. Otherwise: use PUBLISH_HEADING_LEVELS setting
    #
    # Rationale:
    #   - Document-level headings: controlled by PUBLISH_HEADING_LEVELS
    #   - Item text headings: always unnumbered (avoids duplicate numbering)

    # Check context for item text
    in_item_text = context and context.get("in_item_text", False)

    # Determine star suffix
    if in_item_text:
        # Inside item text: always unnumbered
        star = "*"
    elif settings.PUBLISH_HEADING_LEVELS:
        # Global setting: numbered
        star = ""
    else:
        # Global setting: unnumbered
        star = "*"

    # Handle heading levels (deepest first to avoid partial matches)
    if re.match(r"^#{6,} ", line):
        log.warning(
            f"Heading level too deep (>5){context_info}. "
            f"Line: '{original_line[:60]}...'"
        )

    # Level 6+ (too deep)
    line = re.sub(
        r"^#{6,} (.*)$",
        r"\\subparagraph*{\1 \\textbf{NOTE: This heading level is too deep for LaTeX.}}",
        line,
    )

    # Level 5
    line = re.sub(r"^##### (.*)$", r"\\subparagraph" + star + r"{\1}", line)

    # Level 4
    line = re.sub(r"^#### (.*)$", r"\\paragraph" + star + r"{\1}", line)

    # Level 3
    line = re.sub(r"^### (.*)$", r"\\subsubsection" + star + r"{\1}", line)

    # Level 2
    line = re.sub(r"^## (.*)$", r"\\subsection" + star + r"{\1}", line)

    # Level 1
    line = re.sub(r"^# (.*)$", r"\\section" + star + r"{\1}", line)

    #############################
    ## Phase 9: Remaining special characters
    ## IMPORTANT: Skip <<<FINALHREF>>> and <<<HTMLLABEL>>> placeholders!
    #############################
    # Split line by placeholders, process parts, rejoin
    parts = re.split(r"(<<<(?:FINALHREF|HTMLLABEL)\d+>>>)", line)
    processed_parts = []

    for part in parts:
        if part.startswith("<<<") and part.endswith(">>>"):
            # Keep placeholder as-is
            processed_parts.append(part)
        else:
            # Process this part
            part = re.sub(r"#", r"\\#", part)
            part = re.sub(r"\$", r"\\$", part)
            part = re.sub(r"%", r"\\%", part)
            part = re.sub(r"&", r"\\&", part)
            part = re.sub(r"(?<!\\)_", r"\\_", part)
            part = re.sub(r"\^", r"\\textasciicircum{}", part)
            part = re.sub(r"~", r"\\textasciitilde{}", part)
            processed_parts.append(part)

    line = "".join(processed_parts)

    #############################
    ## Phase 10: Restore inline code
    #############################
    for i, code_content in enumerate(code_segments):
        code_escaped = code_content.replace("\\", r"\textbackslash{}")
        code_escaped = code_escaped.replace("{", r"\{")
        code_escaped = code_escaped.replace("}", r"\}")
        code_escaped = code_escaped.replace("_", r"\_")
        line = line.replace(f"<<<INLINECODE{i}>>>", r"\texttt{" + code_escaped + "}")

    #############################
    ## Phase 11: Restore final hrefs
    #############################
    for i, href in final_hrefs.items():
        line = line.replace(f"<<<FINALHREF{i}>>>", href)

    #############################
    ## Phase 12: Restore HTML labels (AFTER all escaping!)
    #############################
    for i, label_cmd in enumerate(html_labels):
        line = line.replace(f"<<<HTMLLABEL{i}>>>", label_cmd)

    #############################
    ## Phase 13: Restore escaped underscores
    #############################
    line = line.replace(ESCAPED_UNDERSCORE_PH, r"\_")

    #############################
    ## Phase 14: Restore images (leave as markdown for _typeset_latex_image)
    #############################
    for i, (alt_text, url_and_title) in enumerate(image_segments):
        # Restore as markdown for _typeset_latex_image to process
        line = line.replace(f"<<<MDIMAGE{i}>>>", f"![{alt_text}]({url_and_title})")

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
            snippet = line[max(0, pos - 5) : min(len(line), pos + 15)]
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


def _convert_html_to_latex(line):
    r"""
    Convert common HTML tags to LaTeX equivalents.

    Handles:
    - <img> → ![alt](src) (Markdown image syntax)
    - <figcaption> → *text* (italic)
    - <cite> → *text* (italic)
    - <figure> → removed (content preserved)
    - <a name="..."> → \label{...} (via placeholder)
    - Other tags → stripped

    Args:
        line: Text line that may contain HTML

    Returns:
        Tuple of (converted_line, label_list) where:
        - converted_line contains <<<HTMLLABEL#>>> placeholders
        - label_list contains the actual \label{} commands
    """
    label_segments = []

    # 1. Convert <a name="..."> to temporary placeholder (without < >)
    def replace_anchor(match):
        anchor_name = match.group(1)
        label_name = re.sub(r"[^a-zA-Z0-9-]", "-", anchor_name)
        label_cmd = f"\\label{{{label_name}}}"
        label_segments.append(label_cmd)
        # Use placeholder without < > to avoid HTML tag removal
        return f"HTMLLABELPH{len(label_segments)-1}ENDPH"

    line = re.sub(
        r'<a\s+name="([^"]+)"[^>]*>\s*</a>', replace_anchor, line, flags=re.IGNORECASE
    )

    # 2. Convert <img> to Markdown
    def replace_img(match):
        full_tag = match.group(0)
        src = re.search(r'src="([^"]+)"', full_tag)
        alt = re.search(r'alt="([^"]*)"', full_tag)
        return f'![{alt.group(1) if alt else ""}]({src.group(1) if src else ""})'

    line = re.sub(r"<img[^>]+>", replace_img, line)

    # 3. Convert semantic tags to italic
    line = re.sub(
        r"<(?:figcaption|cite)>(.*?)</(?:figcaption|cite)>",
        r"*\1*",
        line,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # 4. Remove structural tags (keep content)
    line = re.sub(r"</?figure[^>]*>", "", line, flags=re.IGNORECASE)

    # 5. Remove any remaining HTML tags
    line = re.sub(r"<[^>]+>", "", line)

    # 6. Convert temporary placeholder to final format
    line = re.sub(r"HTMLLABELPH(\d+)ENDPH", r"<<<HTMLLABEL\1>>>", line)

    # 7. Clean up whitespace
    line = re.sub(r"\n\s*\n\s*\n+", "\n\n", line)

    return line, label_segments


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
    in_blockquote = False
    code_language = None

    # Convert to list to allow look-ahead
    lines_list = list(text_lines) if not isinstance(text_lines, list) else text_lines

    for line_num, line in enumerate(lines_list, start=1):
        # Update context with current line number
        if context:
            line_context = context.copy()
            line_context["line_num"] = context.get("line_num", 0) + line_num - 1
        else:
            line_context = {"line_num": line_num}

        # Handle code block end FIRST (before conversion)
        if in_code_block and line.strip() == "```":
            yield "\\end{lstlisting}"
            in_code_block = False
            code_language = None
            continue

        # Check if line is blockquote
        is_blockquote = line.strip().startswith(">")

        # Handle blockquote transitions
        if is_blockquote and not in_code_block:
            if not in_blockquote:
                # Start blockquote environment
                yield ""
                yield "\\begin{quote}"
                in_blockquote = True

            # Remove > and optional space after it
            content = line.strip()[1:].strip()

            if content:
                # Convert the content (without the >)
                converted = _latex_convert(content, context=line_context)
                yield converted
            else:
                # Empty blockquote line (just >)
                yield ""
            continue

        # End blockquote if we're in one and this line doesn't start with >
        if in_blockquote and not is_blockquote:
            yield "\\end{quote}"
            yield ""
            in_blockquote = False
            # Fall through to process this line normally

        # Now convert the line (normal flow)
        converted = _latex_convert(line, context=line_context)

        # Handle code block start
        if converted.startswith("<<<CODEBLOCK_START"):
            if in_code_block:
                log.warning(
                    f"Nested code block detected{_format_context(line_context)} "
                    f"- closing previous block"
                )
                yield "\\end{lstlisting}"

            in_code_block = True
            # Extract language if present
            lang_match = re.match(r"<<<CODEBLOCK_START:(\w+)>>>", converted)
            if lang_match:
                code_language = lang_match.group(1)
                yield f"\\begin{{lstlisting}}[language={code_language}]"
            else:
                code_language = None
                yield "\\begin{lstlisting}"
            continue

        # Handle code block content (don't convert!)
        if in_code_block:
            yield line.rstrip()
            continue

        # Handle indented code lines
        if converted.startswith("<<<CODELINE:"):
            # Extract content between <<<CODELINE: and >>>
            code_content = converted[len("<<<CODELINE:") :]
            if code_content.endswith(">>>"):
                code_content = code_content[:-3]
            # Escaping for \texttt{} context
            code_escaped = code_content.replace("\\", r"\textbackslash{}")
            code_escaped = code_escaped.replace("{", r"\{")
            code_escaped = code_escaped.replace("}", r"\}")
            code_escaped = code_escaped.replace("_", r"\_")  # ← NEU HINZUGEFÜGT!
            yield f"\\texttt{{{code_escaped}}}"
            continue

        # Regular line - check if next non-empty line is code block OR block element
        next_line_is_code_block = False
        for check_idx in range(line_num, len(lines_list)):
            check_line = lines_list[check_idx]
            if check_line.strip():  # Found next non-empty line
                if check_line.strip().startswith("```"):
                    next_line_is_code_block = True
                    break
                # Check if it's a block element (figure, quote, label, etc.)
                check_converted = _latex_convert(check_line, context=line_context)
                if (
                    check_converted.strip().startswith("\\begin{")
                    or check_converted.strip().startswith("\\label{")
                    or "![" in check_line
                ):
                    break
                # If it's actual content, stop looking
                if check_converted.strip():
                    break

        # Add \\ before code blocks (but only for plain text lines)
        # NEVER add \\ to:
        # - Empty lines
        # - LaTeX commands (start with \)
        # - Lines with images
        # - Lines with labels
        # - Lines inside blockquotes! (NEW)
        is_plain_text = (
            converted.strip()
            and not converted.strip().startswith("\\")  # No LaTeX commands
            and "![" not in converted  # No markdown images
            and "\\label{" not in converted  # No labels!
            and not in_blockquote  # Not in blockquote! (NEW)
        )

        if next_line_is_code_block and is_plain_text:
            yield converted + "\\\\"
        else:
            yield converted

    # Close unclosed blockquote
    if in_blockquote:
        yield "\\end{quote}"
        in_blockquote = False

    # Close unclosed code block
    if in_code_block:
        log.warning(f"Unclosed code block at end of text{_format_context(context)}")
        yield "\\end{lstlisting}"


def _format_context(context):
    """Format context dict into readable string."""
    if not context:
        return ""

    parts = []
    if "item_uid" in context:
        parts.append(f"Item: {context['item_uid']}")
    if "file" in context:
        parts.append(f"File: {context['file']}")
    if "line_num" in context:
        parts.append(f"Line: {context['line_num']}")

    return f" [{', '.join(parts)}]" if parts else ""


def _has_complex_formatting(text_lines):
    """
    Check if text contains complex formatting requiring special processing.

    Complex formats (require legacy formatter):
    - Tables (markdown pipes with header separators OR edge cases)
    - PlantUML diagrams (with or without backticks)
    - Math environments ($$)
    - Nested lists (multiple indentation levels)

    Simple formats (handled by _process_text_block):
    - Markdown formatting (bold, italic, strikethrough)
    - Headings
    - Code blocks (fenced with ```)  # ✅ HINZUGEFÜGT
    - Inline code
    - Images (basic)
    - Simple lists (single level)

    Note: When in doubt, use legacy formatter. It's battle-tested and handles
    all edge cases correctly (EOF handling, warnings, proper escaping).

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

    # Join for pattern matching
    text_joined = "\n".join(text_lines)

    # #############################
    # ## Check for code blocks
    # #############################
    # has_code_blocks = False
    # if "```" in text_joined:
    #     # Check if code block is at the start
    #     for line in text_lines:
    #         if line.strip():
    #             if line.strip().startswith("```"):
    #                 has_code_blocks = True
    #                 log.debug("Code block at start - using legacy")
    #             break  # Only check first non-empty line

    #############################
    ## Check for tables
    #############################
    has_tables = False
    for i, line in enumerate(text_lines):
        if "|" in line and line.count("|") >= 2:
            if i + 1 < len(text_lines):
                next_line = text_lines[i + 1]
                # Proper table separator (3+ dashes)
                if re.search(r"\|?\s*:?-{3,}:?\s*\|", next_line):
                    has_tables = True
                    log.debug(f"Table detected at line {i}")
                    break
                # Malformed table - multiple cells with short dashes
                # Pattern: |-|-| (not |--|)
                if (
                    next_line.count("|") >= 3
                    and "-" in next_line
                    and not re.search(r"-{3,}", next_line)
                ):
                    has_tables = True
                    log.debug(f"Malformed table (short dashes) at line {i}")
                    break
            # EOF table check
            if i == len(text_lines) - 1 and i > 0:
                prev_has_pipes = any(
                    "|" in text_lines[j] for j in range(max(0, i - 2), i)
                )
                if not prev_has_pipes:
                    has_tables = True
                    log.debug(f"Potential table start at EOF (line {i}) - using legacy")
                    break

    #############################
    ## Check for PlantUML (with or without backticks)
    #############################
    has_plantuml = bool(re.search(r"^`*plantuml\s", text_joined, re.MULTILINE))
    if has_plantuml:
        log.debug("PlantUML diagram detected")

    #############################
    ## Check for math environments
    #############################
    has_math = "$$" in text_joined
    if has_math:
        log.debug("Math environment detected ($$)")

    #############################
    ## Check for nested lists (multiple indentation levels)
    #############################
    has_nested_lists = False
    list_pattern = r"^\s*([\*\+\-]|\d+\.)\s+"
    list_indents = set()

    for line in text_lines:
        if re.match(list_pattern, line):
            indent = len(line) - len(line.lstrip())
            list_indents.add(indent)

    if len(list_indents) > 1:
        has_nested_lists = True
        log.debug(f"Nested lists detected with indents: {sorted(list_indents)}")

    # Summary
    if has_tables or has_plantuml or has_math or has_nested_lists:
        log.info(
            f"Complex formatting detected: "
            f"tables={has_tables}, plantuml={has_plantuml}, "
            f"math={has_math}, nested_lists={has_nested_lists}"
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
    r"""
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
    """
    text = markdown_link.strip()

    # Must start with [
    if not text.startswith("["):
        return _escape_latex_text(text)

    # Find the matching ] for the opening [ by counting brackets
    bracket_depth = 0
    i = 0

    for i, char in enumerate(text):
        if char == "[":
            bracket_depth += 1
        elif char == "]":
            bracket_depth -= 1

            # Found the closing bracket for link text
            if bracket_depth == 0:
                # Check if followed by (
                if i + 1 < len(text) and text[i + 1] == "(":
                    link_text = text[1:i]  # Extract text between [ and ]

                    # Now find the closing ) for the URL
                    # The URL ends at the last ) in the string
                    # (assuming no ) in the URL, which is standard for markdown)
                    url_start = i + 2

                    # Find matching closing paren
                    paren_depth = 1
                    url_end = -1

                    for j in range(url_start, len(text)):
                        if text[j] == "(":
                            paren_depth += 1
                        elif text[j] == ")":
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
    r"""
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
    r"""Escape LaTeX special characters in text.

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
    # Use placeholders to avoid double-escaping the {} in LaTeX commands
    BACKSLASH_PH = "<<<BACKSLASH>>>"
    CARET_PH = "<<<CARET>>>"
    TILDE_PH = "<<<TILDE>>>"

    # Phase 1: Replace backslash, caret, tilde with placeholders
    # (These become LaTeX commands with {} that we don't want to escape)
    text = text.replace("\\", BACKSLASH_PH)
    text = text.replace("^", CARET_PH)
    text = text.replace("~", TILDE_PH)

    # Phase 2: Escape braces and other special characters
    # (Now we won't escape the {} in our LaTeX commands)
    text = text.replace("{", r"\{")
    text = text.replace("}", r"\}")
    text = text.replace("_", r"\_")
    text = text.replace("&", r"\&")
    text = text.replace("#", r"\#")
    text = text.replace("%", r"\%")
    text = text.replace("$", r"\$")

    # Phase 3: Replace placeholders with proper LaTeX commands
    # (The {} in these won't be escaped because Phase 2 is done)
    text = text.replace(BACKSLASH_PH, r"\textbackslash{}")
    text = text.replace(CARET_PH, r"\textasciicircum{}")
    text = text.replace(TILDE_PH, r"\textasciitilde{}")

    # [ ] and ( ) are OK in LaTeX text, don't escape
    return text
