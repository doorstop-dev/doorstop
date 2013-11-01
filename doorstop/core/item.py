#!/usr/bin/env python

"""
Representation of items in a Doorstop document.
"""

import os
import re
import functools
import logging

import yaml


from doorstop.common import DoorstopError


def _auto_load(func):
    """Decorator for methods that should automatically load from file."""
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        """Wrapped method to call self.load() before execution."""
        self.load()
        return func(self, *args, **kwargs)
    return wrapped


def _auto_save(func):
    """Decorator for methods that should automatically save to file."""
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        """Wrapped method to call self.save() after execution."""
        result = func(self, *args, **kwargs)
        self.save()
        return result

    return wrapped


class Item(object):
    """Represents a file with linkable text that is part of a document."""

    # TODO: only load if an attribute is blank?

    EXTENSIONS = '.yml', '.yaml'

    DEFAULT_LEVEL = (1,)
    DEFAULT_TEXT = ""
    DEFAULT_REF = None
    DEFAULT_LINKS = set()

    def __init__(self, path, root=os.getcwd(),
                 level=None, text=None, ref=None, links=None):
        """Create a new Item.

        @param path: path to Item file
        @param root: path to root of project
        """
        filename = os.path.basename(path)
        name, ext = os.path.splitext(filename)
        # Check file name
        try:
            self.split_id(name)
        except DoorstopError:
            raise
        # Check file extension
        if ext.lower() not in self.EXTENSIONS:
            msg = "'{0}' extension not in {1}".format(path, self.EXTENSIONS)
            raise DoorstopError(msg)
        # Initialize Item
        self.path = path
        self.root = root
        self._level = level or Item.DEFAULT_LEVEL
        self._text = text or Item.DEFAULT_TEXT
        self._ref = ref or Item.DEFAULT_REF
        self._links = links or Item.DEFAULT_LINKS

    def __repr__(self):
        return "Item({})".format(repr(self.path))

    def __str__(self):
        relpath = os.path.relpath(self.path, self.root)
        return "{} (@{}{})".format(self.id, os.sep, relpath)

    def __eq__(self, other):
        return isinstance(other, Item) and self.path == other.path

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        return self.level < other.level

    def load(self):
        """Load the item's properties from a file."""
        logging.debug("loading {}...".format(repr(self)))
        text = self._read()
        try:
            data = yaml.load(text)
        except yaml.scanner.ScannerError as error:
            msg = "invalid contents: {}:\n{}".format(self, error)
            raise DoorstopError(msg)
        if data:
            self._level = self._convert_level(data.get('level', self._level))
            self._text = data.get('text', self._text)
            self._ref = data.get('ref', self._ref)
            self._links = set(data.get('links', self._links))

    def _read(self):  # pragma: no cover, integration test
        """Read text from the file."""
        with open(self.path, 'rb') as infile:
            return infile.read().decode('UTF-8')

    def save(self):
        """Save the item's properties to a file."""
        logging.debug("saving {}...".format(repr(self)))
        level = '.'.join(str(n) for n in self._level)
        if len(self._level) == 2:
            level = float(level)
        elif len(self._level) == 1:
            level = int(level)
        text = self._text
        ref = self._ref
        links = sorted(self._links)
        data = {'level': level,
                'text': text,
                'links': links}
        if ref:
            data['ref'] = ref
        text = yaml.dump(data)
        self._write(text)

    def _write(self, text):  # pragma: no cover, integration test
        """Write text to the file."""
        with open(self.path, 'wb') as outfile:
            outfile.write(bytes(text, 'UTF-8'))

    @property
    def id(self):  # pylint: disable=C0103
        """Get the item's ID."""
        return os.path.splitext(os.path.basename(self.path))[0]

    @staticmethod
    def split_id(text):
        """Split an item's ID into prefix and number.

        >>> Item.split_id("ABC00123")
        ('ABC', 123)

        """
        match = re.match(r"([a-zA-Z]+)(\d+)", text)
        if not match:
            raise DoorstopError("invalid ID: {}".format(text))
        return match.group(1), int(match.group(2))

    @property
    def prefix(self):
        """Get the item ID's prefix."""
        return self.split_id(self.id)[0]

    @property
    def number(self):
        """Get the item ID's number."""
        return self.split_id(self.id)[1]

    @property
    @_auto_load
    def level(self):
        """Get the item level."""
        return self._level

    @level.setter
    @_auto_save
    def level(self, level):
        """Set the item's level."""
        self._level = self._convert_level(level)

    @staticmethod
    def _convert_level(text):
        """Convert a level string to a tuple.

        >>> Item._convert_level("1.2.3")
        (1, 2, 3)

        >>> Item._convert_level(['4', '5'])
        (4, 5)

        >>> Item._convert_level(4.2)
        (4, 2)

        """
        # Correct for integers (42) and floats (4.2) in YAML
        if isinstance(text, int) or isinstance(text, float):
            text = str(text)
        # Split strings by periods
        if isinstance(text, str):
            nums = text.split('.')
        else:
            nums = text
        return tuple(int(n) for n in nums)

    @property
    @_auto_load
    def text(self):
        """Get the item's text."""
        return self._text

    @text.setter
    @_auto_save
    def text(self, text):
        """Set the item's text."""
        self._text = text

    @property
    @_auto_load
    def ref(self):
        """Get the item's external file reference."""
        return self._ref

    @ref.setter
    @_auto_save
    def ref(self, ref):
        """Set the item's external file reference."""
        self._ref = ref

    @_auto_load
    def find_ref(self):
        """Find the external file reference and line number."""
        if not self.ref:
            logging.debug("no external reference to search for")
            return None, None
        regex = re.compile(r"\b{}\b".format(self.ref))
        for root, _, filenames in os.walk(os.path.dirname(self.path)):
            for filename in filenames:  # pragma: no cover, integration test
                path = os.path.join(root, filename)
                if path == self.path:
                    continue
                with open(path) as external:
                    for index, line in enumerate(external):
                        if regex.search(line):
                            return path, index + 1
        raise DoorstopError("external reference not found: {}".format(self.ref))

    @property
    @_auto_load
    def links(self):
        """Get the items this item links to."""
        return sorted(self._links)

    @links.setter
    @_auto_save
    def links(self, links):
        """Set the items this item links to."""
        self._links = set(links)

    @_auto_load
    @_auto_save
    def add_link(self, item):
        """Add a new link to another item."""
        self._links.add(item)

    @_auto_load
    @_auto_save
    def remove_link(self, item):
        """Remove an existing link."""
        try:
            self._links.remove(item)
        except KeyError:
            logging.warning("link to {0} does not exist".format(item))

    def check(self):
        """Confirm the item is valid.

        @return: indication that the item is valid
        """
        logging.info("checking item {}...".format(self))
        # Check text
        if not self.text:
            logging.warning("no text: {}".format(self))
        # Item is valid
        return True
