#!/usr/bin/env python

"""
Representation of items in a Doorstop document.
"""

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

    def __init__(self, path):
        self.path = path
        self._text = ""
        self._links = set()

    def load(self):
        """Load the item's properties from a file."""
        text = self._read()
        data = yaml.load(text)
        if data:
            self._text = data.get('text', self._text)
            self._links = set(data.get('links', self._links))

    def _read(self):  # pragma: no cover, integration test
        """Read text from the file."""
        with open(self.path, 'rb') as infile:
            return infile.read().decode('UTF-8')

    def save(self):
        """Save the item's properties to a file."""
        data = {'text': self._text,
                'links': sorted(self._links)}
        text = yaml.dump(data)
        self._write(text)

    def _write(self, text):  # pragma: no cover, integration test
        """Write text to the file."""
        with open(self.path, 'wb') as outfile:
            outfile.write(bytes(text, 'UTF-8'))

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
