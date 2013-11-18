#!/usr/bin/env python

"""
Representation of a collection of Doorstop items.
"""

import os
import logging

import yaml

from doorstop.core.item import Item
from doorstop.common import DoorstopError


class Document(object):
    """Represents a document containing an outline of items."""

    CONFIG = '.doorstop.yml'
    SKIP = '.doorstop.skip'  # indicates this document should be skipped
    DEFAULT_PREFIX = 'REQ'
    DEFAULT_PARENT = None  # which indicates this is the root document
    DEFAULT_DIGITS = 3

    def __init__(self, path, root=os.getcwd(),
                 _prefix=None, _parent=None, _digits=None):
        """Load a Document from an exiting directory.

        Internally, this constructor is also used to initialize new
        documents by providing default properites.

        @param path: path to Document directory
        @param root: path to root of project
        """
        # Check document's directory
        if not os.path.isfile(os.path.join(path, Document.CONFIG)):
            relpath = os.path.relpath(path, root)
            msg = "no {} in {}".format(Document.CONFIG, relpath)
            raise DoorstopError(msg)
        # Initialize Document
        self.path = path
        self.root = root
        self.prefix = _prefix or Document.DEFAULT_PREFIX
        self.parent = _parent or Document.DEFAULT_PARENT
        self.digits = _digits or Document.DEFAULT_DIGITS
        self.load()
        self.save()
        # Mark if skippable
        self.skip = os.path.isfile(os.path.join(self.path, Document.SKIP))

    def __repr__(self):
        return "Document({})".format(repr(self.path))

    def __str__(self):
        relpath = os.path.relpath(self.path, self.root)
        return "{} (@{}{})".format(self.prefix, os.sep, relpath)

    def __iter__(self):
        for filename in os.listdir(self.path):
            path = os.path.join(self.path, filename)
            try:
                yield Item(path)
            except DoorstopError as error:
                logging.debug(error)

    def __eq__(self, other):
        return isinstance(other, Document) and self.path == other.path

    def __ne__(self, other):
        return not self == other

    @staticmethod
    def new(path, root, prefix, parent=None, digits=None):
        """Create a new Document.

        @param path: path to directory for the new document
        @param root: path to root of the project
        @param prefix: prefix for the new document
        @param parent: parent ID for the new document
        @param digits: number of digits for the new document

        @raise DoorstopError: if the document already exists
        """
        config = os.path.join(path, Document.CONFIG)
        # Check for an existing document
        if os.path.exists(config):
            raise DoorstopError("document already exists: {}".format(path))
        # Create the document directory
        Document._new(path, config)
        # Return the new document
        return Document(path, root=root,
                        _prefix=prefix, _parent=parent, _digits=digits)

    @staticmethod
    def _new(path, config):  # pragma: no cover, integration test
        """Create a new document directory.

        @param path: path to new document directory
        @param config: path to new document config file
        """
        if not os.path.exists(path):
            os.makedirs(path)
        with open(config, 'w'):
            pass  # just touch the file

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

    def add(self):
        """Create a new item for the document and return it."""
        number = self.maximum + 1
        logging.debug("next number: {}".format(number))
        try:
            last = self.items[-1]
        except IndexError:
            level = None
        else:
            level = last.level[:-1] + (last.level[-1] + 1,)
        logging.debug("next level: {}".format(level))
        return Item.new(self.path, self.root, self.prefix, self.digits,
                        number, level)

    @property
    def maximum(self):
        """Return the highest item number in the document."""
        try:
            return max(item.number for item in self)
        except ValueError:
            return 0

    def check(self, tree=None):
        """Confirm the document is valid.

        @return: indication that document is valid
        """
        logging.info("checking document {}...".format(self))
        items = list(self)
        # Check for items
        if not items:
            logging.warning("no items: {}".format(self))
        # Check each item
        for item in items:
            item.check(document=self, tree=tree)
        # Document is valid
        return True
