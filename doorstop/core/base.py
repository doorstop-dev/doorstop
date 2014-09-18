"""Base classes and decorators for the doorstop.core package."""

import os
import abc
import functools


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


class BaseValidatable(metaclass=abc.ABCMeta):  # pylint:disable=R0921

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
        if hasattr(self, 'yorm_mapper'):
            self.yorm_mapper.retrieve(self)
        return func(self, *args, **kwargs)
    return wrapped


def auto_save(func):
    """Decorator for methods that should automatically save to file."""
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        """Wrapped method to call self.save() after execution."""
        result = func(self, *args, **kwargs)
        if hasattr(self, 'yorm_mapper') and self.auto:
            self.yorm_mapper.store(self)
        return result
    return wrapped


class BaseFileObject(metaclass=abc.ABCMeta):  # pylint:disable=R0921

    """Abstract Base Class for objects whose attributes save to a file."""

    auto = True  # TODO: remove this attribute (it's part of YORM now)

    def __init__(self):
        self.path = None
        self.root = None

    def __hash__(self):
        return hash(self.path)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.path == other.path

    def __ne__(self, other):
        return not self == other

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
