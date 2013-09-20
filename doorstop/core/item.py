#!/usr/bin/env python

"""
Representation of items in a Doorstop document.
"""

import logging

import yaml


class Item(object):
    """Represents a file with linkable text that is part of a document."""

    # TODO: add auto load/save

    def __init__(self, path):
        self.path = path
        self._text = ""
        self._links = set()

    def load(self):
        """Load the item's properties from a file."""
        text = self._read()
        yaml.load(text)

    def _read(self):  # pragma: no cover, integration test
        with open(self.path, 'rb') as infile:
            return infile.read()

    def save(self):
        """Save the item's properties to a file."""

    def _write(self, text):  # pragma: no cover, integration test
        with open(self.path, 'wb') as outfile:
            outfile.write(text)

    @property
    def text(self):
        """Get the item's text."""
        return self._text

    @text.setter
    def text(self, text):
        """Set the item's text."""
        self._text = text

    @property
    def links(self):
        """Get the items this item links to."""
        return sorted(self._links)

    def add_link(self, item):
        """Add a new link to another item."""
        self._links.add(item)

    def remove_link(self, item):
        """Remove an existing link."""
        try:
            self._links.remove(item)
        except ValueError:
            logging.warning("link to {0} does not exist".format(item))
