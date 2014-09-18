"""Representation of an item in a document."""

import os
import re
import functools

import yorm
import pyficache

from doorstop import common
from doorstop.common import DoorstopError, DoorstopWarning, DoorstopInfo
from doorstop.core.base import (add_item, edit_item, delete_item,
                                auto_load, auto_save,
                                BaseValidatable, BaseFileObject)
from doorstop.core.types import Prefix, UID, Text, Level, Stamp, to_bool
from doorstop.core import editor
from doorstop import settings

log = common.logger(__name__)


def requires_tree(func):
    """Decorator for methods that require a tree reference."""
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        """Wrapped method that requires a tree reference."""
        if not self.tree:
            name = func.__name__
            log.critical("`{}` can only be called with a tree".format(name))
            return None
        return func(self, *args, **kwargs)
    return wrapped


def requires_document(func):
    """Decorator for methods that require a document reference."""
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        """Wrapped method that requires a document reference."""
        if not self.document:
            name = func.__name__
            msg = "`{}` can only be called with a document".format(name)
            log.critical(msg)
            return None
        return func(self, *args, **kwargs)
    return wrapped


@yorm.map_attr(active=yorm.standard.Boolean)
@yorm.map_attr(derived=yorm.standard.Boolean)
@yorm.map_attr(level=Level)
@yorm.map_attr(links=yorm.standard.List)
@yorm.map_attr(normative=yorm.standard.Boolean)
@yorm.map_attr(ref=yorm.standard.String)
@yorm.map_attr(reviwed=Stamp)
@yorm.map_attr(text=Text)
@yorm.store_instances("{path}", {'path': 'path'})
class Item(BaseValidatable, BaseFileObject):  # pylint: disable=R0902

    """Represents an item file with linkable text."""

    EXTENSIONS = '.yml', '.yaml'

    DEFAULT_LEVEL = Level('1.0')
    DEFAULT_ACTIVE = True
    DEFAULT_NORMATIVE = True
    DEFAULT_DERIVED = False
    DEFAULT_REVIEWED = Stamp()
    DEFAULT_TEXT = Text()
    DEFAULT_REF = ""

    def __init__(self, path, root=os.getcwd(), **kwargs):
        """Initialize an item from an existing file.

        :param path: path to Item file
        :param root: path to root of project

        """
        super().__init__()
        # Ensure the path is valid
        if not os.path.isfile(path):
            raise DoorstopError("item does not exist: {}".format(path))
        # Ensure the filename is valid
        filename = os.path.basename(path)
        name, ext = os.path.splitext(filename)
        try:
            UID(name).check()
        except DoorstopError:
            msg = "invalid item filename: {}".format(filename)
            raise DoorstopError(msg) from None
        # Ensure the file extension is valid
        if ext.lower() not in self.EXTENSIONS:
            msg = "'{0}' extension not in {1}".format(path, self.EXTENSIONS)
            raise DoorstopError(msg)
        # Initialize the item
        self.path = path
        self.root = root
        self.document = kwargs.get('document')
        self.tree = kwargs.get('tree')
        self.auto = kwargs.get('auto', Item.auto)
        # Set default values
        self.level = Item.DEFAULT_LEVEL
        self.active = Item.DEFAULT_ACTIVE
        self.normative = Item.DEFAULT_NORMATIVE
        self.derived = Item.DEFAULT_DERIVED
        self.reviewed = Item.DEFAULT_REVIEWED
        self.text = Item.DEFAULT_TEXT
        self.ref = Item.DEFAULT_REF
        self.links = set()

    def __repr__(self):
        return "Item('{}')".format(self.path)

    def __str__(self):
        if common.verbosity < common.STR_VERBOSITY:
            return str(self.uid)
        else:
            return "{} ({})".format(self.uid, self.relpath)

    def __lt__(self, other):
        if self.level == other.level:
            return self.uid < other.uid
        else:
            return self.level < other.level

    @staticmethod
    @add_item
    def new(tree, document, path, root, uid, level=None, auto=None):  # pylint: disable=R0913
        """Internal method to create a new item.

        :param tree: reference to the tree that contains this item
        :param document: reference to document that contains this item

        :param path: path to directory for the new item
        :param root: path to root of the project
        :param uid: UID for the new item

        :param level: level for the new item
        :param auto: automatically save the item

        :raises: :class:`~doorstop.common.DoorstopError` if the item
            already exists

        :return: new :class:`~doorstop.core.item.Item`

        """
        UID(uid).check()
        filename = str(uid) + Item.EXTENSIONS[0]
        path2 = os.path.join(path, filename)
        # Create the initial item file
        log.debug("creating item file at {}...".format(path2))
        Item._create(path2, name='item')
        # Initialize the item
        item = Item(path2, root=root, document=document, tree=tree, auto=False)
        item.level = level if level is not None else item.level
        if auto or (auto is None and Item.auto):
            item.save()
        # Return the item
        return item

    def load(self, reload=False):
        """Load the item's properties from its file."""
        if self._loaded and not reload:
            return
        log.debug("loading {}...".format(repr(self)))
        # Read text from file
        text = self._read(self.path)
        # Parse YAML data from text
        data = self._load(text, self.path)
        # Store parsed data
        for key, value in data.items():
            if key == 'level':
                value = Level.to_value(value)
            elif key == 'active':
                value = yorm.standard.Boolean.to_value(value)
            elif key == 'normative':
                value = yorm.standard.Boolean.to_value(value)
            elif key == 'derived':
                value = yorm.standard.Boolean.to_value(value)
            elif key == 'reviewed':
                value = Stamp.to_value(value)
            elif key == 'text':
                value = Text.to_value(value)
            elif key == 'ref':
                value = yorm.standard.String.to_value(value)
            elif key == 'links':
                value = set(UID(part) for part in value)
            else:
                if isinstance(value, str):
                    value = Text.to_value(value)
            self._data[key] = value
        # Set meta attributes
        self._loaded = True

    @edit_item
    def save(self):
        """Format and save the item's properties to its file."""
        log.debug("saving {}...".format(repr(self)))
        # Format the data items
        data = self.data
        # Dump the data to YAML
        text = self._dump(data)
        # Save the YAML to file
        self._write(text, self.path)
        # Set meta attributes
        self._loaded = False
        self.auto = True

    # properties #############################################################

    @property
    @auto_load
    def data(self):
        """Get all the item's data formatted for YAML dumping."""
        data = {}
        for key, value in self._data.items():
            if key == 'level':
                value = Level.to_data(value)
            elif key == 'text':
                value = Text.to_data(value)
            elif key == 'ref':
                value = yorm.standard.String.to_data(value)
            elif key == 'links':
                value = [{str(i): Stamp.to_data(i.stamp)} for i in sorted(value)]
            elif key == 'reviewed':
                value = Stamp.to_data(value)
            else:
                if isinstance(value, str):
                    # length of "key_text: value_text"
                    length = len(key) + 2 + len(value)
                    if length > settings.MAX_LINE_LENGTH or '\n' in value:
                        value = Text.save_text(value)
                    else:
                        value = str(value)  # line is short enough as a string
            data[key] = value
        return data

    @property
    def uid(self):
        """Get the item's UID."""
        filename = os.path.basename(self.path)
        return UID(os.path.splitext(filename)[0])

    @property
    def prefix(self):
        """Get the item UID's prefix."""
        return self.uid.prefix

    @property
    def number(self):
        """Get the item UID's number."""
        return self.uid.number

    @property
    def depth(self):
        """Get the item's heading order based on it's level."""
        return len(self.level)

    @property
    def heading(self):
        """Indicate if the item is a heading.

        Headings have a level that ends in zero and are non-normative.

        """
        return self.level.heading and not self.normative

    @heading.setter
    @auto_save
    @auto_load
    def heading(self, value):
        """Set the item's heading status."""
        heading = to_bool(value)
        if heading and not self.heading:
            self.level.heading = True
            self.normative = False
        elif not heading and self.heading:
            self.level.heading = False
            self.normative = True

    @property
    @auto_load
    def cleared(self):
        """Indicate if no links are suspect."""
        items = self.parent_items
        for uid in self.links:
            for item in items:
                if uid == item.uid:
                    if uid.stamp != item.stamp():
                        return False
        return True

    @cleared.setter
    @auto_save
    @auto_load
    def cleared(self, value):
        """Set the item's suspect link status."""
        self.clear(_inverse=not to_bool(value))

    @property
    def parent_links(self):
        """Get a list of the item UIDs this item links to."""
        return self.links  # alias

    @parent_links.setter
    def parent_links(self, value):
        """Set the list of item UIDs this item links to."""
        self.links = value  # alias

    @property
    @requires_tree
    def parent_items(self):
        """Get a list of items that this item links to."""
        items = []
        for uid in self.links:
            try:
                item = self.tree.find_item(uid)
            except DoorstopError:
                item = UnknownItem(uid)
                log.warning(item.exception)
            items.append(item)
        return items

    @property
    @requires_tree
    @requires_document
    def parent_documents(self):
        """Get a list of documents that this item's document should link to.

        .. note::

           A document only has one parent.

        """
        try:
            return [self.tree.find_document(self.document.prefix)]
        except DoorstopError:
            log.warning(Prefix.UNKNOWN_MESSGE.format(self.document.prefix))
            return []

    # actions ################################################################

    @auto_save
    def edit(self, tool=None):
        """Open the item for editing.

        :param tool: path of alternate editor

        """
        # Lock the item
        if self.tree:
            self.tree.vcs.lock(self.path)
        # Open in an editor
        editor.edit(self.path, tool=tool)
        # Force reloaded
        self._loaded = False

    @auto_save
    @auto_load
    def link(self, value):
        """Add a new link to another item UID.

        :param value: item or UID

        """
        uid = UID(value)
        log.info("linking to '{}'...".format(uid))
        self._data['links'].add(uid)

    @auto_save
    @auto_load
    def unlink(self, value):
        """Remove an existing link by item UID.

        :param value: item or UID

        """
        uid = UID(value)
        try:
            self._data['links'].remove(uid)
        except KeyError:
            log.warning("link to {0} does not exist".format(uid))

    def get_issues(self, **kwargs):
        """Yield all the item's issues.

        :return: generator of :class:`~doorstop.common.DoorstopError`,
                              :class:`~doorstop.common.DoorstopWarning`,
                              :class:`~doorstop.common.DoorstopInfo`

        """
        assert kwargs.get('document_hook') is None
        assert kwargs.get('item_hook') is None
        log.info("checking item {}...".format(self))
        # Verify the file can be parsed
        self.load()
        # Skip inactive items
        if not self.active:
            log.info("skipped inactive item: {}".format(self))
            return
        # Delay item save if reformatting
        if settings.REFORMAT:
            self.auto = False
        # Check text
        if not self.text:
            yield DoorstopWarning("no text")
        # Check external references
        if settings.CHECK_REF:
            try:
                self.find_ref()
            except DoorstopError as exc:
                yield exc
        # Check links
        if not self.normative and self.links:
            yield DoorstopWarning("non-normative, but has links")
        # Check links against the document
        if self.document:
            yield from self._get_issues_document(self.document)
        # Check links against the tree
        if self.tree:
            yield from self._get_issues_tree(self.tree)
        # Check links against both document and tree
        if self.document and self.tree:
            yield from self._get_issues_both(self.document, self.tree)
        # Check review status
        if not self.reviewed:
            if settings.CHECK_REVIEW_STATUS:
                yield DoorstopWarning("unreviewed changes")
        # Reformat the file
        if settings.REFORMAT:
            log.debug("reformatting item {}...".format(self))
            self.save()

    def _get_issues_document(self, document):
        """Yield all the item's issues against its document."""
        log.debug("getting issues against document...")
        # Verify an item's UID matches its document's prefix
        if self.prefix != document.prefix:
            msg = "prefix differs from document ({})".format(document.prefix)
            yield DoorstopInfo(msg)
        # Verify an item has upward links
        if all((document.parent,
                self.normative,
                not self.derived)) and not self.links:
            msg = "no links to parent document: {}".format(document.parent)
            yield DoorstopWarning(msg)
        # Verify an item's links are to the correct parent
        for uid in self.links:
            try:
                prefix = uid.prefix
            except DoorstopError:
                msg = "invalid UID in links: {}".format(uid)
                yield DoorstopError(msg)
            else:
                if document.parent and prefix != document.parent:
                    # this is only 'info' because a document is allowed
                    # to contain items with a different prefix, but
                    # Doorstop will not create items like this
                    msg = "parent is '{}', but linked to: {}".format(
                        document.parent, uid)
                    yield DoorstopInfo(msg)

    def _get_issues_tree(self, tree):
        """Yield all the item's issues against its tree."""
        log.debug("getting issues against tree...")
        # Verify an item's links are valid
        identifiers = set()
        for uid in self.links:
            try:
                item = tree.find_item(uid)
            except DoorstopError:
                identifiers.add(uid)  # keep the invalid UID
                msg = "linked to unknown item: {}".format(uid)
                yield DoorstopError(msg)
            else:
                # check the linked item
                if not item.active:
                    msg = "linked to inactive item: {}".format(item)
                    yield DoorstopInfo(msg)
                if not item.normative:
                    msg = "linked to non-normative item: {}".format(item)
                    yield DoorstopWarning(msg)
                # check the link status
                if uid.stamp == Stamp(True):
                    uid.stamp = item.stamp()  # convert True to a stamp
                elif uid.stamp != item.stamp():
                    if settings.CHECK_SUSPECT_LINKS:
                        msg = "suspect link: {}".format(item)
                        yield DoorstopWarning(msg)
                # reformat the item's UID
                identifier2 = UID(item.uid, stamp=uid.stamp)
                identifiers.add(identifier2)
        # Apply the reformatted item UIDs
        if settings.REFORMAT:
            self._data['links'] = identifiers

    def _get_issues_both(self, document, tree):
        """Yield all the item's issues against its document and tree."""
        log.debug("getting issues against document and tree...")
        # Verify an item is being linked to (child links)
        if settings.CHECK_CHILD_LINKS and self.normative:
            items, documents = self._find_child_objects(document=document,
                                                        tree=tree,
                                                        find_all=False)
            if not items:
                for document in documents:
                    msg = "no links from child document: {}".format(document)
                    yield DoorstopWarning(msg)

    @requires_tree
    def find_ref(self):
        """Get the external file reference and line number.

        :raises: :class:`~doorstop.common.DoorstopError` when no
            reference is found

        :return: relative path to file or None (when no reference
            set),
            line number (when found in file) or None (when found as
            filename) or None (when no reference set)

        """
        # Return immediately if no external reference
        if not self.ref:
            log.debug("no external reference to search for")
            return None, None
        # Update the cache
        if not settings.CACHE_PATHS:
            pyficache.clear_file_cache()
        # Search for the external reference
        log.debug("seraching for ref '{}'...".format(self.ref))
        pattern = r"(\b|\W){}(\b|\W)".format(re.escape(self.ref))
        log.trace("regex: {}".format(pattern))
        regex = re.compile(pattern)
        for path, filename, relpath in self.tree.vcs.paths:
            # Skip the item's file while searching
            if path == self.path:
                continue
            # Check for a matching filename
            if filename == self.ref:
                return relpath, None
            # Skip extensions that should not be considered text
            if os.path.splitext(filename)[-1] in settings.SKIP_EXTS:
                continue
            # Search for the reference in the file
            lines = pyficache.getlines(path)
            if lines is None:
                log.trace("unable to read lines from: {}".format(path))
                continue
            for lineno, line in enumerate(lines, start=1):
                if regex.search(line):
                    log.debug("found ref: {}".format(relpath))
                    return relpath, lineno

        msg = "external reference not found: {}".format(self.ref)
        raise DoorstopError(msg)

    def find_child_links(self, find_all=True):
        """Get a list of item UIDs that link to this item (reverse links).

        :param find_all: find all items (not just the first) before returning

        :return: list of found item UIDs

        """
        items, _ = self._find_child_objects(find_all=find_all)
        identifiers = [item.uid for item in items]
        return identifiers

    child_links = property(find_child_links)

    def find_child_items(self, find_all=True):
        """Get a list of items that link to this item.

        :param find_all: find all items (not just the first) before returning

        :return: list of found items

        """
        items, _ = self._find_child_objects(find_all=find_all)
        return items

    child_items = property(find_child_items)

    def find_child_documents(self):
        """Get a list of documents that should link to this item's document.

        :return: list of found documents

        """
        _, documents = self._find_child_objects(find_all=False)
        return documents

    child_documents = property(find_child_documents)

    def _find_child_objects(self, document=None, tree=None, find_all=True):
        """Get lists of child items and child documents.

        :param document: document containing the current item
        :param tree: tree containing the current item
        :param find_all: find all items (not just the first) before returning

        :return: list of found items, list of all child documents

        """
        child_items = []
        child_documents = []
        document = document or self.document
        tree = tree or self.tree
        if not document or not tree:
            return child_items, child_documents
        # Find child objects
        log.debug("finding item {}'s child objects...".format(self))
        for document2 in tree:
            if document2.parent == document.prefix:
                child_documents.append(document2)
                # Search for child items unless we only need to find one
                if not child_items or find_all:
                    for item2 in document2:
                        if self.uid in item2.links:
                            child_items.append(item2)
                            if not find_all:
                                break
        # Display found links
        if child_items:
            if find_all:
                joined = ', '.join(str(i) for i in child_items)
                msg = "child items: {}".format(joined)
            else:
                msg = "first child item: {}".format(child_items[0])
            log.debug(msg)
            joined = ', '.join(str(d) for d in child_documents)
            log.debug("child documents: {}".format(joined))
        return sorted(child_items), child_documents

    @auto_load
    def stamp(self, links=False):
        """Hash the item's key content for later comparison."""
        values = [self.uid, self.text, self.ref]
        if links:
            values.extend(self.links)
        return Stamp(*values)

    @auto_save
    @auto_load
    def clear(self, _inverse=False):
        """Clear suspect links."""
        log.info("clearing suspect links...")
        items = self.parent_items
        for uid in self.links:
            for item in items:
                if uid == item.uid:
                    if _inverse:
                        uid.stamp = Stamp()
                    else:
                        uid.stamp = item.stamp()

    @auto_save
    @auto_load
    def review(self):
        """Mark the item as reviewed."""
        log.info("marking item as reviewed...")
        self._data['reviewed'] = self.stamp(links=True)

    @delete_item
    def delete(self, path=None):
        """Delete the item."""
        pass  # the item is deleted in the decorated method


class UnknownItem:

    """Represents an unknown item, which doesn't have a path."""

    UNKNOWN_PATH = '???'  # string to represent an unknown path

    normative = False  # do not include unknown items in traceability

    def __init__(self, value, spec=Item):
        self._uid = UID(value)
        self._spec = dir(spec)  # list of attribute names for warnings
        msg = UID.UNKNOWN_MESSAGE.format(k='', u=self.uid)
        self.exception = DoorstopError(msg)

    def __str__(self):
        return Item.__str__(self)

    def __getattr__(self, name):
        if name in self._spec:
            log.debug(self.exception)
        return self.__getattribute__(name)

    @property
    def uid(self):
        """Get the item's UID."""
        return self._uid

    prefix = Item.prefix
    number = Item.number

    @property
    def relpath(self):
        """Get the unknown item's relative path string."""
        return "@{}{}".format(os.sep, self.UNKNOWN_PATH)

    def stamp(self):  # pylint: disable=R0201
        """Return an empty stamp."""
        return Stamp(None)
