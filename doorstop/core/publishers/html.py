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
from doorstop.common import DoorstopError
from doorstop.core.publishers.base import extract_prefix, extract_uid
from doorstop.core.publishers.markdown import MarkdownPublisher
from doorstop.core.template import CSS, HTMLTEMPLATE, INDEX, MATRIX
from doorstop.core.types import is_item

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

    def create_index(self, directory, index=INDEX, extensions=(".html",), tree=None):
        """Create an HTML index of all files in a directory.

        :param directory: directory for index
        :param index: filename for index
        :param extensions: file extensions to include
        :param tree: optional tree to determine index structure

        """
        # Get paths for the index index
        filenames = []
        for filename in os.listdir(directory):
            if filename.endswith(extensions) and filename != INDEX:
                filenames.append(os.path.join(filename))

        # Create the index
        if filenames:
            path = os.path.join(directory, index)
            log.info("creating an {}...".format(index))
            lines = self._lines_index(sorted(filenames), tree=tree)
            common.write_lines(lines, path, end=settings.WRITE_LINESEPERATOR)
        else:
            log.warning("no files for {}".format(index))

    def _lines_index(self, filenames, charset="UTF-8", tree=None):
        """Yield lines of HTML for index.html.

        :param filesnames: list of filenames to add to the index
        :param charset: character encoding for output
        :param tree: optional tree to determine index structure

        """
        yield "<!DOCTYPE html>"
        yield "<head>"
        yield (
            '<meta http-equiv="content-type" content="text/html; '
            'charset={charset}">'.format(charset=charset)
        )
        yield '<style type="text/css">'
        yield from _lines_css()
        yield "</style>"
        yield "</head>"
        yield "<body>"
        # Tree structure
        text = tree.draw() if tree else None
        if text:
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
            yield '<li> <a href="{f}">{n}</a> </li>'.format(f=filename, n=name)
        yield "</ul>"
        yield "</p>"
        # Traceability table
        documents = tree.documents if tree else None
        if documents:
            yield ""
            yield "<hr>"
            yield ""
            # table
            yield "<h3>Item Traceability:</h3>"
            yield "<p>"
            yield "<table>"
            # header
            for document in documents:  # pylint: disable=not-an-iterable
                yield '<col width="100">'
            yield "<tr>"
            for document in documents:  # pylint: disable=not-an-iterable
                link = '<a href="{p}.html">{p}</a>'.format(p=document.prefix)
                yield (
                    '  <th height="25" align="center"> {link} </th>'.format(link=link)
                )
            yield "</tr>"
            # data
            for index, row in enumerate(tree.get_traceability()):
                if index % 2:
                    yield '<tr class="alt">'
                else:
                    yield "<tr>"
                for item in row:
                    if item is None:
                        link = ""
                    else:
                        link = self.format_item_link(item)
                    yield '  <td height="25" align="center"> {} </td>'.format(link)
                yield "</tr>"
            yield "</table>"
            yield "</p>"
        yield ""
        yield "</body>"
        yield "</html>"

    def create_matrix(self, directory):
        """Create a traceability matrix for all the items.

        :param directory: directory for matrix

        """
        # Get path and format extension
        filename = MATRIX
        path = os.path.join(directory, filename)
        # ext = self.ext or os.path.splitext(path)[-1] or ".csv"

        # Create the matrix
        log.info("creating an {}...".format(filename))
        content = self._matrix_content()
        common.write_csv(content, path)

    def _matrix_content(self):
        """Yield rows of content for the traceability matrix."""
        yield tuple(map(extract_prefix, self.object.documents))
        for row in self.object.get_traceability():
            yield tuple(map(extract_uid, row))

    def format_item_link(self, item, linkify=True):
        """Format an item link in HTML."""
        if linkify and is_item(item):
            if item.header:
                link = '<a href="{p}.html#{u}">{u} {h}</a>'.format(
                    u=item.uid, h=item.header, p=item.document.prefix
                )
            else:
                link = '<a href="{p}.html#{u}">{u}</a>'.format(
                    u=item.uid, p=item.document.prefix
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

            # line = line.replace("##!!TEMPINLINE!!##", "<code>&#96;</code>")
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
            toc_md = self.table_of_contents(True, obj)
            toc_html = markdown.markdown(toc_md, extensions=self.EXTENSIONS)
        else:
            toc_html = ""

        if document:
            if self.template == "":
                self.template = HTMLTEMPLATE
            try:
                bottle.TEMPLATE_PATH.insert(
                    0, os.path.join(os.path.dirname(__file__), "..", "..", "views")
                )
                if "baseurl" not in bottle.SimpleTemplate.defaults:
                    bottle.SimpleTemplate.defaults["baseurl"] = ""
                html = bottle_template(
                    self.template,
                    body=body,
                    toc=toc_html,
                    parent=obj.parent,
                    document=obj,
                )
            except Exception:
                raise DoorstopError(
                    "Problem parsing the template {}".format(self.template)
                )
            yield "\n".join(html.split(os.linesep))
        else:
            yield body


def _lines_css():
    """Yield lines of CSS to embedded in HTML."""
    yield ""
    for line in common.read_lines(CSS):
        yield line.rstrip()
    yield ""
