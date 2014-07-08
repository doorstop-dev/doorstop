"""Base classes and decorators for the doorstop.core package."""

import os
import abc
import functools
import logging

import yaml

from doorstop import common
from doorstop.common import DoorstopError, DoorstopWarning, DoorstopInfo


def clear_document_cache(func):
    """Decorator for methods that should clear the document cache."""
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        """Wrapped method to clear document cache after execution."""
        result = func(self, *args, **kwargs)
        try:
            tree = self.tree  # document or item method was decorated
        except AttributeError:
            tree = self  # tree method was decorated
        if tree:
            tree._document_cache.clear()  # pylint: disable=W0212
        return result
    return wrapped


def clear_item_cache(func):
    """Decorator for methods that should clear the item cache."""
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        """Wrapped method to clear item cache after execution."""
        result = func(self, *args, **kwargs)
        try:
            tree = self.tree  # document or item method was decorated
        except AttributeError:
            tree = self  # tree method was decorated
        if tree:
            tree._item_cache.clear()  # pylint: disable=W0212
        return result
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
                logging.info(issue)
            elif isinstance(issue, DoorstopWarning):
                logging.warning(issue)
            else:
                assert isinstance(issue, DoorstopError)
                logging.error(issue)
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
    def _new(path, name):  # pragma: no cover (integration test)
        """Create a new file for the object.

        :param path: path to new file
        :param name: humanized name for this file

        :raises: :class:`~doorstop.common.DoorstopError` if the file
            already exists

        """
        if os.path.exists(path):
            raise DoorstopError("{} already exists: {}".format(name, path))
        dirpath = os.path.dirname(path)
        if not os.path.isdir(dirpath):
            os.makedirs(dirpath)
        with open(path, 'w'):
            pass  # just touch the file

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
        with open(path, 'rb') as stream:
            return stream.read().decode('utf-8')

    @staticmethod
    def _load(text, path):
        """Load YAML data from text.

        :param text: text read from a file
        :param path: path to the file (for displaying errors)

        :return: dictionary of YAML data

        """
        # Load the YAML data
        try:
            data = yaml.load(text) or {}
        except yaml.scanner.ScannerError as exc:  # pylint: disable=E1101
            msg = "invalid contents: {}:\n{}".format(path, exc)
            raise DoorstopError(msg) from None
        # Ensure data is a dictionary
        if not isinstance(data, dict):
            msg = "invalid contents: {}".format(path)
            raise DoorstopError(msg)
        return data

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
        with open(path, 'wb') as outfile:
            outfile.write(text.encode('utf-8'))

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
            logging.info(msg)
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
            logging.info(msg)
            return setattr(self, name, value)
        else:
            self._data[name] = value

    # actions ################################################################

    def delete(self, path):
        """Delete the object's file from the file system."""
        if self._exists:
            logging.info("deleting {}...".format(self))
            logging.debug("deleting file {}...".format(path))
            common.delete(path)
            self._loaded = False  # force the object to reload
            self._exists = False  # but, prevent future access
        else:
            logging.warning("already deleted: {}".format(self))


def write_lines(lines, path, end='\n', encoding='utf-8'):  # pragma: no cover (integration test)
    """Write lines of text to a file."""
    logging.debug("writing lines to {}...".format(path))
    with open(path, 'wb') as stream:
        for line in lines:
            stream.write((line + end).encode(encoding))
