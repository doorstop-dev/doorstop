# SPDX-License-Identifier: LGPL-3.0-only

"""Functions to publish LaTeX documents."""

import os
import re
from typing import List

from doorstop import common, settings
from doorstop.cli import utilities
from doorstop.common import DoorstopError
from doorstop.core.publishers.base import BasePublisher
from doorstop.core.template import check_latex_template_data, read_template_data
from doorstop.core.types import is_item, iter_documents, iter_items

log = common.logger(__name__)


class LaTeXPublisher(BasePublisher):
    """LaTeX publisher."""

    def __init__(self, obj):
        super()
        self.END_ENUMERATE = "\\end{enumerate}"
        self.END_ITEMIZE = "\\end{itemize}"
        self.END_LONGTABLE = "\\end{longtable}"
        self.HLINE = "\\hline"
        self.compile_files = []
        self.compile_path = ""

    def preparePublish(self):
        """Publish wrapper files for LaTeX."""
        log.debug("Generating compile script for LaTeX from %s", self.path)
        self.compile_path = self._get_compile_path()

    def publishAction(self, object, path):
        """Add file to compile.sh script."""
        self.document = object
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

    def index(self, directory, index=None, extensions=(".html",), tree=None):
        """No index for LaTeX."""
        pass

    def lines(self, obj, **kwargs):
        """Yield lines for a LaTeX report.

        :param obj: Item, list of Items, or Document to publish
        :param linkify: turn links into hyperlinks

        :return: iterator of lines of text

        """
        linkify = kwargs.get("linkify", False)
        for item in iter_items(obj):
            heading = "\\" + "sub" * (item.depth - 1) + "section*{"
            heading_level = "\\" + "sub" * (item.depth - 1) + "section{"

            if item.heading:
                text_lines = item.text.splitlines()
                if item.header:
                    text_lines.insert(0, item.header)
                # Level and Text
                if settings.PUBLISH_HEADING_LEVELS:
                    standard = "{h}{t}{he}".format(
                        h=heading_level,
                        t=self._latex_convert(text_lines[0]) if text_lines else "",
                        he="}",
                    )
                else:
                    standard = "{h}{t}{he}".format(
                        h=heading,
                        t=self._latex_convert(text_lines[0]) if text_lines else "",
                        he="}",
                    )
                attr_list = self.format_attr_list(item, True)
                yield standard + attr_list
                yield from self._format_latex_text(text_lines[1:])
            else:
                uid = item.uid
                if settings.ENABLE_HEADERS:
                    if item.header:
                        uid = "{h}{{\\small{{}}{u}}}".format(
                            h=self._latex_convert(item.header), u=item.uid
                        )
                    else:
                        uid = "{u}".format(u=item.uid)

                # Level and UID
                if settings.PUBLISH_BODY_LEVELS:
                    standard = "{h}{u}{he}".format(h=heading_level, u=uid, he="}")
                else:
                    standard = "{h}{u}{he}".format(h=heading, u=uid, he="}")

                attr_list = self.format_attr_list(item, True)
                yield standard + attr_list

                # Text
                if item.text:
                    yield ""  # break before text
                    yield from self._format_latex_text(item.text.splitlines())

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
                            yield "\\begin{longtable}{|l|l|}"
                            yield "Attribute & Value\\\\"
                            yield self.HLINE
                        yield "{} & {}".format(attr, item.attribute(attr))
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

    def _latex_convert(self, line):
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
            "\\\\subparagraph"
            + star
            + "{\\1 \\\\textbf{NOTE: This level is too deep.}}",
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

    def _typeset_latex_image(self, image_match, line, block):
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
            + self._latex_convert(image_title)
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

    def _fix_table_line(self, line, end_pipes):
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
        self, table_match, text, i, line, block, table_found, header_done, end_pipes
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
                        line = self._fix_table_line(line, end_pipes)
                    else:
                        log.warning("Possibly incorrectly specified table found.")
                else:
                    log.warning("Possibly unbalanced table found.")
        return table_found, header_done, line, end_pipes

    def _typeset_latex_table(
        self, table_match, text, i, line, block, table_found, header_done, end_pipes
    ):
        """Typeset tables."""
        if not table_found:
            table_found, header_done, line, end_pipes = self._check_for_new_table(
                table_match, text, i, line, block, table_found, header_done, end_pipes
            )
        else:
            if not header_done:
                line = self.HLINE
                header_done = True
            else:
                # Fix the line.
                line = self._fix_table_line(line, end_pipes)
        return table_found, header_done, line, end_pipes

    def _format_latex_text(self, text):
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
        environment_data["enumeration_found"] = False
        environment_data["itemize_found"] = False
        end_pipes = False
        for i, line in enumerate(text):
            no_paragraph = False
            #############################
            ## Fix code blocks.
            #############################
            code_match = re.findall("```", line)
            if environment_data["code_found"]:
                no_paragraph = True
            if code_match:
                if environment_data["code_found"]:
                    block.append("\\end{lstlisting}")
                    environment_data["code_found"] = False
                else:
                    block.append("\\begin{lstlisting}")
                    environment_data["code_found"] = True
                # Replace ```.
                line = re.sub("```", "", line)
            # Skip the rest since we are in a code block!
            if environment_data["code_found"]:
                block.append(line)
                # Check for end of file and end all environments.
                self._check_for_eof(
                    i, block, text, environment_data, plantuml_name, plantuml_file
                )
                continue
            # Replace ` for inline code.
            line = re.sub("`(.*?)`", "\\\\lstinline`\\1`", line)
            #############################
            ## Fix images.
            #############################
            image_match = re.findall(r"!\[(.*)\]\((.*)\)", line)
            if image_match:
                line = self._typeset_latex_image(image_match, line, block)
            #############################
            ## Fix $ and MATH.
            #############################
            math_match = re.split("\\$\\$", line)
            if len(math_match) > 1:
                if math_found and len(math_match) == 2:
                    math_found = False
                    line = math_match[0] + "$" + self._latex_convert(math_match[1])
                elif len(math_match) == 2:
                    math_found = True
                    line = self._latex_convert(math_match[0]) + "$" + math_match[1]
                elif len(math_match) == 3:
                    line = (
                        self._latex_convert(math_match[0])
                        + "$"
                        + math_match[1]
                        + "$"
                        + self._latex_convert(math_match[2])
                    )
                else:
                    raise DoorstopError(
                        "Cannot handle multiple math environments on one row."
                    )
            else:
                line = self._latex_convert(line)
            # Skip all other changes if in MATH!
            if math_found:
                line = line + "\\\\"
                block.append(line)
                continue
            #############################
            ## Fix enumeration.
            #############################
            enumeration_match = re.findall(r"^\d+\.\s(.*)", line)
            if enumeration_match and not environment_data["enumeration_found"]:
                block.append("\\begin{enumerate}")
                environment_data["enumeration_found"] = True
            if environment_data["enumeration_found"]:
                no_paragraph = True
                if enumeration_match:
                    # Replace the number.
                    line = re.sub(r"^\d+\.\s", "\\\\item ", line)
                    # Look ahead - need empty line to end enumeration!
                    if i < len(text) - 1:
                        next_line = text[i + 1]
                        if next_line == "":
                            block.append(line)
                            line = self.END_ENUMERATE
                            environment_data["enumeration_found"] = False
                else:
                    # Look ahead - need empty line to end enumeration!
                    if i < len(text) - 1:
                        next_line = text[i + 1]
                        if next_line == "":
                            block.append(line)
                            line = self.END_ENUMERATE
                            environment_data["enumeration_found"] = False
            #############################
            ## Fix itemize.
            #############################
            itemize_match = re.findall("^[\\*+-]\\s(.*)", line)
            if itemize_match and not environment_data["itemize_found"]:
                block.append("\\begin{itemize}")
                environment_data["itemize_found"] = True
            if environment_data["itemize_found"]:
                no_paragraph = True
                if itemize_match:
                    # Replace the number.
                    line = re.sub("^[\\*+-]\\s", "\\\\item ", line)
                    # Look ahead - need empty line to end itemize!
                    if i < len(text) - 1:
                        next_line = text[i + 1]
                        if next_line == "":
                            block.append(line)
                            line = self.END_ITEMIZE
                            environment_data["itemize_found"] = False
                else:
                    # Look ahead - need empty line to end itemize!
                    if i < len(text) - 1:
                        next_line = text[i + 1]
                        if next_line == "":
                            block.append(line)
                            line = self.END_ITEMIZE
                            environment_data["itemize_found"] = False

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
            #############################
            ## Fix plantuml.
            #############################
            if environment_data["plantuml_found"]:
                no_paragraph = True
            if re.findall("^plantuml\\s", line):
                plantuml_title = re.search('title="(.*)"', line)
                if plantuml_title:
                    plantuml_name = plantuml_title.groups(0)[0]
                else:
                    raise DoorstopError(
                        "'title' is required for plantUML processing in LaTeX."
                    )
                plantuml_file = re.sub("\\s", "-", plantuml_name)
                line = "\\begin{plantuml}{" + plantuml_file + "}"
                environment_data["plantuml_found"] = True
            if re.findall("@enduml", line):
                block.append(line)
                block.append("\\end{plantuml}")
                line = (
                    "\\process{"
                    + plantuml_file
                    + "}{0.8\\textwidth}{"
                    + plantuml_name
                    + "}"
                )
                environment_data["plantuml_found"] = False

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
                i, block, text, environment_data, plantuml_name, plantuml_file
            )
        return block

    def _check_for_eof(
        self, index, block, text, environment_data, plantuml_name, plantuml_file
    ):
        """Check for end of file and end all unended environments."""
        if index == len(text) - 1:
            if environment_data["code_found"]:
                block.append("\\end{lstlisting}")
            if environment_data["enumeration_found"]:
                block.append(self.END_ENUMERATE)
            if environment_data["itemize_found"]:
                block.append(self.END_ITEMIZE)
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

    def matrix(self, table, path):
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
        traceability.append(self.HLINE)
        traceability.append(table_head)
        traceability.append(self.HLINE)
        traceability.append("\\endfirsthead")
        traceability.append("\\caption{\\textit{(Continued)} Traceability matrix.}\\\\")
        traceability.append(self.HLINE)
        traceability.append(table_head)
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
            traceability.append(self.HLINE)
        # End the table.
        traceability.append(self.END_LONGTABLE)
        common.write_lines(traceability, file, end=settings.WRITE_LINESEPERATOR)

    def _get_compile_path(self):
        """Return the path to the compile script."""
        head, tail = os.path.split(self.path)
        tail = "compile.sh"
        return os.path.join(head, tail)

    def _get_document_attributes(self, obj):
        """Try to get attributes from document."""
        doc_attributes = {}
        doc_attributes["name"] = "doc-" + obj.prefix
        log.debug("Document name is '%s'", doc_attributes["name"])
        doc_attributes["title"] = "Test document for development of _Doorstop_"
        doc_attributes["ref"] = ""
        doc_attributes["by"] = ""
        doc_attributes["major"] = ""
        doc_attributes["minor"] = ""
        doc_attributes["copyright"] = "Doorstop"
        try:
            attribute_defaults = obj.__getattribute__("_attribute_defaults")
            if attribute_defaults:
                if attribute_defaults["doc"]["name"]:
                    doc_attributes["name"] = attribute_defaults["doc"]["name"]
                if attribute_defaults["doc"]["title"]:
                    doc_attributes["title"] = attribute_defaults["doc"]["title"]
                if attribute_defaults["doc"]["ref"]:
                    doc_attributes["ref"] = attribute_defaults["doc"]["ref"]
                if attribute_defaults["doc"]["by"]:
                    doc_attributes["by"] = attribute_defaults["doc"]["by"]
                if attribute_defaults["doc"]["major"]:
                    doc_attributes["major"] = attribute_defaults["doc"]["major"]
                if attribute_defaults["doc"]["minor"]:
                    doc_attributes["minor"] = attribute_defaults["doc"]["minor"]
                if attribute_defaults["doc"]["copyright"]:
                    doc_attributes["copyright"] = attribute_defaults["doc"]["copyright"]
        except AttributeError:
            pass
        return doc_attributes

    def _generate_latex_wrapper(self):
        """Generate all wrapper scripts required for typesetting in LaTeX."""
        # Check for defined document attributes.
        doc_attributes = self._get_document_attributes(self.document)
        # Create the wrapper file.
        head, tail = os.path.split(self.documentPath)
        if tail != self.extract_prefix(self.document) + ".tex":
            log.warning(
                "LaTeX export does not support custom file names. Change in .doorstop.yml instead."
            )
        tail = doc_attributes["name"] + ".tex"
        self.documentPath = os.path.join(
            head, self.extract_prefix(self.document) + ".tex"
        )
        wrapperPath = os.path.join(head, tail)
        # Load template data.
        template_data = read_template_data(self.assetsPath, self.template)
        check_latex_template_data(template_data)
        wrapper = []
        wrapper.append(
            "\\documentclass[%s]{template/%s}"
            % (", ".join(template_data["documentclass"]), self.template)
        )
        # Add required packages from template data.
        wrapper = self._add_comment(
            wrapper,
            "These packages were automatically added from the template configuration file.",
        )
        for package, options in template_data["usepackage"].items():
            package_line = "\\usepackage"
            if options:
                package_line += "[%s]" % ", ".join(options)
            package_line += "{%s}" % package
            wrapper.append(package_line)
        wrapper = self._add_comment(
            wrapper, "END data from the template configuration file."
        )
        wrapper.append("")
        wrapper = self._add_comment(
            wrapper,
            "These fields are generated from the default doc attribute in the .doorstop.yml file.",
        )
        wrapper.append(
            "\\def\\doccopyright{{{n}}}".format(
                n=self._latex_convert(doc_attributes["copyright"])
            )
        )
        wrapper.append(
            "\\def\\doccategory{{{t}}}".format(
                t=self._latex_convert(self.extract_prefix(self.document))
            )
        )
        wrapper.append(
            "\\def\\doctitle{{{n}}}".format(
                n=self._latex_convert(doc_attributes["title"])
            )
        )
        wrapper.append(
            "\\def\\docref{{{n}}}".format(n=self._latex_convert(doc_attributes["ref"]))
        )
        wrapper.append(
            "\\def\\docby{{{n}}}".format(n=self._latex_convert(doc_attributes["by"]))
        )
        wrapper.append(
            "\\def\\docissuemajor{{{n}}}".format(
                n=self._latex_convert(doc_attributes["major"])
            )
        )
        wrapper.append(
            "\\def\\docissueminor{{{n}}}".format(
                n=self._latex_convert(doc_attributes["minor"])
            )
        )
        wrapper = self._add_comment(wrapper, "END data from the .doorstop.yml file.")
        wrapper.append("")
        info_text_set = False
        for external, _ in iter_documents(self.object, self.path, ".tex"):
            # Check for defined document attributes.
            external_doc_attributes = self._get_document_attributes(external)
            # Don't add self.
            if external_doc_attributes["name"] != doc_attributes["name"]:
                if not info_text_set:
                    wrapper = self._add_comment(
                        wrapper,
                        "These are automatically added external references to make cross-references work between the PDFs.",
                    )
                    info_text_set = True
                wrapper.append(
                    "\\zexternaldocument{{{n}}}".format(
                        n=external_doc_attributes["name"]
                    )
                )
                wrapper.append(
                    "\\externaldocument{{{n}}}".format(
                        n=external_doc_attributes["name"]
                    )
                )
        if info_text_set:
            wrapper = self._add_comment(wrapper, "END external references.")
            wrapper.append("")
        wrapper = self._add_comment(
            wrapper,
            "These lines were automatically added from the template configuration file to allow full customization of the template _before_ \\begin{document}.",
        )
        for line in template_data["before_begin_document"]:
            wrapper.append(line)
        wrapper = self._add_comment(
            wrapper, "END custom data from the template configuration file."
        )
        wrapper.append("")
        wrapper.append("\\begin{document}")
        wrapper = self._add_comment(
            wrapper,
            "These lines were automatically added from the template configuration file to allow full customization of the template _after_ \\begin{document}.",
        )
        for line in template_data["after_begin_document"]:
            wrapper.append(line)
        wrapper = self._add_comment(
            wrapper, "END custom data from the template configuration file."
        )
        wrapper.append("")
        wrapper = self._add_comment(wrapper, "Load the doorstop data file.")
        wrapper.append(
            "\\input{{{n}.tex}}".format(n=self.extract_prefix(self.document))
        )
        wrapper = self._add_comment(wrapper, "END doorstop data file.")
        wrapper.append("")
        # Include traceability matrix
        if self.matrix:
            wrapper = self._add_comment(wrapper, "Add traceability matrix.")
            if settings.PUBLISH_HEADING_LEVELS:
                wrapper.append("\\section{Traceability}")
            else:
                wrapper.append("\\section*{Traceability}")
            wrapper.append("\\input{traceability.tex}")
            wrapper = self._add_comment(wrapper, "END traceability matrix.")
            wrapper.append("")
        wrapper.append("\\end{document}")
        common.write_lines(wrapper, wrapperPath, end=settings.WRITE_LINESEPERATOR)

        # Add to compile.sh as return value.
        return "pdflatex -halt-on-error -shell-escape {n}.tex".format(
            n=doc_attributes["name"]
        )

    def _add_comment(self, wrapper, text):
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
