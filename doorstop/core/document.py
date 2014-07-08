"""Representation of a collection of items."""

import os
from itertools import chain
from collections import OrderedDict
import logging

from doorstop import common
from doorstop.common import DoorstopError, DoorstopWarning
from doorstop.core.base import BaseValidatable
from doorstop.core.base import clear_document_cache, clear_item_cache
from doorstop.core.base import auto_load, auto_save, BaseFileObject
from doorstop.core.types import Prefix, ID, Level
from doorstop.core.item import Item
from doorstop import settings


class Document(BaseValidatable, BaseFileObject):  # pylint: disable=R0902,R0904

    """Represents a document directory containing an outline of items."""

    CONFIG = '.doorstop.yml'
    SKIP = '.doorstop.skip'  # indicates this document should be skipped

    DEFAULT_PREFIX = Prefix('REQ')
    DEFAULT_SEP = ''
    DEFAULT_DIGITS = 3

    def __init__(self, path, root=os.getcwd(), **kwargs):
        """Initialize a document from an exiting directory.

        :param path: path to document directory
        :param root: path to root of project

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
        self.tree = kwargs.get('tree')
        self.auto = kwargs.get('auto', Document.auto)
        # Set default values
        self._data['prefix'] = Document.DEFAULT_PREFIX
        self._data['sep'] = Document.DEFAULT_SEP
        self._data['digits'] = Document.DEFAULT_DIGITS
        self._data['parent'] = None  # the root document does not have a parent
        self._items = []
        self._itered = False

    def __repr__(self):
        return "Document('{}')".format(self.path)

    def __str__(self):
        if common.VERBOSITY < common.STR_VERBOSITY:
            return self.prefix
        else:
            return "{} ({})".format(self.prefix, self.relpath)

    def __iter__(self):
        yield from self._iter()

    def __len__(self):
        return len(list(self._iter()))

    def __bool__(self):  # override `__len__` behavior, pylint: disable=R0201
        return True

    @staticmethod
    def new(tree, path, root, prefix, sep=None, digits=None, parent=None, auto=None):  # pylint: disable=R0913,C0301
        """Internal method to create a new document.

        :param tree: reference to tree that contains this document

        :param path: path to directory for the new document
        :param root: path to root of the project
        :param prefix: prefix for the new document

        :param sep: separator between prefix and numbers
        :param digits: number of digits for the new document
        :param parent: parent ID for the new document
        :param auto: automatically save the document

        :raises: :class:`~doorstop.common.DoorstopError` if the document
            already exists

        :return: new :class:`~doorstop.core.document.Document`

        """
        # TODO: raise a specific exception for invalid separator characters?
        assert not sep or sep in settings.SEP_CHARS
        config = os.path.join(path, Document.CONFIG)
        # Check for an existing document
        if os.path.exists(config):
            raise DoorstopError("document already exists: {}".format(path))
        # Create the document directory
        Document._new(config, name='document')
        # Initialize the document
        document = Document(path, root=root, tree=tree, auto=False)
        document.prefix = prefix if prefix is not None else document.prefix
        document.sep = sep if sep is not None else document.sep
        document.digits = digits if digits is not None else document.digits
        document.parent = parent if parent is not None else document.parent
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
        data = self._load(text, self.config)
        # Store parsed data
        sets = data.get('settings', {})
        for key, value in sets.items():
            if key == 'prefix':
                self._data['prefix'] = Prefix(value)
            elif key == 'sep':
                self._data['sep'] = value.strip()
            elif key == 'parent':
                self._data['parent'] = value.strip()
            elif key == 'digits':
                self._data['digits'] = int(value)
        # Set meta attributes
        self._loaded = True
        if reload:
            list(self._iter(reload=reload))

    def save(self):
        """Save the document's properties to its file."""
        logging.debug("saving {}...".format(repr(self)))
        # Format the data items
        data = {}
        sets = {}
        for key, value in self._data.items():
            if key == 'prefix':
                sets['prefix'] = str(value)
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
        text = self._dump(data)
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
                    item = Item(path, root=self.root,
                                document=self, tree=self.tree)
                except DoorstopError:
                    pass  # skip non-item files
                else:
                    self._items.append(item)
        # Set meta attributes
        self._itered = True
        # Yield items
        yield from self._items

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
    @auto_load
    def prefix(self, value):
        """Set the document's prefix."""
        self._data['prefix'] = Prefix(value)
        # TODO: should the new prefix be applied to all items?

    @property
    @auto_load
    def sep(self):
        """Get the prefix-number separator to use for new item IDs."""
        return self._data['sep']

    @sep.setter
    @auto_save
    @auto_load
    def sep(self, value):
        """Set the prefix-number separator to use for new item IDs."""
        # TODO: raise a specific exception for invalid separator characters?
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
    @auto_load
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
    @auto_load
    def parent(self, value):
        """Set the document's parent document prefix."""
        self._data['parent'] = str(value) if value else ""

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
        """Indicate the document should be skipped."""
        return os.path.isfile(os.path.join(self.path, Document.SKIP))

    # actions ################################################################

    @clear_item_cache
    def add_item(self, number=None, level=None, reorder=True):
        """Create a new item for the document and return it.

        :param number: desired item number
        :param level: desired item level
        :param reorder: update levels of document items

        :return: added :class:`~doorstop.core.item.Item`

        """
        number = number or self.next
        logging.debug("next number: {}".format(number))
        try:
            last = self.items[-1]
        except IndexError:
            nlevel = level
        else:
            nlevel = level or last.level + 1
        logging.debug("next level: {}".format(nlevel))
        identifier = ID(self.prefix, self.sep, number, self.digits)
        item = Item.new(self.tree, self,
                        self.path, self.root, identifier,
                        level=nlevel)
        self._items.append(item)
        if level and reorder:
            self.reorder(keep=item)
        return item

    @clear_item_cache
    def remove_item(self, value, reorder=True):
        """Remove an item by its ID.

        :param value: item or ID
        :param reorder: update levels of document items

        :raises: :class:`~doorstop.common.DoorstopError` if the item
            cannot be found

        :return: removed :class:`~doorstop.core.item.Item`

        """
        identifier = ID(value)
        item = self.find_item(identifier)
        item.delete()
        if reorder:
            self.reorder()
        return item

    def reorder(self, items=None, start=None, keep=None):
        """Reorder a document's items.

        :param items: items to reorder (None = reorder instance items)
        :param start: level to start numbering (None = use current start)
        :param keep: item or ID to keep over duplicates

        """
        items = items or self.items
        keep = self.find_item(keep) if keep else None
        logging.info("reordering {}...".format(self))
        self._reorder(items, start=start, keep=keep)

    @staticmethod
    def _reorder(items, start=None, keep=None):
        """Reorder a document's items.

        :param items: items to reorder
        :param start: level to start numbering (None = use current start)
        :param keep: item to keep over duplicates

        """
        nlevel = plevel = None
        for clevel, item in Document._items_by_level(items, keep=keep):
            logging.debug("current level: {}".format(clevel))
            # Determine the next level
            if not nlevel:
                # Use the specified or current starting level
                nlevel = Level(start) if start else clevel
                nlevel.heading = clevel.heading
                logging.debug("next level (start): {}".format(nlevel))
            else:
                # Adjust the next level to be the same depth
                if len(clevel) > len(nlevel):
                    nlevel >>= len(clevel) - len(nlevel)
                    logging.debug("matched current indent: {}".format(nlevel))
                elif len(clevel) < len(nlevel):
                    nlevel <<= len(nlevel) - len(clevel)
                    # nlevel += 1
                    logging.debug("matched current dedent: {}".format(nlevel))
                nlevel.heading = clevel.heading
                # Check for a level jump
                _size = min(len(clevel.value), len(plevel.value))
                for index in range(max(_size - 1, 1)):
                    if clevel.value[index] > plevel.value[index]:
                        nlevel <<= len(nlevel) - 1 - index
                        nlevel += 1
                        nlevel >>= len(clevel) - len(nlevel)
                        msg = "next level (jump): {}".format(nlevel)
                        logging.debug(msg)
                        break
                # Check for a normal increment
                else:
                    if len(nlevel) <= len(plevel):
                        nlevel += 1
                        msg = "next level (increment): {}".format(nlevel)
                        logging.debug(msg)
                    else:
                        msg = "next level (indent/dedent): {}".format(nlevel)
                        logging.debug(msg)
            # Apply the next level
            if clevel == nlevel:
                logging.info("{}: {}".format(item, clevel))
            else:
                logging.info("{}: {} to {}".format(item, clevel, nlevel))
            item.level = nlevel.copy()
            # Save the current level as the previous level
            plevel = clevel.copy()

    @staticmethod
    def _items_by_level(items, keep=None):
        """Iterate through items by level with the kept item first."""
        # Collect levels
        levels = OrderedDict()
        for item in items:
            if item.level in levels:
                levels[item.level].append(item)
            else:
                levels[item.level] = [item]
        # Reorder levels
        for level, items in levels.items():
            # Reorder items at this level
            if keep in items:
                # move the kept item to the front of the list
                logging.debug("keeping {} level over duplicates".format(keep))
                items = [items.pop(items.index(keep))] + items
            for item in items:
                yield level, item

    def find_item(self, value, _kind=''):
        """Return an item by its ID.

        :param value: item or ID

        :raises: :class:`~doorstop.common.DoorstopError` if the item
            cannot be found

        :return: matching :class:`~doorstop.core.item.Item`

        """
        identifier = ID(value)
        for item in self:
            if item.id == identifier:
                return item

        raise DoorstopError("no matching{} ID: {}".format(_kind, identifier))

    def get_issues(self, item_hook=None, **kwargs):
        """Yield all the document's issues.

        :param item_hook: function to call for custom item validation

        :return: generator of :class:`~doorstop.common.DoorstopError`,
                              :class:`~doorstop.common.DoorstopWarning`,
                              :class:`~doorstop.common.DoorstopInfo`

        """
        assert kwargs.get('document_hook') is None
        hook = item_hook if item_hook else lambda **kwargs: []
        logging.info("checking document {}...".format(self))
        # Check for items
        items = self.items
        if not items:
            yield DoorstopWarning("no items")
            return
        # Reorder or check item levels
        if settings.REORDER:
            self.reorder(items=items)
        elif settings.CHECK_LEVELS:
            yield from self._get_issues_level(items)
        # Check each item
        for item in self:
            # Check item
            for issue in chain(hook(item=item, document=self, tree=self.tree),
                               item.get_issues()):
                # Prepend the item's ID to yielded exceptions
                if isinstance(issue, Exception):
                    yield type(issue)("{}: {}".format(item.id, issue))

    @staticmethod
    def _get_issues_level(items):
        """Yield all the document's issues related to item level."""
        prev = items[0] if items else None
        for item in items[1:]:
            pid = prev.id
            plev = prev.level
            nid = item.id
            nlev = item.level
            logging.debug("checking level {} to {}...".format(plev, nlev))
            # Duplicate level
            if plev == nlev:
                ids = sorted((pid, nid))
                msg = "duplicate level: {} ({}, {})".format(plev, *ids)
                yield DoorstopWarning(msg)
            # Skipped level
            length = min(len(plev.value), len(nlev.value))
            for index in range(length):
                # Types of skipped levels:
                #         1. over: 1.0 --> 1.2
                #         2. out: 1.1 --> 3.0
                if (nlev.value[index] - plev.value[index] > 1 or
                        # 3. over and out: 1.1 --> 2.2
                        (plev.value[index] != nlev.value[index] and
                         index + 1 < length and
                         nlev.value[index + 1] not in (0, 1))):
                    msg = "skipped level: {} ({}), {} ({})".format(plev, pid,
                                                                   nlev, nid)
                    yield DoorstopWarning(msg)
                    break
            prev = item

    @clear_document_cache
    def delete(self, path=None):
        """Delete the document and its items."""
        for item in self:
            item.delete()
        super().delete(self.config)
        common.delete(self.path)
