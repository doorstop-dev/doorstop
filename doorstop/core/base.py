"""Base classes and decorators for the doorstop.core package."""

import os
import abc
import functools

import yaml

from doorstop import common
from doorstop.common import DoorstopError, DoorstopWarning, DoorstopInfo
from doorstop import settings

log = common.logger(__name__)


def add_item(func):
    """Decorator for methods that return a new item."""
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        """Wrapped method to add and cache the returned item."""
        item = func(self, *args, **kwargs) or self
        if settings.ADDREMOVE_FILES and item.tree:
            item.tree.vcs.add(item.path)
        # pylint: disable=W0212
        if item.document and item not in item.document._items:
            item.document._items.append(item)
        if settings.CACHE_ITEMS and item.tree:
            item.tree._item_cache[item.uid] = item
            log.trace("cached item: {}".format(item))
        return item
    return wrapped


def edit_item(func):
    """Decorator for methods that return a modified item."""
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        """Wrapped method to mark the returned item as modified."""
        item = func(self, *args, **kwargs) or self
        if settings.ADDREMOVE_FILES and item.tree:
            item.tree.vcs.edit(item.path)
        return item
    return wrapped


def delete_item(func):
    """Decorator for methods that return a deleted item."""
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        """Wrapped method to remove and expunge the returned item."""
        item = func(self, *args, **kwargs) or self
        if settings.ADDREMOVE_FILES and item.tree:
            item.tree.vcs.delete(item.path)
        # pylint: disable=W0212
        if item.document and item in item.document._items:
            item.document._items.remove(item)
        if settings.CACHE_ITEMS and item.tree:
            item.tree._item_cache[item.uid] = None
            log.trace("expunged item: {}".format(item))
        BaseFileObject.delete(item, item.path)
        return item
    return wrapped


def add_document(func):
    """Decorator for methods that return a new document."""
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        """Wrapped method to add and cache the returned document."""
        document = func(self, *args, **kwargs) or self
        if settings.ADDREMOVE_FILES and document.tree:
            document.tree.vcs.add(document.config)
        # pylint: disable=W0212
        if settings.CACHE_DOCUMENTS and document.tree:
            document.tree._document_cache[document.prefix] = document
            log.trace("cached document: {}".format(document))
        return document
    return wrapped


def edit_document(func):
    """Decorator for methods that return a modified document."""
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        """Wrapped method to mark the returned document as modified."""
        document = func(self, *args, **kwargs) or self
        if settings.ADDREMOVE_FILES and document.tree:
            document.tree.vcs.edit(document.config)
        return document
    return wrapped


def delete_document(func):
    """Decorator for methods that return a deleted document."""
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        """Wrapped method to remove and expunge the returned document."""
        document = func(self, *args, **kwargs) or self
        if settings.ADDREMOVE_FILES and document.tree:
            document.tree.vcs.delete(document.path)
        # pylint: disable=W0212
        if settings.CACHE_DOCUMENTS and document.tree:
            document.tree._document_cache[document.prefix] = None
            log.trace("expunged document: {}".format(document))
        BaseFileObject.delete(document, document.path)
        return document
    return wrapped


class BaseValidatable(object, metaclass=abc.ABCMeta):  # pylint:disable=R0921
    """Abstract Base Class for objects that can be validated."""

    def validate(self, skip=None, document_hook=None, item_hook=None):
        """Check the object for validity.

        :param skip: list of document prefixes to skip
        :param document_hook: function to call for custom document
            validation
        :param item_hook: function to call for custom item validation

        :return: indication that the object is valid

        """
        valid = True
        # Display all issues
        for issue in self.get_issues(skip=skip, document_hook=document_hook,
                                     item_hook=item_hook):
            if isinstance(issue, DoorstopInfo) and not settings.WARN_ALL:
                log.info(issue)
            elif isinstance(issue, DoorstopWarning) and not settings.ERROR_ALL:
                log.warning(issue)
            else:
                assert isinstance(issue, DoorstopError)
                log.error(issue)
                valid = False
        # Return the result
        return valid

    @abc.abstractmethod
    def get_issues(self, skip=None, document_hook=None, item_hook=None):
        """Yield all the objects's issues.

        :param skip: list of document prefixes to skip
        :param document_hook: function to call for custom document
            validation
        :param item_hook: function to call for custom item validation

        :return: generator of :class:`~doorstop.common.DoorstopError`,
                              :class:`~doorstop.common.DoorstopWarning`,
                              :class:`~doorstop.common.DoorstopInfo`

        """

    @property
    def issues(self):
        """Get a list of the item's issues."""
        return list(self.get_issues())


def auto_load(func):
    """Decorator for methods that should automatically load from file."""
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        """Wrapped method to call self.load() before execution."""
        self.load()
        return func(self, *args, **kwargs)
    return wrapped


def auto_save(func):
    """Decorator for methods that should automatically save to file."""
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        """Wrapped method to call self.save() after execution."""
        result = func(self, *args, **kwargs)
        if self.auto:
            self.save()
        return result
    return wrapped


class BaseFileObject(object, metaclass=abc.ABCMeta):  # pylint:disable=R0921
    """Abstract Base Class for objects whose attributes save to a file.

    For properties that are saved to a file, decorate their getters
    with :func:`auto_load` and their setters with :func:`auto_save`.

    """

    auto = True  # set to False to delay automatic save until explicit save

    def __init__(self):
        self.path = None
        self.root = None
        self._data = {}
        self._exists = True
        self._loaded = False

    def __hash__(self):
        return hash(self.path)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.path == other.path

    def __ne__(self, other):
        return not self == other

    @staticmethod
    def _create(path, name):  # pragma: no cover (integration test)
        """Create a new file for the object.

        :param path: path to new file
        :param name: humanized name for this file

        :raises: :class:`~doorstop.common.DoorstopError` if the file
            already exists

        """
        if os.path.exists(path):
            raise DoorstopError("{} already exists: {}".format(name, path))
        common.create_dirname(path)
        common.touch(path)

    @abc.abstractmethod
    def load(self, reload=False):  # pragma: no cover (abstract method)
        """Load the object's properties from its file."""
        # 1. Start implementations of this method with:
        if self._loaded and not reload:
            return
        # 2. Call self._read() and update properties here
        # 3. End implementations of this method with:
        self._loaded = True

    def _read(self, path):  # pragma: no cover (integration test)
        """Read text from the object's file.

        :param path: path to a text file

        :return: contexts of text file

        """
        if not self._exists:
            msg = "cannot read from deleted: {}".format(self.path)
            raise DoorstopError(msg)
        return common.read_text(path)

    @staticmethod
    def _load(text, path):
        """Load YAML data from text.

        :param text: text read from a file
        :param path: path to the file (for displaying errors)

        :return: dictionary of YAML data

        """
        return common.load_yaml(text, path)

    @abc.abstractmethod
    def save(self):  # pragma: no cover (abstract method)
        """Format and save the object's properties to its file."""
        # 1. Call self._write() with the current properties here
        # 2. End implementations of this method with:
        self._loaded = False
        self.auto = True

    def _write(self, text, path):  # pragma: no cover (integration test)
        """Write text to the object's file.

        :param text: text to write to a file
        :param path: path to the file

        """
        if not self._exists:
            raise DoorstopError("cannot save to deleted: {}".format(self))
        common.write_text(text, path)

    @staticmethod
    def _dump(data):
        """Dump YAML data to text.

        :param data: dictionary of YAML data

        :return: text to write to a file

        """
        return yaml.dump(data, default_flow_style=False, allow_unicode=True)

    # properties #############################################################

    @property
    def relpath(self):
        """Get the item's relative path string."""
        relpath = os.path.relpath(self.path, self.root)
        return "@{}{}".format(os.sep, relpath)

    # extended attributes ####################################################

    @property
    @auto_load
    def extended(self):
        """Get a list of all extended attribute names."""
        names = []
        for name in self._data:
            if not hasattr(self, name):
                names.append(name)
        return sorted(names)

    @auto_load
    def get(self, name, default=None):
        """Get an extended attribute.

        :param name: name of extended attribute
        :param default: value to return for missing attributes

        :return: value of extended attribute

        """
        if hasattr(self, name):
            cname = self.__class__.__name__
            msg = "'{n}' can be accessed from {c}.{n}".format(n=name, c=cname)
            log.trace(msg)
            return getattr(self, name)
        else:
            return self._data.get(name, default)

    @auto_load
    @auto_save
    def set(self, name, value):
        """Set an extended attribute.

        :param name: name of extended attribute
        :param value: value to set

        """
        if hasattr(self, name):
            cname = self.__class__.__name__
            msg = "'{n}' can be set from {c}.{n}".format(n=name, c=cname)
            log.trace(msg)
            return setattr(self, name, value)
        else:
            self._data[name] = value

    # actions ################################################################

    def delete(self, path):
        """Delete the object's file from the file system."""
        if self._exists:
            log.info("deleting {}...".format(self))
            common.delete(path)
            self._loaded = False  # force the object to reload
            self._exists = False  # but, prevent future access
        else:
            log.warning("already deleted: {}".format(self))
