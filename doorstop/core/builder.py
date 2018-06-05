"""Functions to build a tree and access documents and items."""

import os

from doorstop import common
from doorstop.common import DoorstopError
from doorstop.core import vcs
from doorstop.core.tree import Tree
from doorstop.core.document import Document

log = common.logger(__name__)


def build(should_auto_save, cwd=None, root=None, request_next_number=None):
    """Build a tree from the current working directory or explicit root.

    :param cwd: current working directory
    :param root: path to root of the working copy
    :param request_next_number: server method to get a document's next number

    :raises: :class:`~doorstop.common.DoorstopError` when the tree
        cannot be built

    :return: new :class:`~doorstop.core.tree.Tree`

    """
    documents = []

    # Find the root of the working copy
    cwd = cwd or os.getcwd()
    root = root or vcs.find_root(cwd)

    # Find all documents in the working copy
    log.info("looking for documents in {}...".format(root))
    _document_from_path(root, root, documents, should_auto_save=should_auto_save)
    for dirpath, dirnames, _ in os.walk(root):
        for dirname in dirnames:
            path = os.path.join(dirpath, dirname)
            _document_from_path(path, root, documents, should_auto_save=should_auto_save)

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


def _document_from_path(path, root, documents, should_auto_save):
    """Attempt to create and append a document from the specified path.

    :param path: path to a potential document
    :param root: path to root of working copy
    :param documents: list of :class:`~doorstop.core.document.Document`
        to append results

    """
    try:
        document = Document(path=path, should_auto_save=should_auto_save, root=root, tree=None)  # tree attached later
    except DoorstopError:
        pass  # no document in directory
    else:
        if document.skip:
            log.debug("skipped document: {}".format(document))
        else:
            log.info("found document: {}".format(document))
            documents.append(document)
