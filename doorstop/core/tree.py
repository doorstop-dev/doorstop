"""Representation of a hierarchy of documents."""

from itertools import chain
import logging

from doorstop.common import DoorstopError, DoorstopWarning
from doorstop.core.base import BaseValidatable
from doorstop.core.base import clear_document_cache, clear_item_cache
from doorstop.core.types import Prefix, ID
from doorstop.core.document import Document
from doorstop.core import vcs
from doorstop.core import editor


class Tree(BaseValidatable):  # pylint: disable=R0902

    """A bidirectional tree structure to store the hierarchy of documents.

    Although requirements link "upwards", bidirectionality simplifies
    document processing and validation.

    """

    @staticmethod
    def from_list(documents, root=None):
        """Initialize a new tree from a list of documents.

        @param documents: list of Documents
        @param root: path to root of the project

        @raise DoorstopError: when the tree cannot be built

        @return: new Tree

        """
        if not documents:
            return Tree(document=None, root=root)
        unplaced = list(documents)
        for document in list(unplaced):
            if document.parent is None:
                logging.info("root of the tree: {}".format(document))
                tree = Tree(document)
                document.tree = tree
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
                    document.tree = tree
                    unplaced.remove(document)

            if len(unplaced) == count:  # no more documents could be placed
                logging.debug("unplaced documents: {}".format(unplaced))
                msg = "unplaced document: {}".format(unplaced[0])
                raise DoorstopError(msg)

        return tree

    def __init__(self, document, parent=None, root=None):
        self.document = document
        self.root = root or document.root  # enables mock testing
        self.parent = parent
        self.children = []
        self._vcs = None
        self._loaded = False
        self._item_cache = {}
        self._document_cache = {}

    def __repr__(self):
        return "<Tree {}>".format(self)

    def __str__(self):
        # Build parent prefix string (enables mock testing)
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

    def _place(self, document):
        """Attempt to place the document in the current tree.

        @param document: Document to add

        @raise DoorstopError: if the document cannot yet be placed

        """
        logging.debug("trying to add '{}'...".format(document))
        if not self.document:  # tree is empty

            if document.parent:
                msg = "unknown parent for {}: {}".format(document,
                                                         document.parent)
                raise DoorstopError(msg)
            self.document = document

        elif document.parent:  # tree has documents, document has parent

            if document.parent.lower() == self.document.prefix.lower():

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

        else:  # tree has documents, but no parent specified for document

            msg = "no parent specified for {}".format(document)
            logging.info(msg)
            prefixes = ', '.join(document.prefix for document in self)
            logging.info("parent options: {}".format(document, prefixes))
            raise DoorstopError(msg)

    # attributes #############################################################

    @property
    def documents(self):
        """Get an list of documents in the tree."""
        return list(self)

    @property
    def vcs(self):
        """Get the working copy."""
        if self._vcs is None:
            self._vcs = vcs.load(self.root)
        return self._vcs

    # actions ################################################################

    @clear_document_cache
    @clear_item_cache
    def create_document(self, path, value, sep=None, digits=None, parent=None):  # pylint: disable=R0913
        """Create a new document and add it to the tree.

        @param path: directory path for the new document
        @param value: document or prefix
        @param sep: separator between prefix and numbers
        @param digits: number of digits for the document's numbers
        @param parent: parent document's prefix

        @raise DoorstopError: if the document cannot be created

        @return: newly created and placed Document

        """
        prefix = Prefix(value)
        document = Document.new(self,
                                path, self.root, prefix, sep=sep,
                                digits=digits, parent=parent)
        try:
            self._place(document)
        except DoorstopError:
            msg = "deleting unplaced directory {}...".format(document.path)
            logging.debug(msg)
            document.delete()
            raise
        else:
            logging.info("added to tree: {}".format(document))
        return document

    @clear_item_cache
    def add_item(self, value, level=None, reorder=True):
        """Add a new item to an existing document by prefix.

        @param value: document or prefix
        @param level: desired item level
        @param reorder: update levels of document items

        @raise DoorstopError: if the item cannot be created

        @return: newly created Item

        """
        prefix = Prefix(value)
        document = self.find_document(prefix)
        self.vcs.lock(document.config)  # prevents duplicate item IDs
        item = document.add_item(level=level, reorder=reorder)
        return item

    @clear_item_cache
    def remove_item(self, value, reorder=True):
        """Remove an item from a document by ID.

        @param value: item or ID
        @param reorder: update levels of document items

        @raise DoorstopError: if the item cannot be removed

        @return: removed Item

        """
        identifier = ID(value)
        for document in self:
            try:
                document.find_item(identifier)
            except DoorstopError:
                pass  # item not found in that document
            else:
                item = document.remove_item(identifier, reorder=reorder)
                return item

        raise DoorstopError(ID.UNKNOWN_MESSAGE.format(k='', i=identifier))

    def link_items(self, cid, pid):
        """Add a new link between two items by IDs.

        @param cid: child item's ID (or child item)
        @param pid: parent item's ID (or parent item)

        @raise DoorstopError: if the link cannot be created

        @return: child Item, parent Item

        """
        logging.info("linking {} to {}...".format(cid, pid))
        # Find child item
        child = self.find_item(cid, _kind='child')
        # Find parent item
        parent = self.find_item(pid, _kind='parent')
        # Add link
        child.link(parent.id)
        return child, parent

    def unlink_items(self, cid, pid):
        """Remove a link between two items by IDs.

        @param cid: child item's ID (or child item)
        @param pid: parent item's ID (or parent item)

        @raise DoorstopError: if the link cannot be removed

        @return: child Item, parent Item

        """
        logging.info("unlinking '{}' from '{}'...".format(cid, pid))
        # Find child item
        child = self.find_item(cid, _kind='child')
        # Find parent item
        parent = self.find_item(pid, _kind='parent')
        # Remove link
        child.unlink(parent.id)
        return child, parent

    def edit_item(self, identifier, tool=None, launch=False):
        """Open an item for editing by ID.

        @param identifier: item's ID (or item)
        @param tool: alternative text editor to open the item
        @param launch: open the text editor

        @raise DoorstopError: if the item cannot be found

        @return: edited Item

        """
        logging.debug("looking for {}...".format(identifier))
        # Find item
        item = self.find_item(identifier)
        # Lock the item
        self.vcs.lock(item.path)
        # Open item
        if launch:
            editor.launch(item.path, tool=tool)
            # TODO: force an item reload without touching a private attribute
            item._loaded = False  # pylint: disable=W0212
        # Return the item
        return item

    def find_document(self, value):
        """Get a document by its prefix.

        @param value: document or prefix

        @raise DoorstopError: if the document cannot be found

        @return: matching Document

        """
        prefix = Prefix(value)
        logging.debug("looking for document '{}'...".format(prefix))
        try:
            document = self._document_cache[prefix]
            if document:
                logging.debug("found cached document: {}".format(document))
                return document
            else:
                logging.debug("found cached unknown: {}".format(prefix))
        except KeyError:
            for document in self:
                if document.prefix.lower() == prefix.lower():
                    logging.debug("found document: {}".format(document))
                    self._document_cache[prefix] = document
                    return document
            logging.debug("could not find document: {}".format(prefix))
            self._document_cache[prefix] = None

        raise DoorstopError(Prefix.UNKNOWN_MESSGE.format(prefix))

    def find_item(self, value, _kind=''):
        """Get an item by its ID.

        @param value: item or ID

        @raise DoorstopError: if the item cannot be found

        @return: matching Item

        """
        identifier = ID(value)
        _kind = (' ' + _kind) if _kind else _kind  # for logging messages
        logging.debug("looking for{} item '{}'...".format(_kind, identifier))
        try:
            item = self._item_cache[identifier]
            if item:
                logging.debug("found cached item: {}".format(item))
                return item
            else:
                logging.debug("found cached unknown: {}".format(identifier))
        except KeyError:
            for document in self:
                try:
                    item = document.find_item(identifier, _kind=_kind)
                except DoorstopError:
                    pass  # item not found in that document
                else:
                    logging.debug("found item: {}".format(item))
                    self._item_cache[identifier] = item
                    return item
            logging.debug("could not find item: {}".format(identifier))
            self._item_cache[identifier] = None

        raise DoorstopError(ID.UNKNOWN_MESSAGE.format(k=_kind, i=identifier))

    def get_issues(self, document_hook=None, item_hook=None):
        """Yield all the tree's issues.

        @param document_hook: function to call for custom document validation
        @param item_hook: function to call for custom item validation

        @return: generator of DoorstopError, DoorstopWarning, DoorstopInfo

        """
        hook = document_hook if document_hook else lambda **kwargs: []
        documents = list(self)
        # Check for documents
        if not documents:
            yield DoorstopWarning("no documents")
        # Check each document
        for document in documents:
            for issue in chain(hook(document=document, tree=self),
                               document.get_issues(item_hook=item_hook)):
                # Prepend the document's prefix to yielded exceptions
                if isinstance(issue, Exception):
                    yield type(issue)("{}: {}".format(document.prefix, issue))

    @clear_document_cache
    @clear_item_cache
    def load(self, reload=False):
        """Load the tree's documents and items.

        Unlike the Document and Item class, this load method is not
        used internally. Its purpose is to force the loading of
        content in large trees where lazy loading may be too slow.

        """
        if self._loaded and not reload:
            return
        logging.info("loading the tree...")
        for document in self:
            document.load(reload=True)
        # Set meta attributes
        self._loaded = True

    def delete(self):
        """Delete the tree and its documents and items."""
        for document in self:
            document.delete()
        self.document = None
        self.children = []
