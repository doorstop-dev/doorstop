#!/usr/bin/env python

"""
Compiles the Doorstop document hierarchy.
"""

import os
import sys
import shutil
import subprocess
import logging
from itertools import chain

from doorstop.common import DoorstopError
from doorstop.core.document import Document
from doorstop.core.item import Item
from doorstop.core import vcs


class Node(object):
    """
    A bidirectional tree structure to store the document heirarchy.

    Although requirements link "upwards", bidirectionality simplifies
    document processing and validation.
    """

    def __init__(self, document, parent=None, root=None):
        self.document = document
        self.root = root or document.root  # allows non-documents in tests
        self.parent = parent
        self.children = []
        self._vcs = None

    def __repr__(self):
        return "<Node {}>".format(self)

    def __str__(self):
        # Build parent prefix string (getattr to support testing)
        prefix = getattr(self.document, 'prefix', self.document)
        # Build children prefix strings
        children = ", ".join(str(c) for c in self.children)
        # Format the tree
        if children:
            return "{} <- [ {} ]".format(prefix, children)
        else:
            return "{}".format(prefix)

    def __len__(self):
        if self.document:
            return 1 + sum(len(child) for child in self.children)
        else:
            return 0

    def __getitem__(self, key):
        raise IndexError("{} cannot be indexed by key".format(self.__class__))

    def __iter__(self):
        yield self.document
        for document in chain(*(iter(c) for c in self.children)):
            yield document

    @staticmethod
    def from_list(docs, root=None):
        """Get a new tree from the list of Documents.

        @param root: path to root of the project
        @param documents: list of Documents

        @return: tree built from Nodes

        @raise DoorstopError: when the tree cannot be built
        """
        if not docs:
            return Node(document=None, root=root)
        unplaced = list(docs)
        for doc in list(unplaced):
            if doc.parent is None:
                logging.debug("added root of tree: {}".format(doc))
                tree = Node(doc)
                logging.info("root of tree: {}".format(doc))
                unplaced.remove(doc)
                break
        else:
            raise DoorstopError("no root document")

        while unplaced:
            count = len(unplaced)
            for doc in list(unplaced):
                try:
                    tree.place(doc)
                except DoorstopError as error:
                    logging.debug(error)
                else:
                    logging.info("added to tree: {}".format(doc))
                    unplaced.remove(doc)

            if len(unplaced) == count:  # no more documents could be placed
                logging.debug("unplaced documents: {}".format(unplaced))
                msg = "unplaced document: {}".format(unplaced[0])
                raise DoorstopError(msg)

        return tree

    @property
    def vcs(self):
        """Get the working copy."""
        if self._vcs is None:
            self._vcs = vcs.load(self.root)
        return self._vcs

    def place(self, doc):
        """Attempt to place the Document in the current tree.

        @param doc: Document to add

        @raise DoorstopError: if the Document cannot yet be placed
        """
        logging.debug("trying to add '{}'...".format(doc))
        if not self.document:

            # Tree is empty
            if doc.parent:
                msg = "no parent for: {}".format(doc)
                raise DoorstopError(msg)
            self.document = doc

        elif doc.parent == self.document.prefix:

            # Current document is the parent
            node = Node(doc, self)
            self.children.append(node)

        else:

            # Search for the parent
            for child in self.children:
                try:
                    child.place(doc)
                except DoorstopError:
                    pass  # the error is raised later
                else:
                    break
            else:
                msg = "no parent for: {}".format(doc)
                raise DoorstopError(msg)

    def check(self):
        """Confirm the document hiearchy is valid.

        @return: indication that hiearchy is valid

        @raise DoorstopError: on issue
        """
        logging.info("checking document tree...")
        for document in self:
            document.check(tree=self)
        return True

    def new(self, path, prefix, parent=None, digits=None):
        """Create a new document and add it to the tree.

        @param path: directory path for the new document
        @param prefix: document's prefix
        @param parent: parent document's prefix
        @param digits: number of digits for the document's numbers

        @return: newly created and placed Document

        @raise DoorstopError: if the document cannot be created
        """
        document = Document.new(path, self.root, prefix,
                                parent=parent, digits=digits)
        try:
            self.place(document)
        except DoorstopError:
            msg = "deleting unplaced directory {}...".format(document.path)
            logging.debug(msg)
            if os.path.exists(document.path):
                shutil.rmtree(document.path)
            raise
        return document

    def add(self, prefix):
        """Add a new item to an existing document.

        @param prefix: document's prefix

        @return: newly created Item

        @raise DoorstopError: if the item cannot be created
        """
        for document in self:
            if document.prefix.lower() == prefix.lower():
                return document.add()

        raise DoorstopError("no matching prefix: {}".format(prefix))

    def remove(self, identifier):
        """Remove an new item from a document.

        @param identifier: item's ID

        @return: removed item

        @raise DoorstopError: if the item cannot be removed
        """
        item = self.find_item(identifier)
        item.delete()

        return item

    def link(self, cid, pid):
        """Add a new link between two items.

        @param cid: child item's ID
        @param pid: parent item's ID

        @return: (child, parent) item pair

        @raise DoorstopError: if the link cannot be created
        """
        logging.info("linking {} to {}...".format(cid, pid))
        # Find child item
        child = self.find_item(cid, 'child')
        # Find parent item
        parent = self.find_item(pid, 'parent')
        # Add link
        child.add_link(parent.id)
        return child, parent

    def unlink(self, cid, pid):
        """Remove a link between two items.

        @param cid: child item's ID
        @param pid: parent item's ID

        @return: (child, parent) item pair

        @raise DoorstopError: if the link cannot be removed
        """
        logging.info("unlinking {} from {}...".format(cid, pid))
        # Find child item
        child = self.find_item(cid, 'child')
        # Find parent item
        parent = self.find_item(pid, 'parent')
        # Remove link
        child.remove_link(parent.id)
        return child, parent

    def edit(self, identifier, tool=None, launch=False):
        """Open an item for editing.

        @param identifier: ID of item to edit
        @param tool: alternative text editor to open the item
        @param launch: open the default text editor

        @raise DoorstopError: if the item cannot be found
        """
        logging.debug("looking for {}...".format(identifier))
        # Find item
        item = self.find_item(identifier)
        # Lock the item
        self.vcs.lock(item.path)
        # Open item
        if launch:
            _open(item.path, tool=tool)
        # Return the item
        return item

    def find_item(self, identifier, kind=''):
        """Return an the item from its ID.

        @param identifier: item ID
        @param kind: type of item for logging messages

        @return: matching Item

        @raise DoorstopError: if the item cannot be found
        """
        _kind = (' ' + kind) if kind else kind
        prefix, number = Item.split_id(identifier)
        for document in self:
            if document.prefix.lower() == prefix.lower():
                for item in document:
                    if item.number == number:
                        return item
                msg = "no matching{} number: {}".format(_kind, number)
                logging.info(msg)
                break
        else:
            logging.info("no matching{} prefix: {}".format(_kind, prefix))

        raise DoorstopError("no matching{} ID: {}".format(_kind, identifier))


def _open(path, tool=None):  # pragma: no cover, integration test
    """Open the text file using the default editor."""
    if tool:
        args = [tool, path]
        logging.debug("$ {}".format(' '.join(args)))
        subprocess.call(args)
    elif sys.platform.startswith('darwin'):
        args = ['open', path]
        logging.debug("$ {}".format(' '.join(args)))
        subprocess.call(args)
    elif os.name == 'nt':
        logging.debug("$ (start) {}".format(path))
        os.startfile(path)  # pylint: disable=E1101
    elif os.name == 'posix':
        args = ['xdg-open', path]
        logging.debug("$ {}".format(' '.join(args)))
        subprocess.call(args)


def build(cwd, root=None):
    """Build a document heirachy from the current root directory.

    @param cwd: current working directory
    @param root: path to root of the working copy

    @return: tree built from Nodes

    @raise DoorstopError: when the tree cannot be built
    """
    documents = []

    # Find the root of the working copy
    root = root or vcs.find_root(cwd)

    # Find all documents in the working copy
    logging.info("looking for documents in {}...".format(root))
    _add_document_from_path(root, root, documents)
    for dirpath, dirnames, _ in os.walk(root):
        for dirname in dirnames:
            path = os.path.join(dirpath, dirname)
            _add_document_from_path(path, root, documents)

    # Build the document tree
    if not documents:
        logging.warning("no documents found")
    logging.info("building document tree...")
    tree = Node.from_list(documents, root=root)
    logging.info("final document tree: {}".format(tree))
    return tree


def _add_document_from_path(path, root, documents):
    """Attempt to create and append a document from the specified path.

    @param path: path to a potential document
    @param root: path to root of working copy
    @param documents: list of documents to append results
    """
    try:
        document = Document(path, root)
    except DoorstopError:
        pass  # no document in directory
    else:
        if document.skip:
            logging.debug("skipping document: {}".format(document))
        else:
            logging.info("found document: {}".format(document))
            documents.append(document)
