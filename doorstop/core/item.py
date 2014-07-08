"""Representation of an item in a document."""

import os
import re
import logging

from doorstop import common
from doorstop.common import DoorstopError, DoorstopWarning, DoorstopInfo
from doorstop.core.base import BaseValidatable, clear_item_cache
from doorstop.core.base import auto_load, auto_save, BaseFileObject
from doorstop.core.types import Prefix, ID, Text, Level, to_bool
from doorstop.core import editor
from doorstop import settings


class Item(BaseValidatable, BaseFileObject):  # pylint: disable=R0902,R0904

    """Represents an item file with linkable text."""

    EXTENSIONS = '.yml', '.yaml'

    DEFAULT_LEVEL = Level('1.0')
    DEFAULT_ACTIVE = True
    DEFAULT_NORMATIVE = True
    DEFAULT_DERIVED = False
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
            ID(name).check()
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
        self._data['level'] = Item.DEFAULT_LEVEL
        self._data['active'] = Item.DEFAULT_ACTIVE
        self._data['normative'] = Item.DEFAULT_NORMATIVE
        self._data['derived'] = Item.DEFAULT_DERIVED
        self._data['text'] = Item.DEFAULT_TEXT
        self._data['ref'] = Item.DEFAULT_REF
        self._data['links'] = set()

    def __repr__(self):
        return "Item('{}')".format(self.path)

    def __str__(self):
        if common.VERBOSITY < common.STR_VERBOSITY:
            return str(self.id)
        else:
            return "{} ({})".format(self.id, self.relpath)

    def __lt__(self, other):
        if self.level == other.level:
            return self.id < other.id
        else:
            return self.level < other.level

    @staticmethod
    def new(tree, document, path, root, identifier, level=None, auto=None):  # pylint: disable=R0913
        """Internal method to create a new item.

        :param tree: reference to the tree that contains this item
        :param document: reference to document that contains this item

        :param path: path to directory for the new item
        :param root: path to root of the project
        :param identifier: ID for the new item

        :param level: level for the new item
        :param auto: automatically save the item

        :raises: :class:`~doorstop.common.DoorstopError` if the item
            already exists

        :return: new :class:`~doorstop.core.item.Item`

        """
        ID(identifier).check()
        filename = str(identifier) + Item.EXTENSIONS[0]
        path2 = os.path.join(path, filename)
        # Create the initial item file
        logging.debug("creating item file at {}...".format(path2))
        Item._new(path2, name='item')
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
        logging.debug("loading {}...".format(repr(self)))
        # Read text from file
        text = self._read(self.path)
        # Parse YAML data from text
        data = self._load(text, self.path)
        # Store parsed data
        for key, value in data.items():
            if key == 'level':
                self._data['level'] = Level(value)
            elif key == 'active':
                self._data['active'] = to_bool(value)
            elif key == 'normative':
                self._data['normative'] = to_bool(value)
            elif key == 'derived':
                self._data['derived'] = to_bool(value)
            elif key == 'text':
                self._data['text'] = Text(value)
            elif key == 'ref':
                self._data['ref'] = value.strip()
            elif key == 'links':
                self._data['links'] = set(ID(v) for v in value)
            else:
                if isinstance(value, str):
                    value = Text(value)
                self._data[key] = value
        # Set meta attributes
        self._loaded = True

    def save(self):
        """Format and save the item's properties to its file."""
        logging.debug("saving {}...".format(repr(self)))
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
        """Get all the item's data formatted for dumping."""
        data = {}
        for key, value in self._data.items():
            if key == 'level':
                data['level'] = value.yaml
            elif key == 'text':
                data['text'] = value.yaml
            elif key == 'ref':
                data['ref'] = value.strip()
            elif key == 'links':
                data['links'] = sorted(str(v) for v in value)
            else:
                if isinstance(value, str):
                    # length of "key_text: value_text"
                    lenth = len(key) + 2 + len(value)
                    if lenth > settings.MAX_LINE_LENTH or '\n' in value:
                        end = '\n' if value.endswith('\n') else ''
                        value = Text.save_text(value, end=end)
                    else:
                        value = str(value)  # line is short enough as a string
                data[key] = value
        return data

    @property
    def id(self):  # pylint: disable=C0103
        """Get the item's ID."""
        filename = os.path.basename(self.path)
        return ID(os.path.splitext(filename)[0])

    @property
    def prefix(self):
        """Get the item ID's prefix."""
        return self.id.prefix

    @property
    def number(self):
        """Get the item ID's number."""
        return self.id.number

    @property
    @auto_load
    def level(self):
        """Get the item's level."""
        return self._data['level']

    @level.setter
    @auto_save
    @auto_load
    def level(self, value):
        """Set the item's level."""
        self._data['level'] = Level(value)

    @property
    def depth(self):
        """Get the item's heading order based on it's level."""
        return len(self.level)

    @property
    @auto_load
    def active(self):
        """Get the item's active status.

        An inactive item will not be validated. Inactive items are
        intended to be used for:

        - future requirements
        - temporarily disabled requirements or tests
        - externally implemented requirements
        - etc.

        """
        return self._data['active']

    @active.setter
    @auto_save
    @auto_load
    def active(self, value):
        """Set the item's active status."""
        self._data['active'] = to_bool(value)

    @property
    @auto_load
    def derived(self):
        """Get the item's derived status.

        A derived item does not have links to items in its parent
        document, but should still be linked to by items in its child
        documents.

        """
        return self._data['derived']

    @derived.setter
    @auto_save
    @auto_load
    def derived(self, value):
        """Set the item's derived status."""
        self._data['derived'] = to_bool(value)

    @property
    @auto_load
    def normative(self):
        """Get the item's normative status.

        A non-normative item should not have or be linked to.
        Non-normative items are intended to be used for:

        - headings
        - comments
        - etc.

        """
        return self._data['normative']

    @normative.setter
    @auto_save
    @auto_load
    def normative(self, value):
        """Set the item's normative status."""
        self._data['normative'] = to_bool(value)

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
    def text(self):
        """Get the item's text."""
        return self._data['text']

    @text.setter
    @auto_save
    @auto_load
    def text(self, value):
        """Set the item's text."""
        self._data['text'] = Text(value)

    @property
    @auto_load
    def ref(self):
        """Get the item's external file reference.

        An external reference can be part of a line in a text file or
        the filename of any type of file.

        """
        return self._data['ref']

    @ref.setter
    @auto_save
    @auto_load
    def ref(self, value):
        """Set the item's external file reference."""
        self._data['ref'] = str(value) if value else ""

    @property
    @auto_load
    def links(self):
        """Get a list of the item IDs this item links to."""
        return sorted(self._data['links'])

    @links.setter
    @auto_save
    @auto_load
    def links(self, value):
        """Set the list of item IDs this item links to."""
        self._data['links'] = set(value)

    @property
    def parent_links(self):
        """Get a list of the item IDs this item links to."""
        return self.links  # alias

    @parent_links.setter
    def parent_links(self, value):
        """Set the list of item IDs this item links to."""
        self.links = value  # alias

    @property
    def parent_items(self):
        """Get a list of items that this item links to."""
        items = []
        for identifier in self.links:
            try:
                item = self.tree.find_item(identifier)
            except DoorstopError:
                item = UnknownItem(identifier)
                logging.warning(item.exception)
            items.append(item)
        return items

    @property
    def parent_documents(self):
        """Get a list of documents that this item's document should link to.

        .. note::

           A document only has one parent.

        """
        # TODO: determine if an `UnknownDocument` class is needed
        try:
            return [self.tree.find_document(self.document.prefix)]
        except DoorstopError:
            logging.warning(Prefix.UNKNOWN_MESSGE.format(self.document.prefix))
            return []

    # actions ################################################################

    @auto_save
    def edit(self, tool=None):
        """Open the item for editing.

        :param tool: path of alternate editor

        """
        # Lock the item
        self.tree.vcs.lock(self.path)
        # Open in an editor
        editor.edit(self.path, tool=tool)
        # Force reloaded
        self._loaded = False

    @auto_save
    @auto_load
    def link(self, value):
        """Add a new link to another item ID.

        :param value: item or ID

        """
        identifier = ID(value)
        self._data['links'].add(identifier)

    @auto_save
    @auto_load
    def unlink(self, value):
        """Remove an existing link by item ID.

        :param value: item or ID

        """
        identifier = ID(value)
        try:
            self._data['links'].remove(identifier)
        except KeyError:
            logging.warning("link to {0} does not exist".format(identifier))

    def get_issues(self, **kwargs):
        """Yield all the item's issues.

        :return: generator of :class:`~doorstop.common.DoorstopError`,
                              :class:`~doorstop.common.DoorstopWarning`,
                              :class:`~doorstop.common.DoorstopInfo`

        """
        assert kwargs.get('document_hook') is None
        assert kwargs.get('item_hook') is None
        logging.info("checking item {}...".format(self))
        # Verify the file can be parsed
        self.load()
        # Skip inactive items
        if not self.active:
            logging.info("skipped inactive item: {}".format(self))
            return
        # Delay item save if reformatting
        if settings.REFORMAT:
            self.auto = False
        # Check text
        if not self.text and not self.ref:
            yield DoorstopWarning("no text")
        # Check external references
        if settings.CHECK_REF:
            try:
                # TODO: find_ref should get 'self.tree.vcs.ignored' internally
                self.find_ref(ignored=self.tree.vcs.ignored
                              if self.tree else None)
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
        # Reformat the file
        if settings.REFORMAT:
            self.save()

    def _get_issues_document(self, document):
        """Yield all the item's issues against its document."""
        logging.debug("getting issues against document: {}".format(document))
        # Verify an item's ID matches its document's prefix
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
        for identifier in self.links:
            try:
                prefix = identifier.prefix
            except DoorstopError:
                msg = "invalid ID in links: {}".format(identifier)
                yield DoorstopError(msg)
            else:
                if document.parent and prefix != document.parent:
                    # this is only 'info' because a document is allowed
                    # to contain items with a different prefix, but
                    # Doorstop will not create items like this
                    msg = "parent is '{}', but linked to: {}".format(
                        document.parent, identifier)
                    yield DoorstopInfo(msg)

    def _get_issues_tree(self, tree):
        """Yield all the item's issues against its tree."""
        logging.debug("getting issues against tree: {}".format(tree))
        # Verify an item's links are valid
        identifiers = set()
        for identifier in self.links:
            try:
                item = tree.find_item(identifier)
            except DoorstopError:
                identifiers.add(identifier)  # keep the invalid ID
                msg = "linked to unknown item: {}".format(identifier)
                yield DoorstopError(msg)
            else:
                if not item.active:
                    msg = "linked to inactive item: {}".format(item)
                    yield DoorstopInfo(msg)
                if not item.normative:
                    msg = "linked to non-normative item: {}".format(item)
                    yield DoorstopWarning(msg)
                identifier = item.id  # reformat the item's ID
                logging.debug("found linked item: {}".format(identifier))
                identifiers.add(identifier)
        # Apply the reformatted item IDs
        if settings.REFORMAT:
            self._data['links'] = identifiers

    def _get_issues_both(self, document, tree):
        """Yield all the item's issues against its document and tree."""
        logging.debug("getting issues against both: {} & {}".format(document,
                                                                    tree))
        # Verify an item is being linked to (child links)
        if settings.CHECK_CHILD_LINKS and self.normative:
            items, documents = self._find_child_objects(find_all=False)
            if not items:
                for document in documents:
                    msg = "no links from child document: {}".format(document)
                    yield DoorstopWarning(msg)

    def find_ref(self, skip=None, root=None, ignored=None):
        """Get the external file reference and line number.

        :param skip: function to determine if a path is ignored
        :param root: override path to the working copy (for testing)
        :param ignored: override VCS ignore function (for testing)

        :raises: :class:`~doorstop.common.DoorstopError` when no
            reference is found

        :return: relative path to file or None (when no reference
            set),
            line number (when found in file) or None (when found as
            filename) or None (when no reference set)

        """
        root = root or self.root
        ignored = ignored or \
            self.tree.vcs.ignored if self.tree else (lambda _: False)
        # Return immediately if no external reference
        if not self.ref:
            logging.debug("no external reference to search for")
            return None, None
        # Search for the external reference
        logging.debug("seraching for ref '{}'...".format(self.ref))
        pattern = r"(\b|\W){}(\b|\W)".format(re.escape(self.ref))
        logging.debug("regex: {}".format(pattern))
        regex = re.compile(pattern)
        logging.debug("search path: {}".format(root))
        for root, _, filenames in os.walk(root):
            for filename in filenames:  # pragma: no cover (integration test)
                path = os.path.join(root, filename)
                relpath = os.path.relpath(path, self.root)
                # Skip the item's file while searching
                if path == self.path:
                    continue
                # Skip hidden directories
                if os.path.sep + '.' in path:
                    continue
                # Skip ignored paths
                if ignored(path) or (skip and skip(path)):
                    continue
                # Check for a matching filename
                if filename == self.ref:
                    return relpath, None
                # Skip extensions that should not be considered text
                if os.path.splitext(filename)[-1] in settings.SKIP_EXTS:
                    continue
                # Search for the reference in the file
                try:
                    with open(path, 'r') as external:
                        for index, line in enumerate(external):
                            if regex.search(line):
                                logging.debug("found ref: {}".format(relpath))
                                return relpath, index + 1
                except UnicodeDecodeError:
                    pass
        msg = "external reference not found: {}".format(self.ref)
        raise DoorstopError(msg)

    def find_child_links(self, find_all=True):
        """Get a list of item IDs that link to this item (reverse links).

        :param find_all: find all items (not just the first) before returning

        :return: list of found item IDs

        """
        items, _ = self._find_child_objects(find_all=find_all)
        identifiers = [item.id for item in items]
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

    def _find_child_objects(self, find_all=True):
        """Get lists of child items and child documents.

        :param find_all: find all items (not just the first) before returning

        :return: list of found items, list of all child Documents

        """
        child_items = []
        child_documents = []
        # Check for parent references
        if not self.document or not self.tree:
            logging.warning("document and tree required to find children")
            return child_items, child_documents
        # Find child objects
        for document2 in self.tree:
            if document2.parent == self.document.prefix:
                child_documents.append(document2)
                # Search for child items unless we only need to find one
                if not child_items or find_all:
                    for item in document2:
                        if self.id in item.links:
                            child_items.append(item)
                            if not find_all:
                                break
        # Display found links
        if child_items:
            if find_all:
                joined = ', '.join(str(i) for i in child_items)
                msg = "child items: {}".format(joined)
            else:
                msg = "first child item: {}".format(child_items[0])
            logging.debug(msg)
            joined = ', '.join(str(d) for d in child_documents)
            logging.debug("child documents: {}".format(joined))
        return sorted(child_items), child_documents

    @clear_item_cache
    def delete(self, path=None):
        """Delete the item."""
        # TODO: #65: move this to a decorator and remove pylint comments
        if self.document and self in self.document._items:  # pylint:disable=W0212
            self.document._items.remove(self)  # pylint:disable=W0212
        super().delete(self.path)


class UnknownItem(object):

    """Represents an unknown item, which doesn't have a path."""

    UNKNOWN_PATH = '???'  # string to represent an unknown path

    normative = False  # do not include unknown items in traceability

    def __init__(self, value, spec=Item):
        self._id = ID(value)
        self._spec = dir(spec)  # list of attribute names for warnings
        msg = ID.UNKNOWN_MESSAGE.format(k='', i=self.id)
        self.exception = DoorstopError(msg)

    def __str__(self):
        return Item.__str__(self)

    def __getattr__(self, name):
        if name in self._spec:
            logging.debug(self.exception)
        return self.__getattribute__(name)

    @property
    def id(self):  # pylint: disable=C0103
        """Get the item's ID."""
        return self._id

    prefix = Item.prefix
    number = Item.number

    @property
    def relpath(self):
        """Get the unknown item's relative path string."""
        return "@{}???".format(os.sep, self.UNKNOWN_PATH)
