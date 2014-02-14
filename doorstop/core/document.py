"""
Representation of a collection of Doorstop items.
"""

import os
import logging

import yaml

from doorstop.core.base import auto_load, auto_save, BaseFileObject
from doorstop.core.item import Item, split_id
from doorstop import common
from doorstop.common import DoorstopError, DoorstopWarning, DoorstopInfo
from doorstop import settings


class Document(BaseFileObject):
    """Represents a document directory containing an outline of items."""

    CONFIG = '.doorstop.yml'
    SKIP = '.doorstop.skip'  # indicates this document should be skipped

    DEFAULT_PREFIX = 'REQ'
    DEFAULT_SEP = ''
    DEFAULT_DIGITS = 3

    DEFAULT_PARENT = None  # a parent of None indicates this is the root

    def __init__(self, path, root=os.getcwd(),
                 # TODO: remove these to match Item
                 _prefix=None, _sep=None, _digits=None, _parent=None):
        """Load a document from an exiting directory.

        Internally, this constructor is also used to initialize new
        documents by providing default properties.

        @param path: path to document directory
        @param root: path to root of project
        """
        super().__init__()
        # Ensure the directory is valid
        if not os.path.isfile(os.path.join(path, Document.CONFIG)):
            relpath = os.path.relpath(path, root)
            msg = "no {} in {}".format(Document.CONFIG, relpath)
            raise DoorstopError(msg)
        # Initialize the document
        self.path = path
        self.root = root
        self._items = []
        self._itered = False
        # Set default values
        self._data['prefix'] = _prefix or Document.DEFAULT_PREFIX
        self._data['sep'] = _sep or Document.DEFAULT_SEP
        self._data['digits'] = _digits or Document.DEFAULT_DIGITS
        self._data['parent'] = _parent or Document.DEFAULT_PARENT

    def __repr__(self):
        return "Document({})".format(repr(self.path))

    def __str__(self):
        if common.VERBOSITY < common.STR_VERBOSITY:
            return self.prefix
        else:
            return self.prefix_relpath

    def __iter__(self):
        yield from self._iter()

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.path == other.path

    def __ne__(self, other):
        return not self == other

    @staticmethod
    def new(path, root, prefix, sep=None, digits=None, parent=None, auto=None):  # pylint: disable=R0913
        """Create a new document.

        @param path: path to directory for the new document
        @param root: path to root of the project
        @param prefix: prefix for the new document
        @param sep: separator between prefix and numbers
        @param digits: number of digits for the new document
        @param parent: parent ID for the new document
        @param auto: enables automatic save

        @raise DoorstopError: if the document already exists
        """
        # TODO: raise a specific exception
        assert not sep or sep in settings.SEP_CHARS
        config = os.path.join(path, Document.CONFIG)
        # Check for an existing document
        if os.path.exists(config):
            raise DoorstopError("document already exists: {}".format(path))
        # Create the document directory
        Document._new(config, name='document')
        # Initialize the document
        document = Document(path, root=root,
                            _prefix=prefix, _sep=sep, _digits=digits,
                            _parent=parent)
        if auto or (auto is None and Document.auto):
            document.save()
        # Return the document
        return document

    def load(self, reload=False):
        """Load the document's properties from its file."""
        if self._loaded and not reload:
            return
        logging.debug("loading {}...".format(repr(self)))
        # Read text from file
        text = self._read(self.config)
        # Parse YAML data from text
        data = self._parse(text, self.config)
        # Store parsed data
        sets = data.get('settings', {})
        for key, value in sets.items():
            if key == 'prefix':
                self._data['prefix'] = value.strip()
            elif key == 'sep':
                self._data['sep'] = value.strip()
            elif key == 'parent':
                self._data['parent'] = value.strip()
            elif key == 'digits':
                self._data['digits'] = int(value)
        # Set meta attributes
        self._loaded = True
        if reload:
            self._itered = False  # reload the items

    def save(self):
        """Save the document's properties to its file."""
        logging.debug("saving {}...".format(repr(self)))
        # Format the data items
        data = {}
        sets = {}
        for key, value in self._data.items():
            if key == 'prefix':
                sets['prefix'] = value
            elif key == 'sep':
                sets['sep'] = value
            elif key == 'digits':
                sets['digits'] = value
            elif key == 'parent':
                if value:
                    sets['parent'] = value
            else:
                data[key] = value
        data['settings'] = sets
        # Dump the data to YAML
        text = yaml.dump(data, default_flow_style=False)
        # Save the YAML to file
        self._write(text, self.config)
        # Set meta attributes
        self._loaded = False
        self.auto = True

    def _iter(self, reload=False):
        """Yield the document's items."""
        if self._itered and not reload:
            logging.debug("iterating through previously loaded items...")
            yield from self._items
            return
        logging.debug("iterating through items in {}...".format(self.path))
        # Reload the document's item
        self._items = []
        for dirpath, dirnames, filenames in os.walk(self.path):
            for dirname in list(dirnames):
                path = os.path.join(dirpath, dirname, Document.CONFIG)
                if os.path.exists(path):
                    path = os.path.dirname(path)
                    msg = "found embedded document: {}".format(path)
                    logging.debug(msg)
                    dirnames.remove(dirname)
            for filename in filenames:
                path = os.path.join(dirpath, filename)
                try:
                    item = Item(path)
                except DoorstopError:
                    pass  # skip non-item files
                else:
                    self._items.append(item)
                    yield item
        # Set meta attributes
        self._itered = True

    # properties #############################################################

    @property
    def config(self):
        """Get the path to the document's file."""
        return os.path.join(self.path, Document.CONFIG)

    @property
    @auto_load
    def prefix(self):
        """Get the document's prefix."""
        return self._data['prefix']

    @prefix.setter
    @auto_save
    def prefix(self, value):
        """Set the document's prefix."""
        self._data['prefix'] = value.strip()
        # TODO: should the new prefix be applied to all items?

    @property
    def relpath(self):
        """Get the document's relative path string."""
        relpath = os.path.relpath(self.path, self.root)
        return "@{}{}".format(os.sep, relpath)

    # TODO: think of a better name for this property
    @property
    @auto_load
    def prefix_relpath(self):
        """Get the document's prefix + relative path string."""
        return "{} ({})".format(self.prefix, self.relpath)

    @property
    @auto_load
    def sep(self):
        """Get the prefix-number separator to use for new item IDs."""
        return self._data['sep']

    @sep.setter
    @auto_save
    def sep(self, value):
        """Set the prefix-number separator to use for new item IDs."""
        # TODO: raise a specific exception
        assert not value or value in settings.SEP_CHARS
        self._data['sep'] = value.strip()
        # TODO: should the new separator be applied to all items?

    @property
    @auto_load
    def digits(self):
        """Get the number of digits to use for new item IDs."""
        return self._data['digits']

    @digits.setter
    @auto_save
    def digits(self, value):
        """Set the number of digits to use for new item IDs."""
        self._data['digits'] = value
        # TODO: should the new digits be applied to all items?

    @property
    @auto_load
    def parent(self):
        """Get the document's parent document prefix."""
        return self._data['parent']

    @parent.setter
    @auto_save
    def parent(self, value):
        """Set the document's parent document prefix."""
        self._data['parent'] = value.strip()

    @property
    def items(self):
        """Get an ordered list of items in the document."""
        return sorted(self._iter())

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

    @property
    def skip(self):
        """Indicates the document should be skipped."""
        return os.path.isfile(os.path.join(self.path, Document.SKIP))

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
        item = Item.new(self.path, self.root,
                        self.prefix, self.sep, self.digits,
                        number, level=level)
        self._items.append(item)
        return item

    def remove(self, identifier):
        """Remove an item by its ID.

        @param identifier: item ID

        @return: removed Item

        @raise DoorstopError: if the item cannot be found
        """
        item = self.find_item(identifier)
        item.delete()
        self._items.remove(item)
        return item

    def find_item(self, identifier, _kind=''):
        """Return an item by its ID.

        @param identifier: item ID

        @return: matching Item

        @raise DoorstopError: if the item cannot be found
        """
        # Search using the exact ID
        for item in self:
            if item.id.lower() == identifier.lower():
                return item
        logging.debug("no exactly matching ID: {}".format(identifier))

        # Search using the prefix and number
        prefix, number = split_id(identifier)
        if self.prefix.lower() == prefix.lower():
            for item in self:
                if item.number == number:
                    return item
            msg = "no matching{} number: {}".format(_kind, number)
            logging.debug(msg)

        raise DoorstopError("no matching{} ID: {}".format(_kind, identifier))

    def valid(self, tree=None):
        """Check the document (and its items) for validity.

        @param tree: Tree containing the document

        @return: indication that document is valid
        """
        valid = True
        # Display all issues
        for issue in self.issues(tree=tree):
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

    def issues(self, tree=None):
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
            for issue in item.issues(document=self, tree=tree):
                # Prepend the item's ID
                yield type(issue)("{}: {}".format(item.id, issue))
