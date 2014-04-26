"""Representation of items in a Doorstop document."""

import os
import re
import logging

from doorstop.core import base
from doorstop.core.base import auto_load, auto_save, BaseFileObject
from doorstop.core.base import BaseValidatable
from doorstop import common
from doorstop.common import DoorstopError, DoorstopWarning, DoorstopInfo
from doorstop import settings


class Item(BaseValidatable, BaseFileObject):  # pylint: disable=R0904

    """Represents an item file with linkable text."""

    EXTENSIONS = '.yml', '.yaml'

    DEFAULT_LEVEL = (1, 0)
    DEFAULT_ACTIVE = True
    DEFAULT_NORMATIVE = True
    DEFAULT_DERIVED = False
    DEFAULT_TEXT = ""
    DEFAULT_REF = ""

    def __init__(self, path, root=os.getcwd()):
        """Load an item from an existing file.

        @param path: path to Item file
        @param root: path to root of project

        """
        super().__init__()
        # Ensure the path is valid
        if not os.path.isfile(path):
            raise DoorstopError("item does not exist: {}".format(path))
        # Ensure the filename is valid
        filename = os.path.basename(path)
        name, ext = os.path.splitext(filename)
        try:
            split_id(name)
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
        # Set default values
        self._data['level'] = Item.DEFAULT_LEVEL
        self._data['active'] = Item.DEFAULT_ACTIVE
        self._data['normative'] = Item.DEFAULT_NORMATIVE
        self._data['derived'] = Item.DEFAULT_DERIVED
        self._data['text'] = Item.DEFAULT_TEXT
        self._data['ref'] = Item.DEFAULT_REF
        self._data['links'] = set()

    def __repr__(self):
        return "Item({})".format(repr(self.path))

    def __str__(self):
        if common.VERBOSITY < common.STR_VERBOSITY:
            return self.id
        else:
            return "{} ({})".format(self.id, self.relpath)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.path == other.path

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        return self.level < other.level

    @staticmethod
    def new(path, root, identifier, level=None, auto=None):  # pylint: disable=R0913
        """Create a new item.

        @param path: path to directory for the new item
        @param root: path to root of the project
        @param identifier: ID for the new item
        @param level: level for the new item
        @param auto: enables automatic save

        @raise DoorstopError: if the item already exists

        """
        filename = identifier + Item.EXTENSIONS[0]
        path2 = os.path.join(path, filename)
        # Create the initial item file
        logging.debug("creating item file at {}...".format(path2))
        Item._new(path2, name='item')
        # Initialize the item
        item = Item(path2, root=root)
        item.auto = False
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
                self._data['level'] = load_level(value)
            elif key == 'active':
                self._data['active'] = bool(value)
            elif key == 'normative':
                self._data['normative'] = bool(value)
            elif key == 'derived':
                self._data['derived'] = bool(value)
            elif key == 'text':
                self._data['text'] = load_text(value)
            elif key == 'ref':
                self._data['ref'] = value.strip()
            elif key == 'links':
                self._data['links'] = set(value)
            else:
                if isinstance(value, str):
                    value = load_text(value)
                self._data[key] = value
        # Set meta attributes
        self._loaded = True

    def save(self):
        """Format and save the item's properties to its file."""
        logging.debug("saving {}...".format(repr(self)))
        # Format the data items
        data = {}
        for key, value in self._data.items():
            if key == 'level':
                data['level'] = save_level(value)
            elif key == 'text':
                data['text'] = save_text(self._data['text'])
            elif key == 'ref':
                data['ref'] = value.strip()
            elif key == 'links':
                data['links'] = sorted(value)
            else:
                if isinstance(value, str):
                    # length of "key_text: value_text"
                    lenth = len(key) + 2 + len(value)
                    if lenth > settings.MAX_LINE_LENTH or '\n' in value:
                        end = '\n' if value.endswith('\n') else ''
                        value = save_text(value, end=end)
                data[key] = value
        # Dump the data to YAML
        text = self._dump(data)
        # Save the YAML to file
        self._write(text, self.path)
        # Set meta attributes
        self._loaded = False
        self.auto = True

    # properties #############################################################

    @property
    def id(self):  # pylint: disable=C0103
        """Get the item's ID."""
        return os.path.splitext(os.path.basename(self.path))[0]

    @property
    def relpath(self):
        """Get the item's relative path string."""
        relpath = os.path.relpath(self.path, self.root)
        return "@{}{}".format(os.sep, relpath)

    @property
    def prefix(self):
        """Get the item ID's prefix."""
        return split_id(self.id)[0]

    @property
    def number(self):
        """Get the item ID's number."""
        return split_id(self.id)[1]

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
        self._data['level'] = load_level(value)

    @property
    def depth(self):
        """Get the item's heading order based on it's level."""
        level = list(self.level)
        while level[-1] == 0:
            del level[-1]
        return len(level)

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
        self._data['active'] = bool(value)

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
        self._data['derived'] = bool(value)

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
        self._data['normative'] = bool(value)

    @property
    def heading(self):
        """Indicate if the item is a heading.

        Headings have a level that ends in zero and are non-normative.

        """
        return self.level[-1] == 0 and not self.normative

    @heading.setter
    @auto_save
    @auto_load
    def heading(self, value):
        """Set the item's heading status."""
        heading = bool(value)
        if heading and not self.heading:
            self.level = list(self.level) + [0]
            self.normative = False
        elif not heading and self.heading:
            self.level = list(self.level)[:-1]
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
        self._data['text'] = str(value) if value else ""

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

    # actions ################################################################

    @auto_save
    @auto_load
    def link(self, identifier):
        """Add a new link to another item ID.

        @param identifier: item's ID (or item)

        """
        identifier = get_id(identifier)
        self._data['links'].add(identifier)

    @auto_save
    @auto_load
    def unlink(self, identifier):
        """Remove an existing link by item ID.

        @param identifier: item's ID (or item)

        """
        identifier = get_id(identifier)
        try:
            self._data['links'].remove(identifier)
        except KeyError:
            logging.warning("link to {0} does not exist".format(identifier))

    def get_issues(self, document=None, tree=None, **_):
        """Yield all the item's issues.

        @param document: Document containing the item (document-level issues)
        @param tree: Tree containing the item (tree-level issues)

        @return: generator of DoorstopError, DoorstopWarning, DoorstopInfo

        """
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
                self.find_ref(ignored=tree.vcs.ignored if tree else None)
            except DoorstopError as exc:
                yield exc
        # Check links
        if not self.normative and self.links:
            yield DoorstopWarning("non-normative, but has links")
        # Check links against the document
        if document:
            yield from self._get_issues_document(document)
        # Check links against the tree
        if tree:
            yield from self._get_issues_tree(tree)
        # Check links against both document and tree
        if document and tree:
            yield from self._get_issues_both(document, tree)
        # Reformat the file
        if settings.REFORMAT:
            self.save()

    def _get_issues_document(self, document):
        """Yield all the item's issues against its document."""
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
                prefix = split_id(identifier)[0]
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
        # Verify an item is being linked to (reverse links)
        if settings.CHECK_RLINKS and self.normative:
            rlinks, children = self.find_rlinks(document, tree, find_all=False)
            if not rlinks:
                for child in children:
                    msg = "no links from child document: {}".format(child)
                    yield DoorstopWarning(msg)

    def find_ref(self, root=None, ignored=None):
        """Get the external file reference and line number.

        @param root: override the path to the working copy (for testing)
        @param ignored: function to determine if a path should be skipped

        @return: relative path to file, line number (when found in file)
                 relative path to file, None (when found as filename)
                 None, None (when no ref)

        @raise DoorstopError: when no ref is found

        """
        if not self.ref:
            logging.debug("no external reference to search for")
            return None, None
        ignored = ignored or (lambda _: False)
        logging.debug("seraching for ref '{}'...".format(self.ref))
        pattern = r"(\b|\W){}(\b|\W)".format(re.escape(self.ref))
        logging.debug("regex: {}".format(pattern))
        regex = re.compile(pattern)
        logging.debug("search path: {}".format(root or self.root))
        for root, _, filenames in os.walk(root or self.root):
            for filename in filenames:  # pragma: no cover, integration test
                path = os.path.join(root, filename)
                relpath = os.path.relpath(path, self.root)
                # Skip the item's file while searching
                if path == self.path:
                    continue
                # Skip hidden directories
                if os.path.sep + '.' in path:
                    continue
                # Skip ignored paths
                if ignored(path):
                    continue
                # Search for the reference in the file
                if filename == self.ref:
                    return relpath, None
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

    # TODO: should this only return IDs and add a find_children method?
    def find_rlinks(self, document, tree, find_all=True):
        """Get a list of item IDs that link to this item (reverse links).

        @param document: Document containing the item
        @param tree: Tree containing the item
        @param find_all: find all items (not just the first) before returning

        @return: list of found item IDs, list of all child Documents

        """
        rlinks = []
        children = []
        for document2 in tree:
            if document2.parent == document.prefix:
                children.append(document2)
                # Search for reverse links unless we only need to find one
                if not rlinks or find_all:
                    for item in document2:
                        if self.id in item.links:
                            rlinks.append(item.id)
                            if not find_all:
                                break
        if rlinks:
            if find_all:
                msg = "reverse links: {}".format(', '.join(rlinks))
            else:
                msg = "first reverse link: {}".format(rlinks[0])
            logging.debug(msg)
        return rlinks, children

    def delete(self, path=None):
        """Delete the item."""
        super().delete(self.path)


# attribute formatters #######################################################

def get_id(value):
    """Get an ID from an item or string."""
    return str(value).split(' ')[0]


def split_id(text):
    """Split an item's ID into a prefix and number.

    >>> split_id('ABC00123')
    ('ABC', 123)

    >>> split_id('ABC.HLR_01-00123')
    ('ABC.HLR_01', 123)

    >>> split_id('REQ2-001')
    ('REQ2', 1)

    """
    match = re.match(r"([\w.-]*\D)(\d+)", text)
    if not match:
        raise DoorstopError("invalid ID: {}".format(text))
    prefix = match.group(1).rstrip(settings.SEP_CHARS)
    number = int(match.group(2))
    return prefix, number


def join_id(prefix, sep, number, digits):
    """Join the parts of an item's ID into an ID.

    >>> join_id('ABC', '', 123, 5)
    'ABC00123'

    >>> join_id('REQ.H', '-', 42, 4)
    'REQ.H-0042'

    >>> join_id('ABC', '-', 123, 0)
    'ABC-123'

    """
    return "{}{}{}".format(prefix, sep, str(number).zfill(digits))


def load_text(value):
    r"""Convert dumped text to the original string.

    >>> load_text("abc\ndef")
    'abc def'

    >>> load_text("list:\n\n- a\n- b\n")
    'list:\n\n- a\n- b'

    """
    return base.join(value)


def save_text(text, end='\n'):
    """Break a string at sentences and dump as literal YAML with wrapping."""
    return base.Literal(base.wrap(base.sbd(text, end=end)))


def load_level(value):
    """Convert an iterable, number, or level string to a tuple.

    >>> load_level("1.2.3")
    (1, 2, 3)

    >>> load_level(['4', '5'])
    (4, 5)

    >>> load_level(4.2)
    (4, 2)

    >>> load_level([7, 0, 0])
    (7, 0)

    >>> load_level(1)
    (1,)

    """
    # Correct for integers (e.g. 42) and floats (e.g. 4.2) in YAML
    if isinstance(value, (int, float)):
        value = str(value)

    # Split strings by periods
    if isinstance(value, str):
        nums = value.split('.')
    else:  # assume an iterable
        nums = value

    # Clean up multiple trailing zeros
    parts = [int(n) for n in nums]
    if parts[-1] == 0:
        while parts[-1] == 0:
            del parts[-1]
        parts.append(0)

    # Convert the level to a tuple
    return tuple(parts)


def save_level(parts):
    """Convert a level's part into non-quoted YAML value.

    >>> save_level((1,))
    1

    >>> save_level((1,0))
    1.0

    >>> save_level((1,0,0))
    '1.0.0'

    """
    # Join the level's parts
    level = '.'.join(str(n) for n in parts)

    # Convert formats to cleaner YAML formats
    if len(parts) == 1:
        level = int(level)
    elif len(parts) == 2 and not (level.endswith('0') and parts[-1]):
        level = float(level)

    return level
