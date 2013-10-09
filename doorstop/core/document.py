#!/usr/bin/env python

"""
Representation of a collection of Doorstop items.
"""

import os
import logging

import yaml

from doorstop.core import Item


class Document(object):
    """Represents a document containing an outline of items."""

    CONFIG = '.doorstop.yml'
    DEFAULT_PREFIX = 'REQ'
    DEFAULT_DIGITS = 3

    def __init__(self, path, prefix=None, digits=None):
        self.path = path
        self.load()
        self.prefix = prefix or self.prefix
        self.digits = digits or self.digits
        self.save()

    def __str__(self):
        return self.path

    def __iter__(self):
        for filename in os.listdir(self.path):
            path = os.path.join(self.path, filename)
            try:
                yield Item(path)
            except ValueError as error:
                logging.debug(error)

    def load(self):
        """Load the document's properties from a file."""
        logging.debug("loading document '{0}'...".format(self))
        text = self._read()
        data = yaml.load(text)
        if data:
            settings = data.get('settings', {})
            if settings:
                self.prefix = settings.get('prefix', Document.DEFAULT_PREFIX)
                self.digits = settings.get('digits', Document.DEFAULT_DIGITS)

    def _read(self):  # pragma: no cover, integration test
        """Read text from the file."""
        path = os.path.join(self.path, Document.CONFIG)
        with open(path, 'rb') as infile:
            return infile.read().decode('UTF-8')

    def save(self):
        """Save the document's properties to a file."""
        logging.debug("saving document '{0}'...".format(self))
        data = {'prefix': self.prefix,
                'digits': self.digits}
        text = yaml.dump(data)
        self._write(text)

    def _write(self, text):  # pragma: no cover, integration test
        """Write text to the file."""
        path = os.path.join(self.path, Document.CONFIG)
        with open(path, 'wb') as outfile:
            outfile.write(bytes(text, 'UTF-8'))

    @property
    def items(self):
        """Get an ordered list of items in the document."""
        return sorted(item for item in self)
