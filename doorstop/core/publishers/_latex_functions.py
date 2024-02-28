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


def _latex_convert(line):
    """Single string conversion for LaTeX."""
    #############################
    ## Fix all special characters.
    #############################
    # Replace $.
    line = re.sub("\\$", "\\\\$", line)
    # Replace &.
    line = re.sub("&", "\\\\&", line)
    #############################
    ## Fix BOLD and ITALICS and Strikethrough.
    #############################
    # Replace **.
    line = re.sub("\\*\\*(.*?)\\*\\*", "\\\\textbf{\\1}", line)
    # Replace __.
    line = re.sub("__(.*?)__", "\\\\textbf{\\1}", line)
    # Replace *.
    line = re.sub("\\*(.*?)\\*", "\\\\textit{\\1}", line)
    # Replace _.
    line = re.sub(r"_(?<!\\_)(.*?)_(?<!\\_)", "\\\\textit{\\1}", line)
    # Replace ~~.
    line = re.sub("~~(.*?)~~", "\\\\sout{\\1}", line)
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


def _typeset_latex_image(image_match, line, block):
    """Typeset images."""
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
    return line


def _fix_table_line(line, end_pipes):
    r"""Fix table line.

    Fix each line typeset for tables by adding & for column breaking, \\ for row
    breaking and fixing pipes for tables with outside borders.
    """
    line = re.sub("\\|", "&", line)
    if end_pipes:
        line = re.sub("^\\s*&", "", line)
        line = re.sub("&\\s*$", "\\\\\\\\", line)
    else:
        line = line + "\\\\"
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
