"""
Compiles the Doorstop document hierarchy.
"""

import os
import sys
import shutil
import subprocess
import logging
from itertools import chain

from doorstop.common import DoorstopError, DoorstopWarning, DoorstopInfo
from doorstop.core.document import Document
from doorstop.core import vcs


class Tree(object):
    """A bidirectional tree structure to store the hierarchy of documents.

    Although requirements link "upwards", bidirectionality simplifies
    document processing and validation.
    """

    def __init__(self, document, parent=None, root=None):
        self.document = document
        self.root = root or document.root  # allows non-documents in tests
        self.parent = parent
        self.children = []
        self._vcs = None

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
    def from_list(documents, root=None):
        """Get a new tree from a list of documents.

        @param documents: list of Documents
        @param root: path to root of the project

        @return: new Tree

        @raise DoorstopError: when the tree cannot be built
        """
        if not documents:
            return Tree(document=None, root=root)
        unplaced = list(documents)
        for document in list(unplaced):
            if document.parent is None:
                logging.debug("added root of tree: {}".format(document))
                tree = Tree(document)
                logging.info("root of the tree: {}".format(document))
                unplaced.remove(document)
                break
        else:
            raise DoorstopError("no root document")

        while unplaced:
            count = len(unplaced)
            for document in list(unplaced):
                if document.parent is None:
                    logging.info("root of the tree: {}".format(document))
                    raise DoorstopError("multiple root documents")
                try:
                    tree._place(document)  # pylint: disable=W0212
                except DoorstopError as error:
                    logging.debug(error)
                else:
                    logging.info("added to tree: {}".format(document))
                    unplaced.remove(document)

            if len(unplaced) == count:  # no more documents could be placed
                logging.debug("unplaced documents: {}".format(unplaced))
                msg = "unplaced document: {}".format(unplaced[0])
                raise DoorstopError(msg)

        return tree

    def _place(self, document):
        """Attempt to place the document in the current tree.

        @param document: Document to add

        @raise DoorstopError: if the document cannot yet be placed
        """
        logging.debug("trying to add '{}'...".format(document))
        if not self.document:

            # Tree is empty
            if document.parent:
                msg = "unknown parent for {}: {}".format(document,
                                                         document.parent)
                raise DoorstopError(msg)
            self.document = document

        elif (document.parent and
              document.parent.lower() == self.document.prefix.lower()):

            # Current document is the parent
            node = Tree(document, self)
            self.children.append(node)

        else:

            # Search for the parent
            for child in self.children:
                try:
                    child._place(document)  # pylint: disable=W0212
                except DoorstopError:
                    pass  # the error is raised later
                else:
                    break
            else:
                msg = "unknown parent for {}: {}".format(document,
                                                         document.parent)
                raise DoorstopError(msg)

    # attributes #############################################################

    @property
    def vcs(self):
        """Get the working copy."""
        if self._vcs is None:
            self._vcs = vcs.load(self.root)
        return self._vcs

    # actions ################################################################

    def new(self, path, prefix, sep=None, digits=None, parent=None):  # pylint: disable=R0913
        """Create a new document and add it to the tree.

        @param path: directory path for the new document
        @param prefix: document's prefix
        @param sep: separator between prefix and numbers
        @param digits: number of digits for the document's numbers
        @param parent: parent document's prefix

        @return: newly created and placed Document

        @raise DoorstopError: if the document cannot be created
        """
        document = Document.new(path, self.root, prefix,
                                sep=sep, digits=digits,
                                parent=parent)
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
        """Add a new item to an existing document by prefix.

        @param prefix: document's prefix

        @return: newly created Item

        @raise DoorstopError: if the item cannot be created
        """
        document = self.find_document(prefix)
        self.vcs.lock(document.config)  # prevents duplicate item IDs
        item = document.add()
        return item

    def remove(self, identifier):
        """Remove an item from a document by ID.

        @param identifier: item's ID

        @return: removed Item

        @raise DoorstopError: if the item cannot be removed
        """
        for document in self:
            try:
                document.find_item(identifier)
            except DoorstopError:
                pass  # item not found in that document
            else:
                item = document.remove(identifier)
                return item

        raise DoorstopError("no matching ID: {}".format(identifier))

    def link(self, cid, pid):
        """Add a new link between two items by IDs.

        @param cid: child item's ID
        @param pid: parent item's ID

        @return: child Item, parent Item

        @raise DoorstopError: if the link cannot be created
        """
        logging.info("linking {} to {}...".format(cid, pid))
        # Find child item
        child = self.find_item(cid, _kind='child')
        # Find parent item
        parent = self.find_item(pid, _kind='parent')
        # Add link
        child.add_link(parent.id)
        return child, parent

    def unlink(self, cid, pid):
        """Remove a link between two items by IDs.

        @param cid: child item's ID
        @param pid: parent item's ID

        @return: child Item, parent Item

        @raise DoorstopError: if the link cannot be removed
        """
        logging.info("unlinking {} from {}...".format(cid, pid))
        # Find child item
        child = self.find_item(cid, _kind='child')
        # Find parent item
        parent = self.find_item(pid, _kind='parent')
        # Remove link
        child.remove_link(parent.id)
        return child, parent

    def edit(self, identifier, tool=None, launch=False):
        """Open an item for editing by ID.

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
            # TODO: force the item to reload after editing
            item._loaded = False  # pylint: disable=W0212
        # Return the item
        return item

    def find_document(self, prefix):
        """Get a document by its prefix.

        @param prefix: document's prefix

        @return: matching Document

        @raise DoorstopError: if the document cannot be found
        """
        for document in self:
            if document.prefix.lower() == prefix.lower():
                return document

        raise DoorstopError("no matching prefix: {}".format(prefix))

    def find_item(self, identifier, _kind=''):
        """Get an item by its ID.

        @param identifier: item ID

        @return: matching Item

        @raise DoorstopError: if the item cannot be found
        """
        _kind = (' ' + _kind) if _kind else _kind  # for logging messages
        for document in self:
            try:
                return document.find_item(identifier, _kind=_kind)
            except DoorstopError:
                pass  # item not found in that document

        raise DoorstopError("no matching{} ID: {}".format(_kind, identifier))

    def valid(self):
        """Check the tree (and its documents) for validity.

        @return: indication that the tree is valid
        """
        valid = True
        logging.info("checking tree...")
        # Display all issues
        for issue in self.issues():
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

    def issues(self):
        """Yield all the tree's issues.

        @return: generator of DoorstopError, DoorstopWarning, DoorstopInfo
        """
        documents = list(self)
        # Check for documents
        if not documents:
            yield DoorstopWarning("no documents")
        # Check each document
        for document in documents:
            for issue in document.issues(tree=self):
                # Prepend the document's prefix
                yield type(issue)("{}: {}".format(document.prefix, issue))


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
    """Build a tree from the current working directory or explicit root.

    @param cwd: current working directory
    @param root: path to root of the working copy

    @return: new Tree

    @raise DoorstopError: when the tree cannot be built
    """
    documents = []

    # Find the root of the working copy
    cwd = cwd or os.getcwd()
    root = root or vcs.find_root(cwd)

    # Find all documents in the working copy
    logging.info("looking for documents in {}...".format(root))
    _document_from_path(root, root, documents)
    for dirpath, dirnames, _ in os.walk(root):
        for dirname in dirnames:
            path = os.path.join(dirpath, dirname)
            _document_from_path(path, root, documents)

    # Build the tree
    if not documents:
        logging.info("no documents found in: {}".format(root))
    logging.info("building tree...")
    tree = Tree.from_list(documents, root=root)
    logging.info("built tree: {}".format(tree))
    return tree


def _document_from_path(path, root, documents):
    """Attempt to create and append a document from the specified path.

    @param path: path to a potential document
    @param root: path to root of working copy
    @param documents: list of Documents to append results
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
