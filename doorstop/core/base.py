"""Base classes and decorators for the doorstop.core package."""

import os
import abc
import functools

import yaml

from doorstop import common
from doorstop.common import DoorstopError, DoorstopWarning, DoorstopInfo
from doorstop import settings

log = common.logger(__name__)


def cache_item(func):
    """Decorator for methods that add returned item to cache."""
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        """Wrapped method to cache the returned item."""
        item = func(self, *args, **kwargs) or self
        # pylint: disable=W0212
        if item.document and item not in item.document._items:
            item.document._items.append(item)
        if settings.CACHE_ITEMS and item.tree:
            item.tree._item_cache[item.uid] = item
            log.trace("cached item: {}".format(item))
        return item
    return wrapped


def expunge_item(func):
    """Decorator for methods that expunge the returned item from cache."""
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        """Wrapped method to expunge the returned item."""
        item = func(self, *args, **kwargs) or self
        # pylint: disable=W0212
        if item.document and item in item.document._items:
            item.document._items.remove(item)
        if settings.CACHE_ITEMS and item.tree:
            item.tree._item_cache[item.uid] = None
            log.trace("expunged item: {}".format(item))
        return item
    return wrapped


def cache_document(func):
    """Decorator for methods that add the returned document to cache."""
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        """Wrapped method to cache the returned document."""
        document = func(self, *args, **kwargs) or self
        # pylint: disable=W0212
        if settings.CACHE_DOCUMENTS and document.tree:
            document.tree._document_cache[document.prefix] = document
            log.trace("cached document: {}".format(document))
        return document
    return wrapped


class BaseValidatable(object, metaclass=abc.ABCMeta):  # pylint:disable=R0921

    """Abstract Base Class for objects that can be validated."""

    def validate(self, document_hook=None, item_hook=None):
        """Check the object for validity.

        :param document_hook: function to call for custom document
            validation
        :param item_hook: function to call for custom item validation

        :return: indication that the object is valid

        """
        valid = True
        # Display all issues
        for issue in self.get_issues(document_hook=document_hook,
                                     item_hook=item_hook):
            if isinstance(issue, DoorstopInfo):
                log.info(issue)
            elif isinstance(issue, DoorstopWarning):
                log.warning(issue)
            else:
                assert isinstance(issue, DoorstopError)
                log.error(issue)
                valid = False
        # Return the result
        return valid

    @abc.abstractmethod
    def get_issues(self, document_hook=None, item_hook=None):
        """Yield all the objects's issues.

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
        # Start implementations of this method with:
        if self._loaded and not reload:
            return
        # Call self._read() and update properties here:
        pass  # pylint: disable=W0107
        # End implementations of this method with:
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
        # Call self._write() with the current properties here:
        pass  # pylint: disable=W0107
        # End implementations of this method with:
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
            log.info(msg)
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
            log.info(msg)
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
