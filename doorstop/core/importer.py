"""Functions to import exiting documents and items to the Doorstop format."""

import logging

from doorstop.core.tree import build
from doorstop.core.document import Document
from doorstop.core.item import Item
from doorstop.common import DoorstopError


_TREE = None  # implicitly created tree created for convenience functions
_DOCUMENTS = []  # documents that could not be added to the tree


def new_document(prefix, path, parent=None):
    """Create a Doorstop document from existing document information.

    @param prefix: existing document's prefix (for new items)
    @param path: new directory path to store this document's items
    @param parent: parent document's prefix (if one will exist)

    @return: imported Document

    """
    # Load the current tree
    global _TREE  # pylint: disable=W0603
    if _TREE is None:
        _TREE = build()

    # Attempt to create a document with the given parent
    try:
        document = _TREE.new_document(path, prefix, parent=parent)
    except DoorstopError as exc:
        if not parent:
            raise exc from None

        # Create the document despite an unavailable parent
        document = Document.new(path, _TREE.root, prefix, parent=parent)
        logging.warning(exc)
        _DOCUMENTS.append(document)

    # TODO: attempt to place unplaced documents?

    return document


def add_item(prefix, identifier, attrs=None):
    """Create a Doorstop document from existing document information.

    @param prefix: previously imported document's prefix
    @param identifier: existing item's unique ID
    @param attrs: dictionary of Doorstop and custom attributes

    @return: imported Item

    """
    # Load the current tree
    global _TREE  # pylint: disable=W0603
    if _TREE is None:
        _TREE = build()

    # Get the specified document
    document = _TREE.find_document(prefix)

    item = Item.new(document.path, document.root, identifier, auto=False)
    for key, value in (attrs or {}).items():
        item.set(key, value)
    item.save()

    return item
