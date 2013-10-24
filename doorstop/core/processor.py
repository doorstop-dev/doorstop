#!/usr/bin/env python

"""
Compiles the Doorstop document hierarchy.
"""

import os
import logging

from doorstop.core import Document


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

    def add(self, document):
        """Attempt to add the Document to the current tree.

        @param document: Document to add
        @raise TypeError: if the Document cannot yet be placed
        """
        if document.parent == self.document.prefix:
            node = Node(document, self)
            self.children.append(node)
        else:
            for child in self.children:
                try:
                    child.add(document)
                except TypeError:
                    pass
                else:
                    break
            else:
                raise TypeError("no parent for {}".format(document))

    @staticmethod
    def from_list(documents):
        """Get a new tree from the list of Documents.

        @param documents: list of Documents
        @return: tree built from Nodes
        """
        for document in documents:
            if document.parent is None:
                tree = Node(document)
                break
        else:
            raise ValueError("no root document")

        while documents:
            count = len(tree)
            for document in documents:
                try:
                    tree.add(document)
                except ValueError as error:
                    logging.debug(error)
            if not len(tree) > count:
                unplaced = [doc for doc in documents if doc not in tree]
                raise ValueError("unplaced documents: {}".format(unplaced))

        return tree


def build(cwd):
    """Build a document heirachy from the current root directory.

    @param cwd: current working directory
    """
    documents = []

    for dirpath, dirnames, _ in os.walk(cwd):
        logging.debug("looking for documents in {}...".format(dirpath))
        for dirname in dirnames:
            path = os.path.join(dirpath, dirname)
            try:
                document = Document(path)
            except ValueError as error:
                logging.debug(error)
            else:
                documents.append(document)

    tree = Node.from_list(documents)
    return tree


def run(cwd):
    """Main entry point for the program.

    @param cwd: current working directory
    """
    raise NotImplementedError()
