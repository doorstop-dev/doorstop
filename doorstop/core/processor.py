#!/usr/bin/env python

"""
Compiles the Doorstop document hierarchy.
"""

import os
import logging
from itertools import chain

from doorstop.core import Document
from doorstop.core import vcs


class Node(object):
    """
    A bidirectional tree structure to store the document heirarchy.

    Although requirements link "upwards", bidirectionality simplifies
    document processing and validation.
    """

    def __init__(self, document, parent=None):
        self.document = document
        self.parent = parent
        self.children = []

    def __repr__(self):
        return "<Node {}>".format(self)

    def __str__(self):
        children = ", ".join(str(c) for c in self.children)
        if children:
            return "{} <- [ {} ]".format(self.document, children)
        else:
            return "{}".format(self.document)

    def __len__(self):
        return 1 + sum(len(child) for child in self.children)

    def __getitem__(self, key):
        raise IndexError("{} cannot be indexed by key".format(self.__class__))

    def __iter__(self):
        yield self.document
        for document in chain(*(iter(c) for c in self.children)):
            yield document

    @staticmethod
    def from_list(docs):  # TODO: make this a Tree class?
        """Get a new tree from the list of Documents.

        @param documents: list of Documents
        @return: tree built from Nodes
        @raise ValueError: when the tree cannot be built
        """
        unplaced = list(docs)
        for doc in list(unplaced):
            if doc.parent is None:
                logging.debug("root document: {}".format(doc))
                tree = Node(doc)
                logging.info("started tree at: {}".format(doc))
                unplaced.remove(doc)
                break
        else:
            raise ValueError("no root document")

        while unplaced:
            count = len(unplaced)
            for doc in list(unplaced):
                try:
                    tree.add(doc)
                except ValueError as error:
                    logging.debug(error)
                else:
                    logging.info("added to tree: {}".format(doc))
                    unplaced.remove(doc)

            if len(unplaced) == count:  # no more documents could be placed
                for doc in unplaced:
                    logging.error("unplaced document: {}".format(doc))
                raise ValueError("unplaced document: {}".format(unplaced[0]))

        return tree

    def add(self, doc):
        """Attempt to add the Document to the current tree.

        @param doc: Document to add
        @raise TypeError: if the Document cannot yet be placed
        """
        logging.debug("trying to add '{}'...".format(doc))
        if doc.parent == self.document.prefix:
            node = Node(doc, self)
            self.children.append(node)
        else:
            for child in self.children:
                try:
                    child.add(doc)
                except TypeError:
                    pass
                else:
                    break
            else:
                msg = "no parent ({}) for: {}".format(doc.parent, doc)
                raise ValueError(msg)

    def validate(self):
        """Confirm the document hiearchy is valid.

        @raise ValueError: on issue
        """
        pass  # TODO: implement method


def run(cwd):
    """Build a document hiearchy and validate it.

    @param cwd: current working directory
    @return: indicates documents are valid
    """
    try:
        tree = build(cwd)
    except ValueError as error:
        logging.error(error)
        return False
    else:
        tree.validate()  # TODO: surround with try...except
        return True


def build(cwd):
    """Build a document heirachy from the current root directory.

    @param cwd: current working directory
    @return: tree built from Nodes
    @raise ValueError: when the tree cannot be built
    """
    documents = []

    # Find the root of the working copy
    root = vcs.find_root(cwd)

    # Find all documents in the working copy
    logging.debug("looking for documents in {}...".format(root))
    for dirpath, dirnames, _ in os.walk(cwd):
        for dirname in dirnames:
            path = os.path.join(dirpath, dirname)
            try:
                document = Document(path, root)
            except ValueError:
                pass  # no document in directory
            else:
                if document.skip:
                    logging.info("skipping document: {}".format(document))
                else:
                    logging.info("found document: {}".format(document))
                    documents.append(document)

    tree = Node.from_list(documents)
    logging.info("final tree: {}".format(tree))
    return tree
