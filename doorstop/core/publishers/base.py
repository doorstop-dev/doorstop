# SPDX-License-Identifier: LGPL-3.0-only

"""Abstract interface to publishers."""

from abc import ABCMeta, abstractmethod

from doorstop import common, settings
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

    def setup(self, linkify, index, matrix):
        """Check and store linkfy, index and matrix settings."""
        if linkify is None:
            self.linkify = is_tree(self.object) and self.ext in [".html", ".md", ".tex"]
        if index is None:
            self.index = is_tree(self.object) and self.ext == ".html"
        if matrix is None:
            self.matrix = is_tree(self.object)

    def preparePublish(self):
        """Replace this with code that should be run _before_ a document or tree
        is published."""
        pass

    def publishAction(self, object, path):
        """Replace this with code that should be run _for each_ document
        _during_ publishing."""
        self.document = object
        self.documentPath = path

    def concludePublish(self):
        """Replace this with code that should be run _after_ a document or tree
        is published."""
        pass

    @abstractmethod
    def lines(self, obj, **kwargs):  # pragma: no cover (abstract method)
        """Yield lines for a report.

        :param obj: Item, list of Items, or Document to publish
        :param linkify: turn links into hyperlinks

        :return: iterator of lines of text

        """
        raise NotImplementedError

    @abstractmethod
    def index(
        self, directory, index=None, extensions=(".html",), tree=None
    ):  # pragma: no cover (abstract method)
        """Create an index of all files in a directory.

        :param directory: directory for index
        :param index: filename for index
        :param extensions: file extensions to include
        :param tree: optional tree to determine index structure

        """
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
    def format_links(
        self, items, linkify, to_html=False
    ):  # pragma: no cover (abstract method)
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

    def extract_prefix(self, document):
        """Return the document prefix."""
        if document:
            return document.prefix
        else:
            return None

    def extract_uid(self, item):
        """Return the item uid."""
        if item:
            return item.uid
        else:
            return None

    def format_level(self, level):
        """Convert a level to a string and keep zeros if not a top level."""
        text = str(level)
        if text.endswith(".0") and len(text) > 3:
            text = text[:-2]
        return text

    def get_line_generator(self):
        """Return the lines generator for the class."""
        return self.lines

    def setPath(self, path):
        """Set the export path of the tree and/or document."""
        self.path = path

    def getPath(self):
        """Get the export path of the tree and/or document."""
        return self.path

    def setDocumentPath(self, path):
        """Set the export path of the individual document."""
        self.documentPath = path

    def getDocumentPath(self):
        """Get the export path of the individual document."""
        return self.documentPath

    def processTemplates(self, template):
        """Retrieve the template and its path."""
        self.assetsPath, self.template = get_template(
            self.document, self.path, self.ext, template
        )

    def setAssetsPath(self, path):
        """Set the assets path of the individual document."""
        self.assetsPath = path

    def getAssetsPath(self):
        """Get the assets path of the individual document."""
        return self.assetsPath

    def setTemplate(self, template):
        """Set the template."""
        self.template = template

    def getTemplate(self):
        """Get the template."""
        return self.template

    def setIndex(self, index):
        """Set the index flag."""
        self.index = index

    def getIndex(self):
        """Get the index flag."""
        return self.index

    def setMatrix(self, matrix):
        """Set the matrix flag."""
        self.matrix = matrix

    def getMatrix(self):
        """Get the matrix flag."""
        return self.matrix

    def setLinkify(self, linkify):
        """Set the linkify flag."""
        self.linkify = linkify

    def getLinkify(self):
        """Get the linkify flag."""
        return self.linkify
