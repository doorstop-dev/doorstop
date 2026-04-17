# SPDX-License-Identifier: LGPL-3.0-only

"""Abstract interface to publishers."""

import os
from abc import ABCMeta, abstractmethod
from re import compile as re_compile
from re import match as re_match
from typing import Any, Dict, List

from markdown import markdown

from doorstop import common
from doorstop.core.template import get_template
from doorstop.core.types import is_tree

log = common.logger(__name__)


class BasePublisher(metaclass=ABCMeta):
    """Abstract base class for publishers.

    All functions marked as @abstractmethod must be defined by the publisher
    class.

    All other functions are standard and _can_ be overridden _if needed_.
    """

    def __init__(self, obj, ext):
        """Initialize publisher class."""
        self.object = obj
        self.ext = ext
        self.path = ""
        self.document = None
        self.documentPath = ""
        self.assetsPath = ""
        self.template = ""
        self.linkify = None
        self.index = None
        self.matrix = None
        # Define lists.
        self.list: Dict[str, Dict[str, Any]] = {}
        self.list["depth"] = {"itemize": 0, "enumerate": 0}
        self.list["indent"] = {"itemize": 0, "enumerate": 0}
        self.list["found"] = {"itemize": False, "enumerate": False}
        # Create regexps.
        self.list["regexp"] = {
            "itemize": re_compile(r"^\s*[\*+-]\s(.*)"),
            "enumerate": re_compile(r"^\s*\d+\.\s(.*)"),
        }
        self.list["sub"] = {
            "itemize": re_compile(r"^\s*[\*+-]\s"),
            "enumerate": re_compile(r"^\s*\d+\.\s"),
        }

    def setup(self, linkify, index, matrix):
        """Check and store linkfy, index and matrix settings."""
        if linkify is None:
            self.linkify = is_tree(self.object) and self.ext in [".html", ".md", ".tex"]
        else:
            self.linkify = linkify
        if index is None:
            self.index = is_tree(self.object) and self.ext == ".html"
        else:
            self.index = index
        if matrix is None:
            self.matrix = is_tree(self.object)
        else:
            self.matrix = matrix

    def preparePublish(self):
        """Prepare publish.

        Replace this with code that should be run _before_ a document or tree
        is published.
        """

    def publishAction(self, document, path):
        """Publish action.

        Replace this with code that should be run _for each_ document
        _during_ publishing.
        """
        self.document = document
        # If path does not end with self.ext, add it.
        if not path.endswith(self.ext):
            self.documentPath = os.path.join(path, document.prefix + self.ext)
        else:
            self.documentPath = path

    def concludePublish(self):
        """Conclude publish.

        Replace this with code that should be run _after_ a document or tree
        is published.
        """

    @abstractmethod
    def table_of_contents(
        self, linkify=None, obj=None
    ):  # pragma: no cover (abstract method)
        """Yield lines for a table of contents.

        :param linkify: turn links into hyperlinks
        :param obj: Item, list of Items, or Document to publish

        :return: iterator of lines of text

        """
        raise NotImplementedError

    @abstractmethod
    def lines(self, obj, **kwargs):  # pragma: no cover (abstract method)
        """Yield lines for a report.

        :param obj: Item, list of Items, or Document to publish
        :param linkify: turn links into hyperlinks

        :return: iterator of lines of text

        """
        raise NotImplementedError

    @abstractmethod
    def create_index(
        self, directory, index=None, extensions=(".html",), tree=None
    ):  # pragma: no cover (abstract method)
        """Create an index of all files in a directory.

        :param directory: directory for index
        :param index: filename for index
        :param extensions: file extensions to include
        :param tree: optional tree to determine index structure

        """
        raise NotImplementedError

    def create_matrix(self, directory):  # pragma: no cover (abstract method)
        """Create a traceability table."""
        raise NotImplementedError

    @abstractmethod
    def format_attr_list(self, item, linkify):  # pragma: no cover (abstract method)
        """Create an attribute list for a heading."""
        raise NotImplementedError

    @abstractmethod
    def format_ref(self, item):  # pragma: no cover (abstract method)
        """Format an external reference."""
        raise NotImplementedError

    @abstractmethod
    def format_references(self, item):  # pragma: no cover (abstract method)
        """Format an external reference."""
        raise NotImplementedError

    @abstractmethod
    def format_links(self, items, linkify):  # pragma: no cover (abstract method)
        """Format a list of linked items."""
        raise NotImplementedError

    @abstractmethod
    def format_item_link(
        self, item, linkify=True
    ):  # pragma: no cover (abstract method)
        """Format an item link."""
        raise NotImplementedError

    @abstractmethod
    def format_label_links(
        self, label, links, linkify
    ):  # pragma: no cover (abstract method)
        """Join a string of label and links with formatting."""
        raise NotImplementedError

    def get_line_generator(self):
        """Return the lines generator for the class."""
        return self.lines

    def setPath(self, path):
        """Set the export path of the tree and/or document."""
        self.path = path

    def getDocumentPath(self):
        """Get the export path of the individual document."""
        return self.documentPath

    def processTemplates(self, template):
        """Retrieve the template and its path."""
        self.assetsPath, self.template = get_template(
            self.object, self.path, self.ext, template
        )

    def getAssetsPath(self):
        """Get the assets path of the individual document."""
        return self.assetsPath

    def getTemplate(self):
        """Get the template."""
        return self.template

    def getIndex(self):
        """Get the index flag."""
        return self.index

    def getMatrix(self):
        """Get the matrix flag."""
        return self.matrix

    def getLinkify(self):
        """Get the linkify flag."""
        return self.linkify

    def _normalize_list_indentation(self, text):
        """Normalize list indentation based on relative hierarchy.

        Handles inconsistent indentation by tracking relative levels instead
        of absolute indent values. Converts to 4-space standard required by
        most Markdown processors.

        :param text: Markdown text with potentially inconsistent list indentation
        :return: Text with normalized 4-space indentation per level
        """
        lines = text.split("\n")
        list_items: List[Dict[str, int]] = []

        # Parse list structure
        for i, line in enumerate(lines):
            match = re_match(r"^(\s*)([-*]|\d+\.)\s+", line)
            if match:
                list_items.append(
                    {
                        "index": i,
                        "indent": len(match.group(1)),
                    }
                )

        if not list_items:
            return text

        # Split into separate list blocks (separated by non-list lines)
        list_blocks: List[List[Dict[str, int]]] = []
        current_block: List[Dict[str, int]] = []
        prev_index = -2

        for item in list_items:
            # If line is not directly after previous, start new block
            if item["index"] != prev_index + 1:
                if current_block:
                    list_blocks.append(current_block)
                current_block = [item]
            else:
                current_block.append(item)
            prev_index = item["index"]

        if current_block:
            list_blocks.append(current_block)

        # Process each block independently
        result = list(lines)

        for block in list_blocks:
            # Determine hierarchy levels using stack
            indent_stack: List[int] = []

            for item in block:
                indent = item["indent"]

                # Pop stack until we find a level less than current indent
                while indent_stack and indent_stack[-1] >= indent:
                    indent_stack.pop()

                item["level"] = len(indent_stack)
                indent_stack.append(indent)

            # Apply normalization: level * 4 spaces
            for item in block:
                new_indent = item["level"] * 4
                if item["indent"] != new_indent:
                    result[item["index"]] = (
                        " " * new_indent + result[item["index"]].lstrip()
                    )

        return "\n".join(result)

    def _fix_list_spacing(self, text):
        """Add blank lines around lists for proper markdown processing.

        Markdown requires blank lines before and after list blocks to
        properly recognize them as lists.

        :param text: Markdown text
        :return: Text with proper spacing around lists
        """
        list_pattern = r"^(\s*)([-*]|\d+\.)\s+"
        lines = text.split("\n")
        result: List[str] = []

        for i, line in enumerate(lines):
            is_list = re_match(list_pattern, line)
            prev_is_list = i > 0 and re_match(list_pattern, lines[i - 1])
            next_is_list = i < len(lines) - 1 and re_match(list_pattern, lines[i + 1])
            prev_is_blank = i > 0 and lines[i - 1].strip() == ""

            # Add blank line before first list item
            if is_list and not prev_is_list and not prev_is_blank and result:
                result.append("")

            result.append(line)

            # Add blank line after last list item
            if (
                is_list
                and not next_is_list
                and i < len(lines) - 1
                and lines[i + 1].strip()
            ):
                result.append("")

        return "\n".join(result)


def extract_prefix(document):
    """Return the document prefix."""
    return document.prefix


def extract_uid(item):
    """Return the item uid."""
    if item:
        return item.uid
    else:
        return None


def format_level(level):
    """Convert a level to a string and keep zeros if not a top level."""
    text = str(level)
    if text.endswith(".0") and len(text) > 3:
        text = text[:-2]
    return text


def get_document_attributes(obj, is_html=False, extensions=None):
    """Try to get attributes from document."""
    doc_attributes = {}
    doc_attributes["name"] = "doc-" + obj.prefix
    doc_attributes["title"] = "Test document for development of _Doorstop_"
    doc_attributes["ref"] = "-"
    doc_attributes["by"] = "-"
    doc_attributes["major"] = "-"
    doc_attributes["minor"] = ""
    doc_attributes["copyright"] = "Doorstop"
    try:
        attribute_defaults = obj.__getattribute__("_attribute_defaults")
    except AttributeError:
        attribute_defaults = None
    if attribute_defaults:
        if "doc" in attribute_defaults:
            if "name" in attribute_defaults["doc"]:
                # Name should only be set if it is not empty.
                if attribute_defaults["doc"]["name"] != "":
                    doc_attributes["name"] = attribute_defaults["doc"]["name"]
            if "title" in attribute_defaults["doc"]:
                doc_attributes["title"] = attribute_defaults["doc"]["title"]
            if "ref" in attribute_defaults["doc"]:
                doc_attributes["ref"] = attribute_defaults["doc"]["ref"]
            if "by" in attribute_defaults["doc"]:
                doc_attributes["by"] = attribute_defaults["doc"]["by"]
            if "major" in attribute_defaults["doc"]:
                doc_attributes["major"] = attribute_defaults["doc"]["major"]
            if "minor" in attribute_defaults["doc"]:
                doc_attributes["minor"] = attribute_defaults["doc"]["minor"]
            if "copyright" in attribute_defaults["doc"]:
                doc_attributes["copyright"] = attribute_defaults["doc"]["copyright"]
    # Check output format. If html we need go convert from markdown.
    if is_html:
        # Only convert title and copyright.
        doc_attributes["title"] = markdown(
            doc_attributes["title"], extensions=extensions
        )
        doc_attributes["copyright"] = markdown(
            doc_attributes["copyright"], extensions=extensions
        )

    return doc_attributes
