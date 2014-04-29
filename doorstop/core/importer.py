"""Functions to import exiting documents and items to the Doorstop format."""

import logging

from doorstop.core.tree import build
from doorstop.core.document import Document
from doorstop.core.item import Item
from doorstop import common
from doorstop.common import DoorstopError


_documents = []  # cache of unpalced documents, pylint: disable=C0103


def new_document(prefix, path, parent=None):
    """Create a Doorstop document from existing document information.

    @param prefix: existing document's prefix (for new items)
    @param path: new directory path to store this document's items
    @param parent: parent document's prefix (if one will exist)

    @return: imported Document

    """
    # Load the current tree, pylint: disable=W0212
    if common._tree is None:
        common._tree = build()

    # Attempt to create a document with the given parent
    logging.info("importing document '{}'...".format(prefix))
    try:
        document = common._tree.new_document(path, prefix, parent=parent)
    except DoorstopError as exc:
        if not parent:
            raise exc from None

        # Create the document despite an unavailable parent
        document = Document.new(path, common._tree.root, prefix, parent=parent)
        logging.warning(exc)
        _documents.append(document)

    # TODO: attempt to place unplaced documents?

    logging.info("imported: {}".format(document))
    common._tree._document_cache[document.prefix] = document
    return document


def add_item(prefix, identifier, attrs=None):
    """Create a Doorstop document from existing document information.

    @param prefix: previously imported document's prefix
    @param identifier: existing item's unique ID
    @param attrs: dictionary of Doorstop and custom attributes

    @return: imported Item

    """
    # Load the current tree, pylint: disable=W0212
    if common._tree is None:
        common._tree = build()

    # Get the specified document
    document = common._tree.find_document(prefix)

    logging.info("importing item '{}'...".format(identifier))
    item = Item.new(document.path, document.root, identifier, auto=False)
    for key, value in (attrs or {}).items():
        item.set(key, value)
    item.save()

    logging.info("imported: {}".format(item))
    document._items.append(item)
    common._tree._item_cache[item.id] = item

    return item
