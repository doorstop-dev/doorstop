# SPDX-License-Identifier: LGPL-3.0-only

"""Functions to publish documents and items."""

import os
import re
import tempfile

import bottle
import markdown
from bottle import template as bottle_template
from plantuml_markdown import PlantUMLMarkdownExtension

from doorstop import common, settings
from doorstop.core.publishers.base import (
    extract_prefix,
    extract_uid,
    format_level,
    get_document_attributes,
)
from doorstop.core.publishers.markdown import MarkdownPublisher
from doorstop.core.template import HTMLTEMPLATE, INDEX, MATRIX
from doorstop.core.types import is_item, iter_items

log = common.logger(__name__)


class HtmlPublisher(MarkdownPublisher):
    """HTML publisher."""

    def __init__(self, obj, ext):
        super().__init__(obj, ext)
        # Define lists.
        self.list["start"] = {"itemize": "<ul>", "enumerate": "<ol>"}
        self.list["end"] = {"itemize": "</ul>", "enumerate": "</ol>"}
        self.list["start_item"] = {"itemize": "<li>", "enumerate": "<li>"}
        self.list["end_item"] = {"itemize": "</li>", "enumerate": "</li>"}

    EXTENSIONS = (
        "markdown.extensions.extra",
        "markdown.extensions.sane_lists",
        PlantUMLMarkdownExtension(
            server="http://www.plantuml.com/plantuml",
            cachedir=tempfile.gettempdir(),
            format="svg",
            classes="class1,class2",
            title="UML",
            alt="UML Diagram",
        ),
    )

    def publishAction(self, document, path):
        """Publish action.

        Replace this with code that should be run _for each_ document
        _during_ publishing.
        """
        self.document = document
        # Check if path ends with .html
        if path.endswith(".html"):
            # Split of the filename and add 'documents/' to the path.
            documentPath = os.path.join(os.path.dirname(path), "documents")
        else:
            # Add 'documents/' to the path.
            documentPath = os.path.join(path, "documents")
        # Create the document directory if it does not exist.
        if not os.path.exists(documentPath):
            os.makedirs(documentPath)
        # Check if path ends with .html
        if path.endswith(".html"):
            self.documentPath = os.path.join(documentPath, os.path.basename(path))
        else:
            self.documentPath = os.path.join(documentPath, document.prefix + ".html")

    def create_index(self, directory, index=INDEX, extensions=(".html",), tree=None):
        """Create an HTML index of all files in a directory.

        :param directory: directory for index
        :param index: filename for index
        :param extensions: file extensions to include
        :param tree: optional tree to determine index structure

        """
        # Get paths for the index index
        filenames = []
        tmpPath = os.path.join(directory, "documents")
        if os.path.exists(tmpPath):
            for filename in os.listdir(tmpPath):
                if filename.endswith(extensions) and filename != INDEX:
                    filenames.append(os.path.join(filename))

        # Create the index
        if filenames:
            path = os.path.join(directory, index)
            log.info("creating an {}...".format(index))
            lines = self.lines_index(sorted(filenames), tree=tree)
            # Format according to the template.
            templatePath = os.path.abspath(
                os.path.join(self.assetsPath, "..", "..", "template", "views")
            )
            html = self.typesetTemplate(
                templatePath,
                "\n".join(lines),
                doc_attributes={
                    "name": "Index",
                    "ref": "-",
                    "title": "Doorstop index",
                    "by": "-",
                    "major": "-",
                    "minor": "",
                },
            )
            common.write_text(html, path)
        else:
            log.warning("no files for {}".format(index))

    def lines_index(self, filenames, tree=None):
        """Yield lines of HTML for index.html.

        :param filesnames: list of filenames to add to the index
        :param tree: optional tree to determine index structure

        """
        # Tree structure
        text = tree.draw(html_links=True) if tree else None
        yield ""
        yield "<h3>Tree Structure:</h3>"
        yield "<pre><code>" + text + "</pre></code>"
        yield ""
        yield "<hr>"
        # Additional files
        yield ""
        yield "<h3>Published Documents:</h3>"
        yield "<p>"
        yield "<ul>"
        for filename in filenames:
            name = os.path.splitext(filename)[0]
            yield '<li> <a href="documents/{f}">{n}</a> </li>'.format(
                f=filename, n=name
            )
        yield "</ul>"
        yield "</p>"

    def create_matrix(self, directory):
        """Create a traceability matrix for all the items. This will create a .csv and .html file.

        :param directory: directory for matrix

        """
        ############################################################
        # Create the csv matrix
        ############################################################
        # Get path and format extension
        filename = MATRIX
        path = os.path.join(directory, filename)

        # Create the matrix
        log.info("creating an {}...".format(filename))
        content = self._matrix_content()
        common.write_csv(content, path)

        ############################################################
        # Create the HTML matrix
        ############################################################
        filename = MATRIX.replace(".csv", ".html")
        path = os.path.join(directory, filename)
        log.info("creating an {}...".format(filename))
        lines = self.lines_matrix()
        # Format according to the template.
        if self.template == "":
            self.template = HTMLTEMPLATE
        templatePath = os.path.abspath(
            os.path.join(self.assetsPath, "..", "..", "template", "views")
        )
        html = self.typesetTemplate(
            templatePath,
            "\n".join(lines),
            doc_attributes={
                "name": "Traceability",
                "ref": "-",
                "title": "Doorstop traceability matrix",
                "by": "-",
                "major": "-",
                "minor": "",
            },
        )
        common.write_text(html, path)

    def typesetTemplate(
        self,
        templatePath,
        body,
        doc_attributes,
        toc=None,
        parent=None,
        document=None,
        is_doc=False,
        has_index=False,
        has_matrix=False,
    ):
        """Typeset the template."""
        bottle.TEMPLATE_PATH.insert(0, templatePath)
        if "baseurl" not in bottle.SimpleTemplate.defaults:
            bottle.SimpleTemplate.defaults["baseurl"] = ""
        html = bottle_template(
            self.template,
            body=body,
            toc=toc,
            parent=parent,
            document=document,
            doc_attributes=doc_attributes,
            is_doc=is_doc,
            has_index=has_index,
            has_matrix=has_matrix,
        )
        return html

    def _matrix_content(self):
        """Yield rows of content for the traceability matrix in csv format."""
        yield tuple(map(extract_prefix, self.object.documents))
        for row in self.object.get_traceability():
            yield tuple(map(extract_uid, row))

    def lines_matrix(self):
        """Traceability table for html output."""
        yield '<table class="table">'
        # header
        yield "<thead>"
        yield "<tr>"
        for document in self.object:  # pylint: disable=not-an-iterable
            link = '<a href="documents/{p}.html">{p}</a>'.format(p=document.prefix)
            yield ('  <th scope="col">{link}</th>'.format(link=link))
        yield "</tr>"
        yield "</thead>"
        # data
        yield "<tbody>"
        for index, row in enumerate(self.object.get_traceability()):
            if index % 2:
                yield '<tr class="alt">'
            else:
                yield "<tr>"
            for item in row:
                if item is None:
                    link = ""
                else:
                    link = self.format_item_link(item, is_doc=False)
                yield '  <td scope="row">{}</td>'.format(link)
            yield "</tr>"
        yield "</tbody>"
        yield "</table>"

    def format_item_link(self, item, linkify=True, is_doc=True):
        """Format an item link in HTML."""
        if linkify and is_item(item):
            if is_doc:
                tmpRef = ""
            else:
                tmpRef = "documents/"
            if item.header:
                link = '<a href="{r}{p}.html#{u}">{u} {h}</a>'.format(
                    u=item.uid, h=item.header, p=item.document.prefix, r=tmpRef
                )
            else:
                link = '<a href="{r}{p}.html#{u}">{u}</a>'.format(
                    u=item.uid, p=item.document.prefix, r=tmpRef
                )
            return link
        else:
            return str(item.uid)  # if not `Item`, assume this is an `UnknownItem`

    def lines(self, obj, **kwargs):
        """Yield lines for an HTML report.

        :param obj: Item, list of Items, or Document to publish
        :param linkify: turn links into hyperlinks

        :return: iterator of lines of text

        """
        linkify = kwargs.get("linkify", False)
        toc = kwargs.get("toc", False)

        # Determine if a full HTML document should be generated
        try:
            iter(obj)
        except TypeError:
            document = False
        else:
            document = True

        # Check for defined document attributes.
        if document:
            doc_attributes = get_document_attributes(
                obj, is_html=True, extensions=self.EXTENSIONS
            )

        # Generate HTML
        text = "\n".join(self._lines_markdown(obj, linkify=linkify, to_html=True))
        # We need to handle escaped back-ticks before we pass the text to markdown.
        text = text.replace("\\`", "##!!TEMPINLINE!!##")
        body_to_check = markdown.markdown(text, extensions=self.EXTENSIONS).splitlines()
        block = []
        # Check for nested lists since they are not supported by the markdown_sane_lists plugin.
        for i, line in enumerate(body_to_check):
            # Replace the temporary inline code blocks with the escaped back-ticks. If there are
            # multiple back-ticks in a row, we need group them in a single <code> block.
            line = re.sub(
                r"(##!!TEMPINLINE!!##)+",
                lambda m: "<code>" + "&#96;" * int(len(m.group()) / 18) + "</code>",
                line,
            )
            # Check if we are at the end of the body.
            if i == len(body_to_check) - 1:
                next_line = ""
            else:
                next_line = body_to_check[i + 1]
            (_, processed_block, processed_line) = self.process_lists(line, next_line)
            if processed_block != "":
                block.append(processed_block)
            block.append(processed_line)
        body = "\n".join(block)

        if toc:
            toc_html = self.table_of_contents(True, obj)
        else:
            toc_html = ""

        if document:
            if self.template == "":
                self.template = HTMLTEMPLATE
            templatePath = os.path.abspath(
                os.path.join(self.assetsPath, "..", "..", "template", "views")
            )
            html = self.typesetTemplate(
                templatePath,
                body,
                doc_attributes,
                toc=toc_html,
                parent=obj.parent,
                document=obj,
                is_doc=True,
                has_index=self.getIndex(),
                has_matrix=self.getMatrix(),
            )
            yield "\n".join(html.split(os.linesep))
        else:
            yield body

    def table_of_contents(self, linkify=None, obj=None):
        """Generate a table of contents. Returns a nested list of items to be rendered with the template."""
        toc = []
        toc.append({"depth": 0, "text": "Table of Contents", "uid": "toc"})
        toc_doc = obj

        for item in iter_items(toc_doc):
            # Check if item has the attribute heading.
            if item.heading:
                lines = item.text.splitlines()
                heading = lines[0] if lines else ""
            elif item.header:
                heading = "{h}".format(h=item.header)
            else:
                heading = item.uid
            if settings.PUBLISH_HEADING_LEVELS:
                level = format_level(item.level)
                lbl = "{lev} {h}".format(lev=level, h=heading)
            else:
                lbl = heading
            if linkify:
                uid = item.uid
            else:
                uid = ""
            toc.append({"depth": item.depth, "text": lbl, "uid": uid})
        return toc
