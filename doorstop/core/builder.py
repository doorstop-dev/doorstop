# SPDX-License-Identifier: LGPL-3.0-only

"""Functions to build a tree and access documents and items."""

import os
from typing import List, Optional

from doorstop import common
from doorstop.common import DoorstopError
from doorstop.core import vcs
from doorstop.core.document import Document
from doorstop.core.tree import Tree

log = common.logger(__name__)
_tree: Optional[Tree] = None  # implicit tree for convenience functions


def build(cwd=None, root=None, request_next_number=None) -> Tree:
    """Build a tree from the current working directory or explicit root.

    :param cwd: current working directory
    :param root: path to root of the working copy
    :param request_next_number: server method to get a document's next number

    :raises: :class:`~doorstop.common.DoorstopError` when the tree
        cannot be built

    :return: new :class:`~doorstop.core.tree.Tree`

    """
    documents: List[Document] = []

    # Find the root of the working copy
    cwd = cwd or os.getcwd()
    root = root or vcs.find_root(cwd)

    # Find all documents in the working copy
    log.info("looking for documents in {}...".format(root))
    skip_file_name = '.doorstop.skip-all'
    if not os.path.isfile(os.path.join(root, skip_file_name)):
        _document_from_path(root, root, documents)
    exclude_dirnames = {'.git', '.venv', 'venv'}
    if not os.path.isfile(os.path.join(root, skip_file_name)):
        for dirpath, dirnames, _ in os.walk(root, topdown=True):
            whilelist_dirnames = []
            for dirname in dirnames:
                if dirname in exclude_dirnames:
                    continue
                path = os.path.join(dirpath, dirname)
                if os.path.isfile(os.path.join(path, skip_file_name)):
                    continue
                whilelist_dirnames.append(dirname)
                _document_from_path(path, root, documents)
            dirnames[:] = whilelist_dirnames

    # Build the tree
    if not documents:
        log.info("no documents found in: {}".format(root))
    log.info("building tree...")
    tree = Tree.from_list(documents, root=root)
    tree.request_next_number = request_next_number
    if len(tree):  # pylint: disable=len-as-condition
        log.info("built tree: {}".format(tree))
    else:
        log.info("tree is empty")
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
            log.debug("skipped document: {}".format(document))
        else:
            log.info("found document: {}".format(document))
            documents.append(document)


def find_document(prefix):
    """Find a document without an explicitly building a tree."""
    tree = _get_tree()
    document = tree.find_document(prefix)
    return document


def find_item(uid):
    """Find an item without an explicitly building a tree."""
    tree = _get_tree()
    item = tree.find_item(uid)
    return item


def _get_tree(request_next_number=None):
    """Get a shared tree for convenience functions."""
    global _tree
    if _tree is None:
        _tree = build()
    _tree.request_next_number = request_next_number
    return _tree


def _set_tree(value):
    """Set the shared tree to a specific value (for testing)."""
    global _tree
    _tree = value


def _clear_tree():
    """Force the shared tree to be rebuilt."""
    global _tree
    _tree = None
