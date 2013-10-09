#!/usr/bin/env python

"""
Representation of items in a Doorstop document.
"""

import os
import re
import functools
import logging

import yaml


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

    def __init__(self, path):
        self.path = path
        self._level = 1,
        self._text = ""
        self._links = set()

    def __repr__(self):
        return "Item({})".format(repr(self.path))

    def __str__(self):
        return self.id

    def __eq__(self, other):
        return isinstance(other, Item) and self.path == other.path

    def __ne__(self, other):
        return not (self == other)

    def load(self):
        """Load the item's properties from a file."""
        text = self._read()
        data = yaml.load(text)
        if data:
            self._level = self._convert_level(data.get('level', self._level))
            self._text = data.get('text', self._text)
            self._links = set(data.get('links', self._links))

    def _read(self):  # pragma: no cover, integration test
        """Read text from the file."""
        with open(self.path, 'rb') as infile:
            return infile.read().decode('UTF-8')

    def save(self):
        """Save the item's properties to a file."""
        data = {'level': '.'.join(str(n) for n in self._level),
                'text': self._text,
                'links': sorted(self._links)}
        text = yaml.dump(data)
        self._write(text)

    def _write(self, text):  # pragma: no cover, integration test
        """Write text to the file."""
        with open(self.path, 'wb') as outfile:
            outfile.write(bytes(text, 'UTF-8'))

    @property
    def id(self):
        """Get the item's ID."""
        return os.path.splitext(os.path.basename(self.path))[0]

    @staticmethod
    def _split_id(text):
        """Split an item's ID into prefix and number.

        >>> Item._split_id("ABC00123")
        ('ABC', 123)

        """
        match = re.match("(\w*[^\d])(\d+)", text)
        return match.group(1), int(match.group(2))

    @property
    def prefix(self):
        """Get the item ID's prefix."""
        return self._split_id(self.id)[0]

    @property
    def number(self):
        """Get the item ID's number."""
        return self._split_id(self.id)[1]

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

        """
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
