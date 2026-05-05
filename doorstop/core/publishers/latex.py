# SPDX-License-Identifier: LGPL-3.0-only

"""Functions to publish LaTeX documents."""

import os
import re
from typing import List

from doorstop import common, settings
from doorstop.cli import utilities
from doorstop.common import DoorstopError
from doorstop.core.publishers._latex_functions import (
    _add_comment,
    _check_for_new_table,
    _fix_table_line,
    _format_simple_text_block,
    _has_complex_formatting,
    _latex_convert,
    _process_text_block,
    _typeset_latex_image,
    _convert_markdown_link_to_href,
    _escape_latex_text,
)
from doorstop.core.publishers.base import (
    BasePublisher,
    extract_prefix,
    format_level,
    get_document_attributes,
    normalize_link_list, 
    is_link_attribute, 
)
from doorstop.core.template import check_latex_template_data, read_template_data
from doorstop.core.types import is_item, iter_documents, iter_items

log = common.logger(__name__)


class LaTeXPublisher(BasePublisher):
    """LaTeX publisher."""

    def __init__(self, obj, ext):
        super().__init__(obj, ext)
        self.END_LONGTABLE = "\\end{longtable}"
        self.HLINE = "\\hline"
        self.compile_files = []
        self.compile_path = ""
        # Define lists.
        self.list["start"] = {
            "itemize": r"\begin{itemizeDeep}",
            "enumerate": r"\begin{enumerateDeep}",
        }
        self.list["end"] = {
            "itemize": r"\end{itemizeDeep}",
            "enumerate": r"\end{enumerateDeep}",
        }
        self.list["start_item"] = {"itemize": r"\\item ", "enumerate": r"\\item "}
        self.list["end_item"] = {"itemize": "", "enumerate": ""}

    def preparePublish(self):
        """Publish wrapper files for LaTeX."""
        log.debug("Generating compile script for LaTeX from %s", self.path)
        self.compile_path = self._get_compile_path()

    def publishAction(self, document, path):
        """Add file to compile.sh script."""
        self.document = document
        # If path does not end with .tex, add it.
        if not path.endswith(".tex"):
            self.documentPath = os.path.join(path, document.prefix + ".tex")
        else:
            self.documentPath = path

        log.debug("Generating compile script for LaTeX from %s", self.documentPath)
        file_to_compile = self._generate_latex_wrapper()
        self.compile_files.append(file_to_compile)

    def concludePublish(self):
        """Write out the compile.sh file."""
        common.write_lines(
            self.compile_files,
            self.compile_path,
            end=settings.WRITE_LINESEPERATOR,
            executable=True,
        )
        msg = "You can now execute the file 'compile.sh' twice in the exported folder to produce the PDFs!"
        utilities.show(msg, flush=True)

    def create_index(self, directory, index=None, extensions=(".tex",), tree=None):
        """No index for LaTeX."""

    def table_of_contents(self, linkify=None, obj=None):
        """No table of contents LaTeX."""

    def lines(self, obj, **kwargs):
        """Yield lines for a LaTeX report.

        :param obj: Item, list of Items, or Document to publish
        :param linkify: turn links into hyperlinks

        :return: iterator of lines of text

        """
        linkify = kwargs.get("linkify", False)
        for item in iter_items(obj):
            # Cap depth at 5 (LaTeX maximum)
            safe_depth = min(item.depth, 5)

            if item.heading:
                # For heading items, use PUBLISH_HEADING_LEVELS setting
                if settings.PUBLISH_HEADING_LEVELS:
                    heading_map = {
                        1: "\\section{",
                        2: "\\subsection{",
                        3: "\\subsubsection{",
                        4: "\\paragraph{",
                        5: "\\subparagraph{",
                    }
                else:
                    heading_map = {
                        1: "\\section*{",
                        2: "\\subsection*{",
                        3: "\\subsubsection*{",
                        4: "\\paragraph*{",
                        5: "\\subparagraph*{",
                    }
                heading = heading_map.get(safe_depth, heading_map[1])
                
                text_lines = item.text.splitlines()
                if item.header:
                    text_lines.insert(0, item.header)
                # Level and Text
                standard = "{h}{t}{he}".format(
                    h=heading,
                    t=_latex_convert(text_lines[0]) if text_lines else "",
                    he="}",
                )
                attr_list = self.format_attr_list(item, True)
                yield standard + attr_list
                yield from self._format_latex_text(text_lines[1:], item=item)
            else:
                # For body items (non-headings), use PUBLISH_BODY_LEVELS setting
                if settings.PUBLISH_BODY_LEVELS:
                    heading_map = {
                        1: "\\section{",
                        2: "\\subsection{",
                        3: "\\subsubsection{",
                        4: "\\paragraph{",
                        5: "\\subparagraph{",
                    }
                else:
                    heading_map = {
                        1: "\\section*{",
                        2: "\\subsection*{",
                        3: "\\subsubsection*{",
                        4: "\\paragraph*{",
                        5: "\\subparagraph*{",
                    }
                heading = heading_map.get(safe_depth, heading_map[1])
                
                uid = item.uid
                if settings.ENABLE_HEADERS:
                    if item.header:
                        uid = "{h}{{ - \\small{{}}\\texttt{{}}{u}}}".format(
                            h=_latex_convert(item.header), u=item.uid
                        )

                # Level and UID - use heading (already set based on PUBLISH_BODY_LEVELS)
                standard = "{h}{u}{he}".format(h=heading, u=uid, he="}")

                attr_list = self.format_attr_list(item, True)
                yield standard + attr_list

                # Text
                if item.text:
                    yield ""  # break before text
                    yield from self._format_latex_text(item.text.splitlines(), item=item)

                # Reference
                if item.ref:
                    yield ""  # break before reference
                    yield self.format_ref(item)

                # Reference
                if item.references:
                    yield ""  # break before reference
                    yield self.format_references(item)

                # Parent links
                if item.links:
                    yield ""  # break before links
                    items2 = item.parent_items
                    if settings.PUBLISH_CHILD_LINKS:
                        label = "Parent links:"
                    else:
                        label = "Links:"
                    links = self.format_links(items2, linkify)
                    label_links = self.format_label_links(label, links, linkify)
                    yield label_links

                # Child links
                if settings.PUBLISH_CHILD_LINKS:
                    items2 = item.find_child_items()
                    if items2:
                        yield ""  # break before links
                        label = "Child links:"
                        links = self.format_links(items2, linkify)
                        label_links = self.format_label_links(label, links, linkify)
                        yield label_links

                # Add custom publish attributes
                if item.document and item.document.publish:
                    header_printed = False
                    for attr in item.document.publish:
                        if not item.attribute(attr):
                            continue
                        if not header_printed:
                            header_printed = True
                            yield "\\begin{longtable}[\\tablealignment]{|l|p{\\attrtablecolwidth}|}"
                            yield self.HLINE
                            yield "\\tableheaderrow{Attribute} & \\tableheaderrow{Value}\\\\"
                            yield self.HLINE

                        value = item.attribute(attr)
                        
                        # ========== Handle link attributes specially ==========
                        if is_link_attribute(attr):
                            link_list = normalize_link_list(value)
                            if link_list:
                                # Convert each markdown link to LaTeX
                                converted_links = [_convert_markdown_link_to_href(link) for link in link_list]
                                
                                value_str = " \\newline ".join(converted_links) if len(converted_links) > 1 else converted_links[0]
                                yield "{} & {}\\\\".format(_escape_latex_text(attr), value_str)
                                yield self.HLINE
                                                                                        
                        # ========== Handle regular lists ==========
                        elif isinstance(value, list):
                            if len(value) > 0:
                                # Convert list items, strip whitespace
                                items = []
                                for v in value:
                                    item_str = str(v).strip()
                                    if item_str:
                                        items.append(_latex_convert(item_str))
                                
                                if items:
                                    if len(items) == 1:
                                        value_str = items[0]
                                    else:
                                        value_str = " \\newline ".join(items)
                                    
                                    yield "{} & {}\\\\".format(
                                        _escape_latex_text(attr),
                                        value_str
                                    )
                                    yield self.HLINE
                        
                        # ========== Handle dictionaries ==========
                        elif isinstance(value, dict):
                            # Format as key: value pairs
                            dict_items = []
                            for k, v in value.items():
                                k_str = _latex_convert(str(k))
                                v_str = _latex_convert(str(v).strip())
                                dict_items.append(f"\\textbf{{{k_str}}}: {v_str}")
                            
                            if dict_items:
                                value_str = " \\newline ".join(dict_items)
                                yield "{} & {}\\\\".format(
                                    _escape_latex_text(attr),
                                    value_str
                                )
                                yield self.HLINE
                        
                        # ========== Handle simple values ==========
                        else:
                            yield "{} & {}\\\\".format(
                                _escape_latex_text(attr),
                                _latex_convert(str(value))
                            )
                            yield self.HLINE
                    
                    if header_printed:
                        yield self.END_LONGTABLE
                    else:
                        yield ""

            yield ""  # break between items
            
    def format_attr_list(self, item, linkify):
        """Create a LaTeX attribute list for a heading."""
        return (
            "{l}{u}{le}{zl}{u}{le}".format(
                l="\\label{", zl="\\zlabel{", u=item.uid, le="}"
            )
            if linkify
            else ""
        )

    def format_ref(self, item):
        """Format an external reference in LaTeX."""
        if settings.CHECK_REF:
            path, line = item.find_ref()
            path = path.replace("\\", "/")  # always use unix-style paths
            if line:
                return (
                    "\\begin{{quote}} \\verb|{p}| (line {line})\\end{{quote}}".format(
                        p=path, line=line
                    )
                )
            else:
                return "\\begin{{quote}} \\verb|{p}|\\end{{quote}}".format(p=path)
        else:
            return "\\begin{{quote}} \\verb|{r}|\\end{{quote}}".format(r=item.ref)

    def format_references(self, item):
        """Format an external reference in LaTeX."""
        if settings.CHECK_REF:
            references = item.find_references()
            text_refs = []
            for ref_item in references:
                path, line = ref_item
                path = path.replace("\\", "/")  # always use unix-style paths

                if line:
                    text_refs.append(
                        "\\begin{{quote}} \\verb|{p}| (line {line})\\end{{quote}}".format(
                            p=path, line=line
                        )
                    )
                else:
                    text_refs.append(
                        "\\begin{{quote}} \\verb|{p}|\\end{{quote}}".format(p=path)
                    )

            return "\n".join(ref for ref in text_refs)
        else:
            references = item.references
            text_refs = []
            for ref_item in references:
                path = ref_item["path"]
                path = path.replace("\\", "/")  # always use unix-style paths
                text_refs.append(
                    "\\begin{{quote}} \\verb|{r}|\\end{{quote}}".format(r=path)
                )
            return "\n".join(ref for ref in text_refs)

    def format_links(self, items, linkify):
        """Format a list of linked items in LaTeX."""
        links = []
        for item in items:
            link = self.format_item_link(item, linkify=linkify)
            links.append(link)
        return ", ".join(links)

    def format_item_link(self, item, linkify=True):
        """Format an item link in LaTeX."""
        if linkify and is_item(item):
            if item.header:
                return "\\hyperref[{u}]{{{u}}}".format(u=item.uid)
            return "\\hyperref[{u}]{{{u}}}".format(u=item.uid)
        else:
            return str(item.uid)  # if not `Item`, assume this is an `UnknownItem`

    def format_label_links(self, label, links, linkify):
        """Join a string of label and links with formatting."""
        if linkify:
            return "\\textbf{{{lb}}} {ls}".format(lb=label, ls=links)
        else:
            return "\\textbf{{{lb} {ls}}}".format(lb=label, ls=links)

    def _typeset_latex_table(
        self, table_match, text, i, line, block, table_found, header_done, end_pipes
    ):
        """Typeset tables."""
        if not table_found:
            table_found, header_done, line, end_pipes = _check_for_new_table(
                table_match, text, i, line, block, table_found, header_done, end_pipes
            )
        else:
            if not header_done:
                line = self.HLINE
                header_done = True
            else:
                # Fix the line.
                line = _fix_table_line(line, end_pipes)
        return table_found, header_done, line, end_pipes

    def _format_latex_text_legacy(self, text):
        """Fix all general text formatting to use LaTeX-macros."""
        block: List[str]
        block = []
        environment_data = {}
        environment_data["table_found"] = False
        header_done = False
        environment_data["code_found"] = False
        math_found = False
        environment_data["plantuml_found"] = False
        plantuml_file = ""
        plantuml_name = ""
        plantuml_count = 0
        end_pipes = False
        for i, line in enumerate(text):
            no_paragraph = False
            #############################
            ## Fix plantuml.
            #############################
            if environment_data["plantuml_found"]:
                no_paragraph = True
            if re.findall("^`*plantuml\\s", line):
                plantuml_count = plantuml_count + 1
                plantuml_title = re.search('title="(.*)"', line)
                if plantuml_title:
                    plantuml_name = str(plantuml_title.groups(0)[0])
                else:
                    raise DoorstopError(
                        "'title' is required for plantUML processing in LaTeX."
                    )
                plantuml_file = re.sub("\\s", "-", plantuml_name)
                block.append(
                    r"\hyperref[fig:plant"
                    + str(plantuml_count)
                    + "]{"
                    + plantuml_name
                    + "}"
                )
                line = "\\begin{plantuml}{" + plantuml_file + "}"
                environment_data["plantuml_found"] = True
            if re.findall("@enduml", line):
                block.append(line)
                block.append("\\end{plantuml}")
                process_line = (
                    "\\process{"
                    + plantuml_file
                    + "}{0.8\\textwidth}{"
                    + plantuml_name
                    + "}"
                    + "{"
                    + str(plantuml_count)
                    + "}"
                )
                block.append(process_line)
                environment_data["plantuml_found"] = False
                continue
            # Skip the rest since we are in a plantuml block!
            if environment_data["plantuml_found"]:
                block.append(line)
                # Check for end of file and end all environments.
                self._check_for_eof(
                    i,
                    block,
                    text,
                    environment_data,
                    plantuml_name,
                    plantuml_file,
                )
                continue

            #############################
            ## Fix code blocks.
            #############################
            code_match = re.findall("```", line)
            if environment_data["code_found"]:
                no_paragraph = True
            if code_match:
                # Check previous line of @enduml.
                if i > 0:
                    previous_line = text[i - 1]
                    if re.findall("@enduml", previous_line):
                        continue
                if environment_data["code_found"]:
                    line = "\\end{lstlisting}"
                    environment_data["code_found"] = False
                    block.append(line)  # ✅ HINZUFÜGEN: Direkt appenden
                    self._check_for_eof(  # ✅ HINZUFÜGEN: EOF check
                        i,
                        block,
                        text,
                        environment_data,
                        plantuml_name,
                        plantuml_file,
                    )
                    continue  # ✅ HINZUFÜGEN: Skip rest der Schleife!
                else:
                    # Check for language.
                    language = re.search("```(.*)", line)
                    if language and str(language.groups(0)[0]) != "":
                        line = (
                            "\\begin{lstlisting}[language="
                            + str(language.groups(0)[0])
                            + "]"
                        )
                    else:
                        line = "\\begin{lstlisting}"
                    environment_data["code_found"] = True
            # Skip the rest since we are in a code block!
            if environment_data["code_found"]:
                block.append(line)
                # Check for end of file and end all environments.
                self._check_for_eof(
                    i,
                    block,
                    text,
                    environment_data,
                    plantuml_name,
                    plantuml_file,
                )
                continue
            # Replace ` for inline code, but not if it is already escaped.
            # First replace escaped inline code.
            line = re.sub("\\\\`", "##!!TEMPINLINE!!##", line)
            # Then replace inline code.
            line = re.sub("`(.+?)`", "\\\\lstinline`\\1`", line)
            # Then replace escaped inline code back.
            line = re.sub("##!!TEMPINLINE!!##", "\\\\`{}", line)

            #############################
            ## Fix images.
            #############################
            image_match = re.findall(r"!\[(.*)\]\((.*)\)", line)
            if image_match:
                line = _typeset_latex_image(image_match, line, block)
            #############################
            ## Fix $ and MATH.
            #############################
            math_match = re.split("\\$\\$", line)
            if len(math_match) > 1:
                # Line contains $$
                if math_found and len(math_match) == 2:
                    math_found = False
                    line = math_match[0] + "$" + math_match[1]
                elif len(math_match) == 2:
                    math_found = True
                    line = _latex_convert(math_match[0]) + "$" + math_match[1]
                elif len(math_match) == 3:
                    line = (
                        _latex_convert(math_match[0])
                        + "$"
                        + math_match[1]
                        + "$"
                        + _latex_convert(math_match[2])
                    )
                else:
                    raise DoorstopError(
                        "Cannot handle multiple math environments on one row."
                    )
            else:
                # ✅ GEÄNDERT: Nur _latex_convert wenn NICHT in Math!
                if not math_found:
                    line = _latex_convert(line)
                # else: line bleibt raw (wir sind in Math)

            # Skip all other changes if in MATH!
            if math_found:
                line = line + "\\\\"
                block.append(line)
                continue
            #############################
            ## Fix lists.
            #############################
            # Check if we are at the end of the data.
            if i == len(text) - 1:
                next_line = ""
            else:
                next_line = text[i + 1]
            no_paragraph, processed_block, line = self.process_lists(line, next_line)
            if processed_block != "":
                block.append(processed_block)
            #############################
            ## Fix tables.
            #############################
            # Check if line is part of table.
            table_match = re.findall("\\|", line)
            if table_match:
                (
                    environment_data["table_found"],
                    header_done,
                    line,
                    end_pipes,
                ) = self._typeset_latex_table(
                    table_match,
                    text,
                    i,
                    line,
                    block,
                    environment_data["table_found"],
                    header_done,
                    end_pipes,
                )
            else:
                if environment_data["table_found"]:
                    block.append(self.END_LONGTABLE)
                environment_data["table_found"] = False
                header_done = False

            # Look ahead for empty line and add paragraph.
            if i < len(text) - 1:
                next_line = text[i + 1]
                if next_line == "" and not re.search("\\\\", line) and not no_paragraph:
                    line = line + "\\\\"

            #############################
            ## All done. Add the line.
            #############################
            block.append(line)

            # Check for end of file and end all environments.
            self._check_for_eof(
                i,
                block,
                text,
                environment_data,
                plantuml_name,
                plantuml_file,
            )
        return block

    def _format_latex_text(self, text_lines, item=None):
        """
        Format text with automatic routing to appropriate handler.
        
        Args:
            text_lines: List of text lines to format
            item: Optional Item object for context
            
        Returns:
            List of formatted LaTeX lines
        """
        # Ensure we have a list
        if isinstance(text_lines, str):
            text_lines = text_lines.splitlines()
        
        # Check for complex formatting
        if _has_complex_formatting(text_lines):
            log.debug("Using legacy formatter for complex text")
            return self._format_latex_text_legacy(text_lines)
        else:
            log.debug("Using simple formatter with modern code block support")
            return self._post_process_simple_text(text_lines, item=item)

    def _post_process_simple_text(self, text_lines, item=None):
        """
        Post-process simple text for images and lists.
        
        Args:
            text_lines: List of text lines
            item: Optional Item object for context
            
        Returns:
            List of formatted LaTeX lines
        """
        # Build context
        context = {}
        if item:
            context['item_uid'] = str(item.uid)
            if hasattr(item, 'path'):
                context['file'] = item.path
            context['line_num'] = 1
            context['in_item_text'] = True
        
        # Get basic formatting with code blocks handled
        processed_lines = list(_format_simple_text_block(text_lines, context=context))
        
        result = []
        for i, line in enumerate(processed_lines):
            # Update line number in context
            line_context = context.copy()
            line_context['line_num'] = i + 1
            
            # Skip if in code environment
            if line.strip().startswith("\\begin{lstlisting}") or \
            line.strip().startswith("\\end{lstlisting}"):
                result.append(line)
                continue
            
            # Handle images
            image_match = re.findall(r"!\[(.*)\]\((.*)\)", line)
            if image_match:
                temp_block = []
                line = _typeset_latex_image(image_match, line, temp_block)
                
                # Add \\ to the last non-empty line before the image.
                # But ONLY if it's plain text, not a LaTeX command.
                for idx in range(len(result) - 1, -1, -1):
                    if result[idx].strip():  # Found last non-empty line
                        last_line = result[idx].rstrip()
                        # Only add \\ if:
                        # - Line doesn't already end with \\
                        # - Line doesn't start with \ (LaTeX command)
                        if (not last_line.endswith("\\\\") and
                            not last_line.strip().startswith("\\")):
                            result[idx] = last_line + "\\\\"
                        break

                # Add the figure block
                result.extend(temp_block)
                if line:
                    result.append(line)
                continue

            # Handle lists
            next_line = processed_lines[i + 1] if i + 1 < len(processed_lines) else ""
            no_paragraph, processed_block, line = self.process_lists(line, next_line)
            
            # If we just started a list, add \\ to previous non-empty line
            if processed_block and processed_block.strip().startswith("\\begin{"):
                # We're starting a list environment
                for idx in range(len(result) - 1, -1, -1):
                    if result[idx].strip():  # Found last non-empty line
                        last_line = result[idx].rstrip()
                        if not last_line.endswith("\\\\"):
                            result[idx] = last_line + "\\\\"
                        break

            if processed_block:
                result.append(processed_block)
            
            # NOTE: No \\ appending here - the new block-aware text processing preserves
            # blank lines for LaTeX paragraph separation. Tables, lists, and code blocks
            # have their own formatting. Adding \\ would break natural paragraph flow.

            result.append(line)        
            
        return result

    def _check_for_eof(
        self,
        index,
        block,
        text,
        environment_data,
        plantuml_name,
        plantuml_file,
    ):
        """Check for end of file and end all unended environments."""
        if index == len(text) - 1:
            if environment_data["code_found"]:
                block.append("\\end{lstlisting}")
            if environment_data["plantuml_found"]:
                block.append("\\end{plantuml}")
                block.append(
                    "\\process{"
                    + plantuml_file
                    + "}{0.8\\textwidth}{"
                    + plantuml_name
                    + "}"
                )
            if environment_data["table_found"]:
                block.append(self.END_LONGTABLE)

    def create_matrix(self, directory):
        """Create a traceability table for LaTeX."""
        # Setup.
        traceability = []
        file = os.path.join(directory, "traceability.tex")

        # Get documents for column headers
        documents = list(self.object.documents)
        count = len(documents)

        # Start the table with customizable alignment
        table_start = "\\begin{longtable}[\\matrixalignment]{"

        table_head = ""

        # Build header from document prefixes
        header_cells = []
        for document in documents:
            table_start = table_start + "|l"
            # Use matrix header styling hook
            header_cells.append("\\matrixheaderrow{" + str(document.prefix) + "}")

        table_start = table_start + "|}"
        table_head = " & ".join(header_cells) + "\\\\"

        traceability.append(table_start)
        traceability.append(
            "\\caption{Traceability matrix.}\\label{tbl:trace}\\zlabel{tbl:trace}\\\\"
        )
        traceability.append(self.HLINE)
        # Apply header background styling (if defined)
        traceability.append("\\matrixheaderbg" + table_head)
        traceability.append(self.HLINE)
        traceability.append("\\endfirsthead")
        traceability.append("\\caption{\\textit{(Continued)} Traceability matrix.}\\\\")
        traceability.append(self.HLINE)
        traceability.append("\\matrixheaderbg" + table_head)
        traceability.append(self.HLINE)
        traceability.append("\\endhead")
        traceability.append(self.HLINE)
        traceability.append(
            "\\multicolumn{{{n}}}{{r}}{{\\textit{{Continued on next page.}}}}\\\\".format(
                n=count
            )
        )
        traceability.append("\\endfoot")
        traceability.append(self.HLINE)
        traceability.append("\\endlastfoot")

        # Add data rows
        for row in self.object.get_traceability():
            row_text = ""
            for column in row:
                if len(row_text) > 0:
                    row_text = row_text + " & "
                if column:
                    row_text = row_text + "\\hyperref[{u}]{{{u}}}".format(u=str(column))
                else:
                    row_text = row_text + " "
            row_text = row_text + "\\\\"
            traceability.append(row_text)
            traceability.append(self.HLINE)

        # End the table.
        traceability.append(self.END_LONGTABLE)
        common.write_lines(traceability, file, end=settings.WRITE_LINESEPERATOR)

    def _get_compile_path(self):
        """Return the path to the compile script."""
        head, tail = os.path.split(self.path)
        # If tail ends with .tex, replace it with compile.sh.
        if tail.endswith(".tex"):
            return os.path.join(head, "compile.sh")
        return os.path.join(self.path, "compile.sh")

    def _generate_latex_wrapper(self):
        """Generate all wrapper scripts required for typesetting in LaTeX."""
        # Check for defined document attributes.
        doc_attributes = get_document_attributes(self.document)
        
        # Sanitize the document name for use as filename (replace spaces with hyphens)
        safe_name = doc_attributes["name"].replace(" ", "-")
        
        # Create the wrapper file.
        head, tail = os.path.split(self.documentPath)
        if tail != extract_prefix(self.document) + ".tex":
            log.warning(
                "LaTeX export does not support custom file names. Change in .doorstop.yml instead."
            )
        tail = safe_name + ".tex"
        self.documentPath = os.path.join(head, extract_prefix(self.document) + ".tex")
        wrapperPath = os.path.join(head, tail)
        # Load template data.
        templatePath = os.path.abspath(os.path.join(self.assetsPath, "..", "template"))
        log.info(
            "Loading template data from {}/{}.yml".format(templatePath, self.template)
        )
        template_data = read_template_data(self.assetsPath, self.template)
        check_latex_template_data(
            template_data, "{}/{}.yml".format(templatePath, self.template)
        )
        wrapper = []
        wrapper.append(
            "\\documentclass[%s]{template/%s}"
            % (", ".join(template_data["documentclass"]), self.template)
        )
        # Add required packages.
        wrapper = _add_comment(
            wrapper,
            "These packages are required.",
        )
        wrapper.append("\\usepackage{enumitem}")
        wrapper = _add_comment(wrapper, "END required packages.")
        wrapper.append("")

        # Add required packages from template data.
        wrapper = _add_comment(
            wrapper,
            "These packages were automatically added from the template configuration file.",
        )
        for package, options in template_data["usepackage"].items():
            package_line = "\\usepackage"
            if options:
                package_line += "[%s]" % ", ".join(options)
            package_line += "{%s}" % package
            wrapper.append(package_line)
        wrapper = _add_comment(
            wrapper, "END data from the template configuration file."
        )
        wrapper.append("")
        wrapper = _add_comment(
            wrapper,
            "These fields are generated from the default doc attribute in the .doorstop.yml file.",
        )
        wrapper.append(
            "\\def\\doccopyright{{{n}}}".format(
                n=_latex_convert(doc_attributes["copyright"])
            )
        )
        wrapper.append(
            "\\def\\doccategory{{{t}}}".format(
                t=_latex_convert(extract_prefix(self.document))
            )
        )
        wrapper.append(
            "\\def\\doctitle{{{n}}}".format(n=_latex_convert(doc_attributes["title"]))
        )
        wrapper.append(
            "\\def\\docref{{{n}}}".format(n=_latex_convert(doc_attributes["ref"]))
        )
        wrapper.append(
            "\\def\\docby{{{n}}}".format(n=_latex_convert(doc_attributes["by"]))
        )
        wrapper.append(
            "\\def\\docissuemajor{{{n}}}".format(
                n=_latex_convert(doc_attributes["major"])
            )
        )
        wrapper.append(
            "\\def\\docissueminor{{{n}}}".format(
                n=_latex_convert(doc_attributes["minor"])
            )
        )
        wrapper = _add_comment(wrapper, "END data from the .doorstop.yml file.")
        wrapper.append("")

        wrapper = _add_comment(
            wrapper,
            "LaTex is limited to four (4) levels of lists. The following code extends this to nine (9) levels.",
        )
        wrapper.append("% ******************************************************")
        wrapper.append("% Increase nesting level for lists")
        wrapper.append("% ******************************************************")
        wrapper.append("\\setlistdepth{9}")
        wrapper.append("\\newlist{itemizeDeep}{enumerate}{9}")
        wrapper.append("\\setlist[itemizeDeep,1]{label=\\textbullet}")
        wrapper.append(
            "\\setlist[itemizeDeep,2]{label=\\normalfont\\bfseries \\textendash}"
        )
        wrapper.append("\\setlist[itemizeDeep,3]{label=\\textasteriskcentered}")
        wrapper.append("\\setlist[itemizeDeep,4]{label=\\textperiodcentered}")
        wrapper.append("\\setlist[itemizeDeep,5]{label=\\textopenbullet}")
        wrapper.append("\\setlist[itemizeDeep,6]{label=\\textbullet}")
        wrapper.append(
            "\\setlist[itemizeDeep,7]{label=\\normalfont\\bfseries \\textendash}"
        )
        wrapper.append("\\setlist[itemizeDeep,8]{label=\\textasteriskcentered}")
        wrapper.append("\\setlist[itemizeDeep,9]{label=\\textperiodcentered}")
        wrapper.append("\\newlist{enumerateDeep}{enumerate}{9}")
        wrapper.append("\\setlist[enumerateDeep]{label*=\\arabic*.}")
        wrapper = _add_comment(wrapper, "END list depth fix.")
        wrapper.append("")

        info_text_set = False
        for external, _ in iter_documents(self.object, self.path, ".tex"):
            # Check for defined document attributes.
            external_doc_attributes = get_document_attributes(external)
            # Don't add self.
            if external_doc_attributes["name"] != doc_attributes["name"]:
                if not info_text_set:
                    wrapper = _add_comment(
                        wrapper,
                        "These are automatically added external references to make cross-references work between the PDFs.",
                    )
                    info_text_set = True
                
                # Sanitize external document name
                external_safe_name = external_doc_attributes["name"].replace(" ", "-")
                
                wrapper.append(
                    "\\zexternaldocument{{{n}}}".format(
                        n=external_safe_name
                    )
                )
                wrapper.append(
                    "\\externaldocument{{{n}}}".format(
                        n=external_safe_name
                    )
                )
        if info_text_set:
            wrapper = _add_comment(wrapper, "END external references.")
            wrapper.append("")
        wrapper = _add_comment(
            wrapper,
            "These lines were automatically added from the template configuration file to allow full customization of the template _before_ \\begin{document}.",
        )
        for line in template_data["before_begin_document"]:
            wrapper.append(line)
        wrapper = _add_comment(
            wrapper, "END custom data from the template configuration file."
        )
        wrapper.append("")
        wrapper.append("\\begin{document}")
        wrapper = _add_comment(
            wrapper,
            "These lines were automatically added from the template configuration file to allow full customization of the template _after_ \\begin{document}.",
        )
        for line in template_data["after_begin_document"]:
            wrapper.append(line)
        wrapper = _add_comment(
            wrapper, "END custom data from the template configuration file."
        )
        wrapper.append("")
        wrapper = _add_comment(wrapper, "Load the doorstop data file.")
        wrapper.append("\\input{{{n}.tex}}".format(n=extract_prefix(self.document)))
        wrapper = _add_comment(wrapper, "END doorstop data file.")
        wrapper.append("")
        # Include traceability matrix
        if self.matrix:
            wrapper = _add_comment(wrapper, "Add traceability matrix.")
            if settings.PUBLISH_HEADING_LEVELS:
                wrapper.append("\\section{Traceability}")
            else:
                wrapper.append("\\section*{Traceability}")
            wrapper.append("\\input{traceability.tex}")
            wrapper = _add_comment(wrapper, "END traceability matrix.")
            wrapper.append("")
        wrapper.append("\\end{document}")
        common.write_lines(wrapper, wrapperPath, end=settings.WRITE_LINESEPERATOR)

        # Add to compile.sh as return value.
        return 'pdflatex -halt-on-error -shell-escape "{n}.tex"'.format(
            n=safe_name
        )