"""Functions to build a tree and access documents and items."""

import os
import logging

from doorstop.common import DoorstopError
from doorstop.core import vcs
from doorstop.core.tree import Tree
from doorstop.core.document import Document


_TREE = None  # implicit tree for convenience functions


def build(cwd=None, root=None):
    """Build a tree from the current working directory or explicit root.

    :param cwd: current working directory
    :param root: path to root of the working copy

    :raises: :class:`~doorstop.common.DoorstopError` when the tree
    `cannot be built

    :return: new :class:`~doorstop.core.tree.Tree`

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

    :param path: path to a potential document
    :param root: path to root of working copy
    :param documents: list of :class:`~doorstop.core.document.Document`
        to append results

    """
    try:
        document = Document(path, root, tree=None)  # tree attached later
    except DoorstopError:
        pass  # no document in directory
    else:
        if document.skip:
            logging.debug("skipping document: {}".format(document))
        else:
            logging.info("found document: {}".format(document))
            documents.append(document)


def find_document(prefix):
    """Find a document without an explicitly building a tree."""
    tree = _get_tree()
    document = tree.find_document(prefix)
    return document


def find_item(identifier):
    """Find an item without an explicitly building a tree."""
    tree = _get_tree()
    item = tree.find_item(identifier)
    return item


def _get_tree():
    """Get a shared tree for convenience functions."""
    global _TREE  # pylint: disable=W0603
    if _TREE is None:
        _TREE = build()
    return _TREE


def _set_tree(value):
    """Set the shared tree to a specific value (for testing)."""
    global _TREE  # pylint: disable=W0603
    _TREE = value


def _clear_tree():
    """Force the shared tree to be rebuilt."""
    global _TREE  # pylint: disable=W0603
    _TREE = None
