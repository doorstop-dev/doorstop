# SPDX-License-Identifier: LGPL-3.0-only

"""Abstract interface to publishers."""

from abc import ABCMeta, abstractmethod

from doorstop import common, settings

log = common.logger(__name__)


class BasePublisher(metaclass=ABCMeta):
    """Abstract base class for publishers."""

    def __init__(self):
        """Initialize publisher class."""
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
    def index(self, directory, index=INDEX, extensions=(".html",), tree=None): # pragma: no cover (abstract method)
        """Create an index of all files in a directory.

        :param directory: directory for index
        :param index: filename for index
        :param extensions: file extensions to include
        :param tree: optional tree to determine index structure

        """
        raise NotImplementedError


    @abstractmethod
    def format_attr_list(self,item, linkify): # pragma: no cover (abstract method)
        """Create an attribute list for a heading."""
        raise NotImplementedError

    def _format_text_ref(self,item):# pragma: no cover (abstract method)
        """Format an external reference in text."""
        raise NotImplementedError


    def extract_prefix(self,document):
        """Return the document prefix."""
        if document:
            return document.prefix
        else:
            return None


    def extract_uid(self,item):
        """Return the item uid."""
        if item:
            return item.uid
        else:
            return None

    def format_level(self,level):
        """Convert a level to a string and keep zeros if not a top level."""
        text = str(level)
        if text.endswith(".0") and len(text) > 3:
            text = text[:-2]
        return text
