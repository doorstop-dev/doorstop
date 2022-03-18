# SPDX-License-Identifier: LGPL-3.0-only

"""Functions to publish LaTeX documents."""

import os
import re

from doorstop import common, settings
from doorstop.common import DoorstopError
from doorstop.core.types import is_item, iter_items

log = common.logger(__name__)


def _lines_latex(obj, **kwargs):
    """Yield lines for a LaTeX report.

    :param obj: Item, list of Items, or Document to publish
    :param linkify: turn links into hyperlinks

    :return: iterator of lines of text

    """
    linkify = kwargs.get("linkify", False)
    for item in iter_items(obj):
        heading = "\\" + "sub" * (item.depth - 1) + "section*{"
        headingLev = "\\" + "sub" * (item.depth - 1) + "section{"

        if item.heading:
            text_lines = item.text.splitlines()
            # Level and Text
            if settings.PUBLISH_HEADING_LEVELS:
                standard = "{h}{t}{he}".format(
                    h=headingLev, t=text_lines[0] if text_lines else "", he="}"
                )
            else:
                standard = "{h}{t}{he}".format(
                    h=heading, t=text_lines[0] if text_lines else "", he="}"
                )
            attr_list = _format_latex_attr_list(item, True)
            yield standard + attr_list
            yield from text_lines[1:]
        else:
            uid = item.uid
            if settings.ENABLE_HEADERS:
                if item.header:
                    uid = "{h}{{\\small{{}}{u}}}".format(h=item.header, u=item.uid)
                else:
                    uid = "{u}".format(u=item.uid)

            # Level and UID
            if settings.PUBLISH_BODY_LEVELS:
                standard = "{h}{u}{he}".format(h=headingLev, u=uid, he="}")
            else:
                standard = "{h}{u}{he}".format(h=heading, u=uid, he="}")

            attr_list = _format_latex_attr_list(item, True)
            yield standard + attr_list

            # Text
            if item.text:
                yield ""  # break before text
                yield from _format_latex_text(item.text.splitlines())

            # Reference
            if item.ref:
                yield ""  # break before reference
                yield _format_latex_ref(item)

            # Reference
            if item.references:
                yield ""  # break before reference
                yield _format_latex_references(item)

            # Parent links
            if item.links:
                yield ""  # break before links
                items2 = item.parent_items
                if settings.PUBLISH_CHILD_LINKS:
                    label = "Parent links:"
                else:
                    label = "Links:"
                links = _format_latex_links(items2, linkify)
                label_links = _format_latex_label_links(label, links, linkify)
                yield label_links

            # Child links
            if settings.PUBLISH_CHILD_LINKS:
                items2 = item.find_child_items()
                if items2:
                    yield ""  # break before links
                    label = "Child links:"
                    links = _format_latex_links(items2, linkify)
                    label_links = _format_latex_label_links(label, links, linkify)
                    yield label_links

            # Add custom publish attributes
            if item.document and item.document.publish:
                header_printed = False
                for attr in item.document.publish:
                    if not item.attribute(attr):
                        continue
                    if not header_printed:
                        header_printed = True
                        yield "\\begin{longtable}{|l|l|}"
                        yield "Attribute & Value\\\\"
                        yield "\\hline"
                    yield "{} & {}".format(attr, item.attribute(attr))
                if header_printed:
                    yield "\\end{longtable}"
                else:
                    yield ""

        yield ""  # break between items


def _format_latex_attr_list(item, linkify):
    """Create a LaTeX attribute list for a heading."""
    return (
        "{l}{u}{le}{zl}{u}{le}".format(l="\\label{", zl="\\zlabel{", u=item.uid, le="}")
        if linkify
        else ""
    )


def _format_latex_ref(item):
    """Format an external reference in LaTeX."""
    if settings.CHECK_REF:
        path, line = item.find_ref()
        path = path.replace("\\", "/")  # always use unix-style paths
        if line:
            return "\\begin{{quote}} \\verb|{p}| (line {line})\\end{{quote}}".format(
                p=path, line=line
            )
        else:
            return "\\begin{{quote}} \\verb|{p}|\\end{{quote}}".format(p=path)
    else:
        return "\\begin{{quote}} \\verb|{r}|\\end{{quote}}".format(r=item.ref)


def _format_latex_references(item):
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


def _format_latex_links(items, linkify):
    """Format a list of linked items in LaTeX."""
    links = []
    for item in items:
        link = _format_latex_item_link(item, linkify=linkify)
        links.append(link)
    return ", ".join(links)


def _format_latex_item_link(item, linkify=True):
    """Format an item link in LaTeX."""
    if linkify and is_item(item):
        if item.header:
            return "\\hyperref[{u}]{{{u}}}".format(u=item.uid)
        return "\\hyperref[{u}]{{{u}}}".format(u=item.uid)
    else:
        return str(item.uid)  # if not `Item`, assume this is an `UnknownItem`


def _format_latex_label_links(label, links, linkify):
    """Join a string of label and links with formatting."""
    if linkify:
        return "\\textbf{{{lb}}} {ls}".format(lb=label, ls=links)
    else:
        return "\\textbf{{{lb} {ls}}}".format(lb=label, ls=links)


def _latex_convert(line):
    """Single string conversion for LaTeX."""
    # Replace $.
    line = re.sub("\\$", "\\\\$", line)
    #############################
    ## Fix BOLD and ITALICS and Strikethrough.
    #############################
    # Replace **.
    line = re.sub("\\*\\*(.*)\\*\\*", "\\\\textbf{\\1}", line)
    # Replace __.
    line = re.sub("__(.*)__", "\\\\textbf{\\1}", line)
    # Replace *.
    line = re.sub("\\*(.*)\\*", "\\\\textit{\\1}", line)
    # Replace _.
    line = re.sub("_(.*)_", "\\\\textit{\\1}", line)
    # Replace ~~.
    line = re.sub("~~(.*)~~", "\\\\sout{\\1}", line)
    #############################
    ## Fix manual heading levels
    #############################
    if settings.PUBLISH_BODY_LEVELS:
        star = ""
    else:
        star = "*"
    # Replace ######.
    line = re.sub(
        "###### (.*)",
        "\\\\subparagraph" + star + "{\\1 \\\\textbf{NOTE: This level is too deep.}}",
        line,
    )
    # Replace #####.
    line = re.sub("##### (.*)", "\\\\subparagraph" + star + "{\\1}", line)
    # Replace ####.
    line = re.sub("#### (.*)", "\\\\paragraph" + star + "{\\1}", line)
    # Replace ###.
    line = re.sub("### (.*)", "\\\\subsubsection" + star + "{\\1}", line)
    # Replace ##.
    line = re.sub("## (.*)", "\\\\subsection" + star + "{\\1}", line)
    # Replace #.
    line = re.sub("# (.*)", "\\\\section" + star + "{\\1}", line)
    return line


def _format_latex_text(text):
    """Fix all general text formatting to use LaTeX-macros."""
    block = []
    tableFound = False
    headerDone = False
    codeFound = False
    mathFound = False
    plantUMLFound = False
    enumerationFound = False
    itemizeFound = False
    for i, line in enumerate(text):
        noParagraph = False
        #############################
        ## Fix images.
        #############################
        image_match = re.findall(r"!\[(.*)\]\((.*)\)", line)
        if image_match:
            image_title, image_path = image_match[0]
            # Check for title. If not found, alt_text will be used as caption.
            title_match = re.findall(r'(.*)\s+"(.*)"', image_path)
            if title_match:
                image_path, image_title = title_match[0]
            # Make a safe label.
            label = "fig:{l}".format(l=re.sub("[^0-9a-zA-Z]+", "", image_title))
            # Make the string to replace!
            replacement = (
                r"\includegraphics[width=0.8\textwidth]{"
                + image_path
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

        #############################
        ## Fix $ and MATH.
        #############################
        math_match = re.split("\\$\\$", line)
        if len(math_match) > 1:
            if mathFound and len(math_match) == 2:
                mathFound = False
                line = math_match[0] + "$" + _latex_convert(math_match[1])
            elif len(math_match) == 2:
                mathFound = True
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
            line = _latex_convert(line)
        # Skip all other changes if in MATH!
        if mathFound:
            line = line + "\\\\"
            block.append(line)
            continue
        #############################
        ## Fix code blocks.
        #############################
        code_match = re.findall("```", line)
        if codeFound:
            noParagraph = True
        if code_match:
            if codeFound:
                block.append("\\end{lstlisting}")
                codeFound = False
            else:
                block.append("\\begin{lstlisting}")
                codeFound = True
            # Replace ```.
            line = re.sub("```", "", line)
        # Replace ` for inline code.
        line = re.sub("`(.*)`", "\\\\lstinline`\\1`", line)
        #############################
        ## Fix enumeration.
        #############################
        enumeration_match = re.findall("^[0-9]+\\.\\s(.*)", line)
        if enumeration_match and not enumerationFound:
            block.append("\\begin{enumerate}")
            enumerationFound = True
        if enumerationFound:
            noParagraph = True
            if enumeration_match:
                # Replace the number.
                line = re.sub("^[0-9]+\\.\\s", "\\\\item ", line)
                # Look ahead - need empty line to end enumeration!
                if i < len(text) - 1:
                    nextLine = text[i + 1]
                    if nextLine == "":
                        block.append(line)
                        line = "\\end{enumerate}"
                        enumerationFound = False
            else:
                # Look ahead - need empty line to end enumeration!
                if i < len(text) - 1:
                    nextLine = text[i + 1]
                    if nextLine == "":
                        block.append(line)
                        line = "\\end{enumerate}"
                        enumerationFound = False
        #############################
        ## Fix itemize.
        #############################
        itemize_match = re.findall("^[\\*+-]\\s(.*)", line)
        if itemize_match and not itemizeFound:
            block.append("\\begin{itemize}")
            itemizeFound = True
        if itemizeFound:
            noParagraph = True
            if itemize_match:
                # Replace the number.
                line = re.sub("^[\\*+-]\\s", "\\\\item ", line)
                # Look ahead - need empty line to end itemize!
                if i < len(text) - 1:
                    nextLine = text[i + 1]
                    if nextLine == "":
                        block.append(line)
                        line = "\\end{itemize}"
                        itemizeFound = False
            else:
                # Look ahead - need empty line to end itemize!
                if i < len(text) - 1:
                    nextLine = text[i + 1]
                    if nextLine == "":
                        block.append(line)
                        line = "\\end{itemize}"
                        itemizeFound = False

        #############################
        ## Fix tables.
        #############################
        # Check if line is part of table.
        table_match = re.findall("\\|", line)
        if table_match:
            if not tableFound:
                # Check next line for minimum 3 dashes and the same count of |.
                if i < len(text) - 1:
                    nextLine = text[i + 1]
                    table_match_next = re.findall("\\|", nextLine)
                    if table_match_next:
                        if len(table_match) == len(table_match_next):
                            table_match_dashes = re.findall("-{3,}", nextLine)
                            if table_match_dashes:
                                tableFound = True
                                endPipes = bool(
                                    len(table_match) > len(table_match_dashes)
                                )
                                nextLine = re.sub(":-+:", "c", nextLine)
                                nextLine = re.sub("-+:", "r", nextLine)
                                nextLine = re.sub("-+", "l", nextLine)
                                tableHeader = "\\begin{longtable}{" + nextLine + "}"
                                block.append(tableHeader)
                                # Fix the header.
                                line = re.sub("\\|", "&", line)
                                if endPipes:
                                    line = re.sub("^\\s*&", "", line)
                                    line = re.sub("&\\s*$", "\\\\\\\\", line)
                                else:
                                    line = line + "\\\\"
                            else:
                                log.warning(
                                    "Possibly incorrectly specified table found."
                                )
                        else:
                            log.warning("Possibly unbalanced table found.")

            else:
                if not headerDone:
                    line = "\\hline"
                    headerDone = True
                else:
                    # Fix the line.
                    line = re.sub("\\|", "&", line)
                    if endPipes:
                        line = re.sub("^\\s*&", "", line)
                        line = re.sub("&\\s*$", "\\\\\\\\", line)
                    else:
                        line = line + "\\\\"
        else:
            if tableFound:
                block.append("\\end{longtable}")
            tableFound = False
            headerDone = False
        #############################
        ## Fix plantuml.
        #############################
        if plantUMLFound:
            noParagraph = True
        if re.findall("^plantuml\\s", line):
            plantUML_title = re.search('title="(.*)"', line)
            if plantUML_title:
                plantUMLName = plantUML_title.groups(0)[0]
            else:
                raise DoorstopError(
                    "'title' is required for plantUML processing in LaTeX."
                )
            plantUMLFile = re.sub("\\s", "-", plantUMLName)
            line = "\\begin{plantuml}{" + plantUMLFile + "}"
            plantUMLFound = True
        if re.findall("@enduml", line):
            block.append(line)
            block.append("\\end{plantuml}")
            line = (
                "\\process{" + plantUMLFile + "}{0.8\\textwidth}{" + plantUMLName + "}"
            )
            plantUMLFound = False

        # Look ahead for empty line and add paragraph.
        if i < len(text) - 1:
            nextLine = text[i + 1]
            if nextLine == "" and not re.search("\\\\", line) and not noParagraph:
                line = line + "\\\\"

        #############################
        ## All done. Add the line.
        #############################
        block.append(line)

        # Check for end of file and end all environments.
        if i == len(text) - 1:
            if codeFound:
                block.append("\\end{lstlisting}")
            if enumerationFound:
                block.append("\\end{enumerate}")
            if itemizeFound:
                block.append("\\end{itemize}")
            if plantUMLFound:
                block.append("\\end{plantuml}")
                block.append(
                    "\\process{"
                    + plantUMLFile
                    + "}{0.8\\textwidth}{"
                    + plantUMLName
                    + "}"
                )
            if tableFound:
                block.append("\\end{longtable}")
    return block


def _matrix_latex(table, path):
    """Create a traceability table for LaTeX."""
    # Setup.
    traceability = []
    head, tail = os.path.split(path)
    tail = "traceability.tex"
    file = os.path.join(head, tail)
    count = 0
    # Start the table.
    table_start = "\\begin{longtable}{"
    table_head = ""
    header_data = table.__next__()
    for column in header_data:
        count = count + 1
        table_start = table_start + "|l"
        if len(table_head) > 0:
            table_head = table_head + " & "
        table_head = table_head + "\\textbf{" + str(column) + "}"
    table_start = table_start + "|}"
    table_head = table_head + "\\\\"
    traceability.append(table_start)
    traceability.append(
        "\\caption{Traceability matrix.}\\label{tbl:trace}\\zlabel{tbl:trace}\\\\"
    )
    traceability.append("\\hline")
    traceability.append(table_head)
    traceability.append("\\hline")
    traceability.append("\\endfirsthead")
    traceability.append("\\caption{\\textit{(Continued)} Traceability matrix.}\\\\")
    traceability.append("\\hline")
    traceability.append(table_head)
    traceability.append("\\hline")
    traceability.append("\\endhead")
    traceability.append("\\hline")
    traceability.append(
        "\\multicolumn{{{n}}}{{r}}{{\\textit{{Continued on next page.}}}}\\\\".format(
            n=count
        )
    )
    traceability.append("\\endfoot")
    traceability.append("\\hline")
    traceability.append("\\endlastfoot")
    # Add rows.
    for row in table:
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
        traceability.append("\\hline")
    # End the table.
    traceability.append("\\end{longtable}")
    common.write_lines(traceability, file)
