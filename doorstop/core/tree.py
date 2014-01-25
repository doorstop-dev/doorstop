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
from doorstop.core.item import split_id
from doorstop.core import vcs


class Tree(object):
    """
    A bidirectional tree structure to store the hierarchy or documents.

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
        return "<{} {}>".format(self.__class__.__name__, self)

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
        if self.document:
            yield self.document
        yield from chain(*(iter(c) for c in self.children))

    @staticmethod
    def from_list(docs, root=None):
        """Get a new tree from the list of Documents.

        @param root: path to root of the project
        @param documents: list of Documents

        @return: new tree

        @raise DoorstopError: when the tree cannot be built
        """
        if not docs:
            return Tree(document=None, root=root)
        unplaced = list(docs)
        for doc in list(unplaced):
            if doc.parent is None:
                logging.debug("added root of tree: {}".format(doc))
                tree = Tree(doc)
                logging.info("root of tree: {}".format(doc))
                unplaced.remove(doc)
                break
        else:
            raise DoorstopError("no root document")

        while unplaced:
            count = len(unplaced)
            for doc in list(unplaced):
                try:
                    tree._place(doc)  # pylint: disable=W0212
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

    def _place(self, doc):
        """Attempt to place the Document in the current tree.

        @param doc: Document to add

        @raise DoorstopError: if the Document cannot yet be placed
        """
        logging.debug("trying to add '{}'...".format(doc))
        if not self.document:

            # Tree is empty
            if doc.parent:
                msg = "unknown parent for {}: {}".format(doc, doc.parent)
                raise DoorstopError(msg)
            self.document = doc

        elif doc.parent.lower() == self.document.prefix.lower():

            # Current document is the parent
            node = Tree(doc, self)
            self.children.append(node)

        else:

            # Search for the parent
            for child in self.children:
                try:
                    child._place(doc)  # pylint: disable=W0212
                except DoorstopError:
                    pass  # the error is raised later
                else:
                    break
            else:
                msg = "unknown parent for {}: {}".format(doc, doc.parent)
                raise DoorstopError(msg)

    # attributes #############################################################

    @property
    def vcs(self):
        """Get the working copy."""
        if self._vcs is None:
            self._vcs = vcs.load(self.root)
        return self._vcs

    # actions ################################################################

    def new(self, path, prefix, sep=None, parent=None, digits=None):
        """Create a new document and add it to the tree.

        @param path: directory path for the new document
        @param prefix: document's prefix
        @param sep: separator between prefix and number for items
        @param parent: parent document's prefix
        @param digits: number of digits for the document's numbers

        @return: newly created and placed Document

        @raise DoorstopError: if the document cannot be created
        """
        document = Document.new(path, self.root, prefix, sep=sep,
                                parent=parent, digits=digits)
        try:
            self._place(document)
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
        document = self.find_document(prefix)
        self.vcs.lock(document.config)  # prevents duplicate item IDs
        item = document.add()
        return item

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

    def find_document(self, prefix):
        """Return a document from its prefix.

        @param prefix: document's prefix

        @return: matching Document

        @raise DoorstopError: if the document cannot be found
        """
        for document in self:
            if document.prefix.lower() == prefix.lower():
                return document

        raise DoorstopError("no matching prefix: {}".format(prefix))

    def find_item(self, identifier, kind=''):
        """Return an item from its ID.

        @param identifier: item ID
        @param kind: type of item for logging messages

        @return: matching Item

        @raise DoorstopError: if the item cannot be found
        """
        _kind = (' ' + kind) if kind else kind

        # Search using the prefix and number
        prefix, number = split_id(identifier)
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

        # Fall back to a search using the exact ID
        for document in self:
            for item in document:
                if item.id.lower() == identifier.lower():
                    return item

        raise DoorstopError("no matching{} ID: {}".format(_kind, identifier))

    def check(self):
        """Confirm the document hiearchy is valid.

        @return: indication that hiearchy is valid

        @raise DoorstopError: on issue
        """
        logging.info("checking tree...")
        for document in self:
            document.check(tree=self, ignored=self.vcs.ignored)
        return True


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


def build(cwd=None, root=None):
    """Build a document hierarchy from the current root directory.

    @param cwd: current working directory
    @param root: path to root of the working copy

    @return: new tree

    @raise DoorstopError: when the tree cannot be built
    """
    documents = []

    # Find the root of the working copy
    cwd = cwd or os.getcwd()
    root = root or vcs.find_root(cwd)

    # Find all documents in the working copy
    logging.info("looking for documents in {}...".format(root))
    _add_document_from_path(root, root, documents)
    for dirpath, dirnames, _ in os.walk(root):
        for dirname in dirnames:
            path = os.path.join(dirpath, dirname)
            _add_document_from_path(path, root, documents)

    # Build the tree
    if not documents:
        logging.warning("no documents found in: {}".format(root))
    logging.info("building tree...")
    tree = Tree.from_list(documents, root=root)
    logging.info("built tree: {}".format(tree))
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
