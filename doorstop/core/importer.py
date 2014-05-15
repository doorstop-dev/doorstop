"""Functions to import exiting documents and items to the Doorstop format."""

import logging

from doorstop.core.tree import _get_tree
from doorstop.core.document import Document
from doorstop.core.item import Item
from doorstop.common import DoorstopError


_documents = []  # cache of unplaced documents, pylint: disable=C0103


def new_document(prefix, path, parent=None):
    """Create a Doorstop document from existing document information.

    @param prefix: existing document's prefix (for new items)
    @param path: new directory path to store this document's items
    @param parent: parent document's prefix (if one will exist)

    @return: imported Document

    """
    # Load the current tree
    tree = _get_tree()

    # Attempt to create a document with the given parent
    logging.info("importing document '{}'...".format(prefix))
    try:
        document = tree.new_document(path, prefix, parent=parent)
    except DoorstopError as exc:
        if not parent:
            raise exc from None

        # Create the document despite an unavailable parent
        document = Document.new(tree,
                                path, tree.root, prefix,
                                parent=parent)
        logging.warning(exc)
        _documents.append(document)

    # TODO: attempt to place unplaced documents?

    # Cache and return the document
    logging.info("imported: {}".format(document))
    tree._document_cache[document.prefix] = document  # pylint: disable=W0212
    return document


def add_item(prefix, identifier, attrs=None):
    """Create a Doorstop document from existing document information.

    @param prefix: previously imported document's prefix
    @param identifier: existing item's unique ID
    @param attrs: dictionary of Doorstop and custom attributes

    @return: imported Item

    """
    # Load the current tree
    tree = _get_tree()

    # Get the specified document
    document = tree.find_document(prefix)

    logging.info("importing item '{}'...".format(identifier))
    item = Item.new(tree, document,
                    document.path, document.root, identifier,
                    auto=False)
    for key, value in (attrs or {}).items():
        item.set(key, value)
    item.save()

    # Cache and return the item
    logging.info("imported: {}".format(item))
    document._items.append(item)  # pylint: disable=W0212
    tree._item_cache[item.id] = item  # pylint: disable=W0212
    return item
