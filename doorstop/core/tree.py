#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-3.0-only

"""Representation of a hierarchy of documents."""

import sys
from itertools import chain
from typing import Dict, List, Optional

from doorstop import common, settings
from doorstop.common import DoorstopError, DoorstopWarning
from doorstop.core import vcs
from doorstop.core.base import BaseValidatable
from doorstop.core.document import Document
from doorstop.core.item import Item
from doorstop.core.types import UID, Prefix

UTF8 = 'utf-8'
CP437 = 'cp437'
ASCII = 'ascii'

BOX = {
    'end': {UTF8: '│   ', CP437: '┬   ', ASCII: '|   '},
    'tee': {UTF8: '├── ', CP437: '├── ', ASCII: '+-- '},
    'bend': {UTF8: '└── ', CP437: '└── ', ASCII: '+-- '},
    'pipe': {UTF8: '│   ', CP437: '│   ', ASCII: '|   '},
    'space': {UTF8: '    ', CP437: '    ', ASCII: '    '},
}

log = common.logger(__name__)


class Tree(BaseValidatable):  # pylint: disable=R0902
    """A bidirectional tree structure to store a hierarchy of documents.

    Although requirements link "upwards", bidirectionality simplifies
    document processing and validation.

    """

    @staticmethod
    def from_list(documents, root=None):
        """Initialize a new tree from a list of documents.

        :param documents: list of :class:`~doorstop.core.document.Document`
        :param root: path to root of the project

        :raises: :class:`~doorstop.common.DoorstopError` when the tree
            cannot be built

        :return: new :class:`~doorstop.core.tree.Tree`

        """
        if not documents:
            return Tree(document=None, root=root)
        unplaced = list(documents)
        for document in list(unplaced):
            if document.parent is None:
                log.info("root of the tree: {}".format(document))
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
                    log.info("root of the tree: {}".format(document))
                    message = "multiple root documents:\n- {}: {}\n- {}: {}".format(
                        tree.document.prefix,
                        tree.document.path,
                        document.prefix,
                        document.path,
                    )
                    raise DoorstopError(message)
                try:
                    tree._place(document)  # pylint: disable=W0212
                except DoorstopError as error:
                    log.debug(error)
                else:
                    log.info("added to tree: {}".format(document))
                    document.tree = tree
                    unplaced.remove(document)

            if len(unplaced) == count:  # no more documents could be placed
                log.debug("unplaced documents: {}".format(unplaced))
                msg = "unplaced document: {}".format(unplaced[0])
                raise DoorstopError(msg)

        return tree

    def __init__(self, document, parent=None, root=None):
        self.document = document
        self.root = root or document.root  # enables mock testing
        self.parent = parent
        self.children: List[Tree] = []
        self._vcs = None  # working copy reference loaded in a property
        self.request_next_number = None  # server method injected by clients
        self._loaded = False
        self._item_cache: Dict[str, Item] = {}
        self._document_cache: Dict[str, Optional[Document]] = {}

    def __repr__(self):
        return "<Tree {}>".format(self._draw_line())

    def __str__(self):
        return self._draw_line()

    def __len__(self):
        if self.document:
            return 1 + sum(len(child) for child in self.children)
        else:
            return 0

    def __bool__(self):
        """Even empty trees should be considered truthy."""
        return True

    def __getitem__(self, key):
        raise IndexError("{} cannot be indexed by key".format(self.__class__))

    def __iter__(self):
        if self.document:
            yield self.document
        yield from chain(*(iter(c) for c in self.children))

    def _place(self, document):
        """Attempt to place the document in the current tree.

        :param document: :class:`doorstop.core.document.Document` to add

        :raises: :class:`~doorstop.common.DoorstopError` if the document
            cannot yet be placed

        """
        log.debug("trying to add {}...".format(document))
        if not self.document:  # tree is empty

            if document.parent:
                msg = "unknown parent for {}: {}".format(document, document.parent)
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
                    msg = "unknown parent for {}: {}".format(document, document.parent)
                    raise DoorstopError(msg)

        else:  # tree has documents, but no parent specified for document

            msg = "no parent specified for {}".format(document)
            log.info(msg)
            prefixes = ', '.join(document.prefix for document in self)
            log.info("parent options: {}".format(prefixes))
            raise DoorstopError(msg)

        for document2 in self:
            children = self._get_prefix_of_children(document2)
            document2.children = children

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

    # decorators are applied to methods in the associated classes
    def create_document(
        self, path, value, sep=None, digits=None, parent=None
    ):  # pylint: disable=R0913
        """Create a new document and add it to the tree.

        :param path: directory path for the new document
        :param value: document or prefix
        :param sep: separator between prefix and numbers
        :param digits: number of digits for the document's numbers
        :param parent: parent document's prefix

        :raises: :class:`~doorstop.common.DoorstopError` if the
            document cannot be created

        :return: newly created and placed document
            :class:`~doorstop.core.document.Document`

        """
        prefix = Prefix(value)

        # Check if a document with the same name already exists in the tree.
        for d in self.documents:
            if d.prefix == value:
                raise DoorstopError(
                    "The document name is already in use ({}).".format(d.path)
                )

        document = Document.new(
            self, path, self.root, prefix, sep=sep, digits=digits, parent=parent
        )
        try:
            self._place(document)
        except DoorstopError:
            msg = "deleting unplaced directory {}...".format(document.path)
            log.debug(msg)
            document.delete()
            raise
        else:
            log.info("added to tree: {}".format(document))
        return document

    # decorators are applied to methods in the associated classes
    def add_item(self, value, number=None, level=None, reorder=True):
        """Add a new item to an existing document by prefix.

        :param value: document or prefix
        :param number: desired item number
        :param level: desired item level
        :param reorder: update levels of document items

        :raises: :class:`~doorstop.common.DoorstopError` if the item
            cannot be created

        :return: newly created :class:`~doorstop.core.item.Item`

        """
        prefix = Prefix(value)
        document = self.find_document(prefix)
        item = document.add_item(number=number, level=level, reorder=reorder)
        return item

    # decorators are applied to methods in the associated classes
    def remove_item(self, value, reorder=True):
        """Remove an item from a document by UID.

        :param value: item or UID
        :param reorder: update levels of document items

        :raises: :class:`~doorstop.common.DoorstopError` if the item
            cannot be removed

        :return: removed :class:`~doorstop.core.item.Item`

        """
        uid = UID(value)
        for document in self:
            try:
                document.find_item(uid)
            except DoorstopError:
                pass  # item not found in that document
            else:
                item = document.remove_item(uid, reorder=reorder)
                return item

        raise DoorstopError(UID.UNKNOWN_MESSAGE.format(k='', u=uid))

    def check_for_cycle(self, item, cid, path):
        """Check if a cyclic dependency would be created.

        :param item: an item on the dependency path
        :param cid: the child item's UID
        :param path: the path of UIDs from the child item to the item

        :raises: :class:`~doorstop.common.DoorstopError` if the link
            would create a cyclic dependency
        """
        for did in item.links:
            path2 = path + [did]
            if did in path:
                s = " -> ".join(list(map(str, path2)))
                msg = "link would create a cyclic dependency: {}".format(s)
                raise DoorstopError(msg)
            dep = self.find_item(did, _kind='dependency')
            self.check_for_cycle(dep, cid, path2)

    # decorators are applied to methods in the associated classes
    def link_items(self, cid, pid):
        """Add a new link between two items by UIDs.

        :param cid: child item's UID (or child item)
        :param pid: parent item's UID (or parent item)

        :raises: :class:`~doorstop.common.DoorstopError` if the link
            cannot be created

        :return: child :class:`~doorstop.core.item.Item`,
                 parent :class:`~doorstop.core.item.Item`

        """
        log.info("linking {} to {}...".format(cid, pid))
        # Find child item
        child = self.find_item(cid, _kind='child')
        # Find parent item
        parent = self.find_item(pid, _kind='parent')
        # Add link if it is not a self reference or cyclic dependency
        if child is parent:
            raise DoorstopError("link would be self reference")
        self.check_for_cycle(parent, child.uid, [child.uid, parent.uid])
        child.link(parent.uid)
        return child, parent

    # decorators are applied to methods in the associated classes`
    def unlink_items(self, cid, pid):
        """Remove a link between two items by UIDs.

        :param cid: child item's UID (or child item)
        :param pid: parent item's UID (or parent item)

        :raises: :class:`~doorstop.common.DoorstopError` if the link
            cannot be removed

        :return: child :class:`~doorstop.core.item.Item`,
                 parent :class:`~doorstop.core.item.Item`

        """
        log.info("unlinking '{}' from '{}'...".format(cid, pid))
        # Find child item
        child = self.find_item(cid, _kind='child')
        # Find parent item
        parent = self.find_item(pid, _kind='parent')
        # Remove link
        child.unlink(parent.uid)
        return child, parent

    # decorators are applied to methods in the associated classes
    def edit_item(self, uid, tool=None, launch=False):
        """Open an item for editing by UID.

        :param uid: item's UID (or item)
        :param tool: alternative text editor to open the item
        :param launch: open the text editor

        :raises: :class:`~doorstop.common.DoorstopError` if the item
            cannot be found

        :return: edited :class:`~doorstop.core.item.Item`

        """
        # Find the item
        item = self.find_item(uid)
        # Edit the item
        if launch:
            item.edit(tool=tool)
        # Return the item
        return item

    def find_document(self, value) -> Document:
        """Get a document by its prefix.

        :param value: document or prefix

        :raises: :class:`~doorstop.common.DoorstopError` if the document
            cannot be found

        :return: matching :class:`~doorstop.core.document.Document`

        """
        prefix = Prefix(value)
        log.debug("looking for document '{}'...".format(prefix))
        try:
            document = self._document_cache[prefix]
            if document:
                log.trace("found cached document: {}".format(document))  # type: ignore
                return document
            else:
                log.trace("found cached unknown: {}".format(prefix))  # type: ignore
        except KeyError:
            for document in self:
                if not document:
                    # TODO: mypy seems to think document can be None here, but that shouldn't be possible
                    continue
                if document.prefix == prefix:
                    log.trace("found document: {}".format(document))  # type: ignore
                    if settings.CACHE_DOCUMENTS:
                        self._document_cache[prefix] = document
                        log.trace(  # type: ignore
                            "cached document: {}".format(document)
                        )
                    return document
            log.debug("could not find document: {}".format(prefix))
            if settings.CACHE_DOCUMENTS:
                self._document_cache[prefix] = None
                log.trace("cached unknown: {}".format(prefix))  # type: ignore

        raise DoorstopError(Prefix.UNKNOWN_MESSAGE.format(prefix))

    def find_item(self, value, _kind=''):
        """Get an item by its UID.

        :param value: item or UID

        :raises: :class:`~doorstop.common.DoorstopError` if the item
            cannot be found

        :return: matching :class:`~doorstop.core.item.Item`

        """
        uid = UID(value)
        _kind = (' ' + _kind) if _kind else _kind  # for logging messages
        log.debug("looking for{} item '{}'...".format(_kind, uid))
        try:
            item = self._item_cache[uid]
            if item:
                log.trace("found cached item: {}".format(item))  # type: ignore
                if item.active:
                    return item
                else:
                    log.trace("item is inactive: {}".format(item))  # type: ignore
            else:
                log.trace("found cached unknown: {}".format(uid))  # type: ignore
        except KeyError:
            for document in self:
                try:
                    item = document.find_item(uid, _kind=_kind)
                except DoorstopError:
                    pass  # item not found in that document
                else:
                    log.trace("found item: {}".format(item))  # type: ignore
                    if settings.CACHE_ITEMS:
                        self._item_cache[uid] = item
                        log.trace("cached item: {}".format(item))  # type: ignore
                    if item.active:
                        return item
                    else:
                        log.trace("item is inactive: {}".format(item))  # type: ignore

            log.debug("could not find item: {}".format(uid))
            if settings.CACHE_ITEMS:
                self._item_cache[uid] = None
                log.trace("cached unknown: {}".format(uid))  # type: ignore

        raise DoorstopError(UID.UNKNOWN_MESSAGE.format(k=_kind, u=uid))

    def get_issues(self, skip=None, document_hook=None, item_hook=None):
        """Yield all the tree's issues.

        :param skip: list of document prefixes to skip
        :param document_hook: function to call for custom document validation
        :param item_hook: function to call for custom item validation

        :return: generator of :class:`~doorstop.common.DoorstopError`,
                              :class:`~doorstop.common.DoorstopWarning`,
                              :class:`~doorstop.common.DoorstopInfo`

        """
        hook = document_hook if document_hook else lambda **kwargs: []
        documents = list(self)
        # Check for documents
        if not documents:
            yield DoorstopWarning("no documents")
        # Check each document
        for document in documents:
            for issue in chain(
                hook(document=document, tree=self),
                document.get_issues(skip=skip, item_hook=item_hook),
            ):
                # Prepend the document's prefix to yielded exceptions
                if isinstance(issue, Exception):
                    yield type(issue)("{}: {}".format(document.prefix, issue))

    def get_traceability(self):
        """Return sorted rows of traceability slices.

        :return: list of list of :class:`~doorstop.core.item.Item` or `None`

        """

        def by_uid(row):
            row2 = []
            for item in row:
                if item:
                    row2.append('0' + str(item.uid))
                else:
                    row2.append('1')  # force `None` to sort after items
            return row2

        # Create mapping of document prefix to slice index
        mapping = {}
        for index, document in enumerate(self.documents):
            mapping[document.prefix] = index

        # Collect all rows
        rows = set()
        for index, document in enumerate(self.documents):
            for item in document:
                if item.active:
                    for row in self._iter_rows(item, mapping):
                        rows.add(row)

        # Sort rows
        return sorted(rows, key=by_uid)

    def _get_prefix_of_children(self, document):
        """Return the prefixes of the children of this document."""
        for child in self.children:
            if child.document == document:
                children = [c.document.prefix for c in child.children]
                return children
        children = [c.document.prefix for c in self.children]
        return children

    def _iter_rows(
        self, item, mapping, parent=True, child=True, row=None
    ):  # pylint: disable=R0913
        """Generate all traceability row slices.

        :param item: base :class:`~doorstop.core.item.Item` for slicing
        :param mapping: `dict` of document prefix to slice index
        :param parent: indicate recursion is in the parent direction
        :param child: indicates recursion is in the child direction
        :param row: currently generated row

        """

        class Row(list):
            """List type that tracks upper and lower boundaries."""

            def __init__(self, *args, parent=False, child=False, **kwargs):
                super().__init__(*args, **kwargs)
                # Flags to indicate upper and lower bounds have been hit
                self.parent = parent
                self.child = child

        if item.normative:

            # Start the next row or copy from recursion
            if row is None:
                row = Row([None] * len(mapping))
            else:
                row = Row(row, parent=row.parent, child=row.child)

            # Add the current item to the row
            row[mapping[item.document.prefix]] = item

            # Recurse to the next parent/child item
            if parent:
                items = item.parent_items
                for item2 in items:
                    yield from self._iter_rows(item2, mapping, child=False, row=row)
                if not items:
                    row.parent = True
            if child:
                items = item.child_items
                for item2 in items:
                    yield from self._iter_rows(item2, mapping, parent=False, row=row)
                if not items:
                    row.child = True

            # Yield the row if both boundaries have been hit
            if row.parent and row.child:
                yield tuple(row)

    def load(self, reload=False):
        """Load the tree's documents and items.

        Unlike the :class:`~doorstop.core.document.Document` and
        :class:`~doorstop.core.item.Item` class, this load method is not
        used internally. Its purpose is to force the loading of
        content in large trees where lazy loading may cause long delays
        late in processing.

        """
        if self._loaded and not reload:
            return
        log.info("loading the tree...")
        for document in self:
            document.load(reload=True)
        # Set meta attributes
        self._loaded = True

    def draw(self, encoding=None, html_links=False):
        """Get the tree structure as text.

        :param encoding: limit character set to:

            - `'utf-8'` - all characters
            - `'cp437'` - Code Page 437 characters
            - (other) - ASCII characters

        """
        encoding = encoding or getattr(sys.stdout, 'encoding', None)
        encoding = encoding.lower() if encoding else None
        return '\n'.join(self._draw_lines(encoding, html_links))

    def _draw_line(self):
        """Get the tree structure in one line."""
        # Build parent prefix string (`getattr` to enable mock testing)
        prefix = getattr(self.document, 'prefix', '') or str(self.document)
        # Build children prefix strings
        children = ", ".join(
            c._draw_line() for c in self.children  # pylint: disable=protected-access
        )
        # Format the tree
        if children:
            return "{} <- [ {} ]".format(prefix, children)
        else:
            return "{}".format(prefix)

    def _draw_lines(self, encoding, html_links=False):
        """Generate lines of the tree structure."""
        # Build parent prefix string (`getattr` to enable mock testing)
        prefix = getattr(self.document, 'prefix', '') or str(self.document)
        if html_links:
            prefix = '<a href="documents/{0}">{0}</a>'.format(prefix)
        yield prefix
        # Build child prefix strings
        for count, child in enumerate(self.children, start=1):
            if count == 1:
                yield self._symbol('end', encoding)
            else:
                yield self._symbol('pipe', encoding)
            if count < len(self.children):
                base = self._symbol('pipe', encoding)
                indent = self._symbol('tee', encoding)
            else:
                base = self._symbol('space', encoding)
                indent = self._symbol('bend', encoding)
            for index, line in enumerate(
                # pylint: disable=protected-access
                child._draw_lines(encoding, html_links)
            ):
                if index == 0:
                    yield indent + line
                else:
                    yield base + line

    @staticmethod
    def _symbol(name, encoding):
        """Get a drawing symbol based on encoding."""
        if encoding not in (UTF8, CP437):
            encoding = ASCII
        return BOX[name][encoding]

    # decorators are applied to methods in the associated classes
    def delete(self):
        """Delete the tree and its documents and items."""
        for document in self:
            document.delete()
        self.document = None
        self.children = []
