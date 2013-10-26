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
    SKIP = '.doorstop.skip'  # indicates this document should be skipped
    DEFAULT_PREFIX = 'REQ'
    DEFAULT_PARENT = None  # which indicates this is the root document
    DEFAULT_DIGITS = 3

    def __init__(self, path, root=os.getcwd(), prefix=None, parent=None, digits=None):
        """Create a new Document.

        @param path: path to Document directory
        @param root: path to root of project
        """
        # Check directory contents
        if not prefix:  # not creating a new document
            if not os.path.isfile(os.path.join(path, Document.CONFIG)):
                relpath = os.path.relpath(path, root)
                msg = "no {} in {}".format(Document.CONFIG, relpath)
                raise ValueError(msg)
        # Initialize Document
        self.path = path
        self.root = root
        self.prefix = prefix or Document.DEFAULT_PREFIX
        self.parent = parent or Document.DEFAULT_PARENT
        self.digits = digits or Document.DEFAULT_DIGITS
        self.load()
        self.save()
        # Mark if skippable
        self.skip = os.path.isfile(os.path.join(self.path, Document.SKIP))

    def __repr__(self):
        return "Document({})".format(repr(self.path))

    def __str__(self):
        relpath = os.path.relpath(self.path, self.root)
        return "{} (@/{})".format(self.prefix, relpath)

    def __iter__(self):
        for filename in os.listdir(self.path):
            path = os.path.join(self.path, filename)
            try:
                yield Item(path)
            except ValueError as error:
                logging.debug(error)

    def __eq__(self, other):
        return isinstance(other, Document) and self.path == other.path

    def __ne__(self, other):
        return not self == other

    def load(self):
        """Load the document's properties from a file."""
        logging.debug("loading {}...".format(repr(self)))
        text = self._read()
        data = yaml.load(text)
        if data:
            settings = data.get('settings', {})
            if settings:
                self.prefix = settings.get('prefix', self.prefix)
                self.parent = settings.get('parent', self.parent)
                self.digits = settings.get('digits', self.digits)

    def _read(self):  # pragma: no cover, integration test
        """Read text from the file."""
        path = os.path.join(self.path, Document.CONFIG)
        if not os.path.exists(path):
            logging.debug("document does not exist yet: {}".format(path))
            return ""
        with open(path, 'rb') as infile:
            return infile.read().decode('UTF-8')

    def save(self):
        """Save the document's properties to a file."""
        logging.debug("saving {}...".format(repr(self)))
        settings = {'prefix': self.prefix,
                    'digits': self.digits}
        if self.parent:
            settings['parent'] = self.parent
        data = {'settings': settings}
        text = yaml.dump(data, default_flow_style=False)
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
