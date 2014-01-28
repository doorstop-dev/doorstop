"""
Representation of a collection of Doorstop items.
"""

import os
import logging

import yaml

from doorstop.core.item import Item, split_id
from doorstop import common
from doorstop.common import DoorstopError, DoorstopWarning, DoorstopInfo
from doorstop import settings


class Document(object):
    """Represents a document directory containing an outline of items."""

    CONFIG = '.doorstop.yml'
    SKIP = '.doorstop.skip'  # indicates this document should be skipped
    DEFAULT_PREFIX = 'REQ'
    DEFAULT_SEP = ''
    DEFAULT_PARENT = None  # which indicates this is the root document
    DEFAULT_DIGITS = 3

    def __init__(self, path, root=os.getcwd(),
                 _prefix=None, _sep=None, _parent=None, _digits=None):
        """Load a document from an exiting directory.

        Internally, this constructor is also used to initialize new
        documents by providing default properties.

        @param path: path to document directory
        @param root: path to root of project
        """
        # Ensure the directory is valid
        if not os.path.isfile(os.path.join(path, Document.CONFIG)):
            relpath = os.path.relpath(path, root)
            msg = "no {} in {}".format(Document.CONFIG, relpath)
            raise DoorstopError(msg)
        # Initialize Document
        self.path = path
        self.root = root
        self.prefix = _prefix or Document.DEFAULT_PREFIX
        self.sep = _sep or Document.DEFAULT_SEP
        self.parent = _parent or Document.DEFAULT_PARENT
        self.digits = _digits or Document.DEFAULT_DIGITS
        self.load()
        self.save()
        # Mark if skippable
        self.skip = os.path.isfile(os.path.join(self.path, Document.SKIP))

    def __repr__(self):
        return "Document({})".format(repr(self.path))

    def __str__(self):
        if common.VERBOSITY < common.STR_VERBOSITY:
            return self.prefix
        else:
            return self.prefix_relpath

    def __iter__(self):
        for filename in os.listdir(self.path):
            path = os.path.join(self.path, filename)
            try:
                yield Item(path)
            except DoorstopError:
                pass  # skip non-item files

    def __eq__(self, other):
        return isinstance(other, Document) and self.path == other.path

    def __ne__(self, other):
        return not self == other

    @staticmethod
    def new(path, root, prefix, sep=None, parent=None, digits=None):  # pylint: disable=R0913
        """Create a new document.

        @param path: path to directory for the new document
        @param root: path to root of the project
        @param prefix: prefix for the new document
        @param sep: separator between prefix and numbers
        @param parent: parent ID for the new document
        @param digits: number of digits for the new document

        @raise DoorstopError: if the document already exists
        """
        # TODO: remove after testing or raise a specific exception
        assert sep is None or sep in settings.SEP_CHARS
        config = os.path.join(path, Document.CONFIG)
        # Check for an existing document
        if os.path.exists(config):
            raise DoorstopError("document already exists: {}".format(path))
        # Create the document directory
        Document._new(path, config)
        # Return the new document
        return Document(path, root=root, _prefix=prefix, _sep=sep,
                        _parent=parent, _digits=digits)

    @staticmethod
    def _new(path, config):  # pragma: no cover, integration test
        """Create a new document directory.

        @param path: path to new document directory
        @param config: path to new document config file
        """
        if not os.path.exists(path):
            os.makedirs(path)
        with open(config, 'w'):
            pass  # just touch the file

    def load(self):
        """Load the document's properties from its file."""
        logging.debug("loading {}...".format(repr(self)))
        text = self._read()
        data = yaml.load(text)
        if data:
            sets = data.get('settings', {})
            if sets:
                self.prefix = sets.get('prefix', self.prefix)
                self.sep = sets.get('sep', self.sep)
                self.parent = sets.get('parent', self.parent)
                self.digits = sets.get('digits', self.digits)

    def _read(self):  # pragma: no cover, integration test
        """Read text from the document's file."""
        path = self.config
        if not os.path.exists(path):
            logging.debug("document does not exist yet: {}".format(path))
            return ""
        with open(path, 'rb') as infile:
            return infile.read().decode('UTF-8')

    def save(self):
        """Save the document's properties to its file."""
        logging.debug("saving {}...".format(repr(self)))
        sets = {'prefix': self.prefix,
                'sep': self.sep,
                'digits': self.digits}
        if self.parent:
            sets['parent'] = self.parent
        data = {'settings': sets}
        text = yaml.dump(data, default_flow_style=False)
        self._write(text)

    def _write(self, text):  # pragma: no cover, integration test
        """Write text to the document's file."""
        path = self.config
        with open(path, 'wb') as outfile:
            outfile.write(bytes(text, 'UTF-8'))

    # attributes #############################################################

    @property
    def relpath(self):
        """Get the document's relative path string."""
        relpath = os.path.relpath(self.path, self.root)
        return "@{}{}".format(os.sep, relpath)

    # TODO: think of a better name for this property
    @property
    def prefix_relpath(self):
        """Get the document's prefix + relative path string."""
        return "{} ({})".format(self.prefix, self.relpath)

    @property
    def config(self):
        """Get the path to the document's file."""
        return os.path.join(self.path, Document.CONFIG)

    @property
    def items(self):
        """Get an ordered list of items in the document."""
        return sorted(item for item in self)

    @property
    def depth(self):
        """Return the maximum item level depth."""
        return max(item.depth for item in self)

    @property
    def next(self):
        """Return the next item number in the document."""
        try:
            return max(item.number for item in self) + 1
        except ValueError:
            return 1

    # actions ################################################################

    def add(self):
        """Create a new item for the document and return it."""
        number = self.next
        logging.debug("next number: {}".format(number))
        try:
            last = self.items[-1]
        except IndexError:
            level = None
        else:
            level = last.level[:-1] + (last.level[-1] + 1,)
        logging.debug("next level: {}".format(level))
        return Item.new(self.path, self.root, self.prefix, self.sep, number,
                        self.digits, level)

    def find_item(self, identifier, _kind=''):
        """Return an item from its ID.

        @param identifier: item ID

        @return: matching Item

        @raise DoorstopError: if the item cannot be found
        """
        # Search using the prefix and number
        prefix, number = split_id(identifier)
        if self.prefix.lower() == prefix.lower():
            for item in self:
                if item.number == number:
                    return item
            msg = "no matching{} number: {}".format(_kind, number)
            logging.debug(msg)

        # Fall back to a search using the exact ID
        else:
            for item in self:
                if item.id.lower() == identifier.lower():
                    return item

        raise DoorstopError("no matching{} ID: {}".format(_kind, identifier))

    def valid(self, tree=None):
        """Check the document (and its items) for validity.

        @param tree: Tree containing the document

        @return: indication that document is valid
        """
        valid = True
        # Display all issues
        for issue in self.iter_issues(tree=tree):
            if isinstance(issue, DoorstopInfo):
                logging.info(issue)
            elif isinstance(issue, DoorstopWarning):
                logging.warning(issue)
            else:
                assert isinstance(issue, DoorstopError)
                logging.error(issue)
                valid = False
        # Return the result
        return valid

    def iter_issues(self, tree=None):
        """Yield all the document's issues.

        @param tree: Tree containing the document

        @return: generator of DoorstopError, DoorstopWarning, DoorstopInfo
        """
        logging.info("checking document {}...".format(self))
        items = list(self)
        # Check for items
        if not items:
            yield DoorstopWarning("no items")
        # Check each item
        for item in items:
            for issue in item.iter_issues(document=self, tree=tree):
                # Prepend the item's ID
                yield type(issue)("{}: {}".format(item.id, issue))
