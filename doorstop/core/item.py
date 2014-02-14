"""
Representation of items in a Doorstop document.
"""

import os
import re
import logging

import yaml

from doorstop.core.base import auto_load, auto_save, BaseFileObject
from doorstop import common
from doorstop.common import DoorstopError, DoorstopWarning, DoorstopInfo
from doorstop import settings


class Item(BaseFileObject):  # pylint: disable=R0904
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

        Internally, this constructor is also used to initialize new
        items by providing default properties.

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
            return self.id_relpath

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.path == other.path

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        return self.level < other.level

    @staticmethod
    def new(path, root, prefix, sep, digits, number, level, auto=None):  # pylint: disable=R0913
        """Create a new item.

        @param path: path to directory for the new item
        @param root: path to root of the project
        @param prefix: prefix for the new item
        @param sep: separator between prefix and number
        @param digits: number of digits for the new document
        @param number: number for the new item
        @param level: level for the new item (None for default)
        @param auto: enables automatic save

        @raise DoorstopError: if the item already exists
        """
        identifier = join_id(prefix, sep, number, digits)
        filename = identifier + Item.EXTENSIONS[0]
        path2 = os.path.join(path, filename)
        # Create the initial item file
        logging.debug("creating item file at {}...".format(path2))
        Item._new(path2, name='item')
        # Initialize the item
        item = Item(path2, root=root)
        item.auto = False
        item.level = level or Item.DEFAULT_LEVEL
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
        data = self._parse(text, self.path)
        # Store parsed data
        for key, value in data.items():
            if key == 'level':
                self._data['level'] = convert_level(value)
            elif key == 'active':
                self._data['active'] = bool(value)
            elif key == 'normative':
                self._data['normative'] = bool(value)
            elif key == 'derived':
                self._data['derived'] = bool(value)
            elif key == 'text':
                self._data['text'] = value.strip()
            elif key == 'ref':
                self._data['ref'] = value.strip()
            elif key == 'links':
                self._data['links'] = set(value)
            else:
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
                level = '.'.join(str(n) for n in value)
                if len(value) == 2:
                    level = float(level)
                data['level'] = level
            elif key == 'text':
                data['text'] = Literal(sbd(self._data['text']))
            elif key == 'ref':
                data['ref'] = value.strip()
            elif key == 'links':
                data['links'] = sorted(value)
            else:
                # TODO: dump long strings as Literal (and SBD?)
                data[key] = value
        # Dump the data to YAML
        dump = yaml.dump(data, default_flow_style=False)
        # Save the YAML to file
        self._write(dump, self.path)
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

    # TODO: think of a better name for this property
    @property
    def id_relpath(self):
        """Get the item's ID + relative path string."""
        return "{} ({})".format(self.id, self.relpath)

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
    def level(self, value):
        """Set the item's level."""
        self._data['level'] = convert_level(value)

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
    def normative(self, value):
        """Set the item's normative status."""
        self._data['normative'] = bool(value)

    @property
    def heading(self):
        """Indicates if the item is a heading.

        Headings have a level that ends in zero and are non-normative.
        """
        return self.level[-1] == 0 and not self.normative

    @heading.setter
    @auto_save
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
    def text(self, value):
        """Set the item's text."""
        self._data['text'] = value

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
    def ref(self, value):
        """Set the item's external file reference."""
        self._data['ref'] = value

    @property
    @auto_load
    def links(self):
        """Get a list of the item IDs this item links to."""
        return sorted(self._data['links'])

    @links.setter
    @auto_save
    def links(self, value):
        """Set the list of item IDs this item links to."""
        self._data['links'] = set(value)

    # actions ################################################################

    @auto_load
    @auto_save
    def add_link(self, item):
        """Add a new link to another item ID."""
        self._data['links'].add(item)

    @auto_load
    @auto_save
    def remove_link(self, item):
        """Remove an existing link by item ID."""
        try:
            self._data['links'].remove(item)
        except KeyError:
            logging.warning("link to {0} does not exist".format(item))

    def valid(self, document=None, tree=None):
        """Check the item for validity.

        @param document: Document containing the item
        @param tree: Tree containing the item

        @return: indication that the item is valid
        """
        # TODO: this could be common code with Item/Document/Tree
        valid = True
        # Display all issues
        for issue in self.issues(document=document, tree=tree):
            if isinstance(issue, DoorstopInfo):
                logging.info(issue)
            elif isinstance(issue, DoorstopWarning):
                logging.warning(issue)
            else:
                assert isinstance(issue, DoorstopError)
                logging.error(issue)
                valid = False
        # Return the result
        return valid

    def issues(self, document=None, tree=None):
        """Yield all the item's issues.

        @param document: Document containing the item
        @param tree: Tree containing the item

        @return: generator of DoorstopError, DoorstopWarning, DoorstopInfo
        """
        logging.info("checking item {}...".format(self))
        # Verify the file can be parsed
        self.load()
        # Skip inactive items
        if not self.active:
            logging.info("skipped inactive item: {}".format(self))
            return
        self.auto = False
        # Check text
        if not self.text and not self.ref:
            yield DoorstopWarning("no text")
        # Check external references
        try:
            self.find_ref(ignored=tree.vcs.ignored if tree else None)
        except DoorstopError as exc:
            yield exc
        # Check links
        if not self.normative and self.links:
            yield DoorstopWarning("non-normative, but has links")
        # Check links against the document
        if document:
            yield from self._issues_document(document)
        # Check links against the tree
        if tree:
            yield from self._issues_tree(tree)
        # Check links against both document and tree
        if document and tree:
            yield from self._issues_both(document, tree)
        # Reformat the file
        self.save()

    def _issues_document(self, document):
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
                if prefix != document.parent:
                    # this is only 'info' because a document is allowed
                    # to contain items with a different prefix, but
                    # Doorstop will not create items like this
                    msg = "linked to non-parent item: {}".format(identifier)
                    yield DoorstopInfo(msg)

    def _issues_tree(self, tree):
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
        self._data['links'] = identifiers

    def _issues_both(self, document, tree):
        """Yield all the item's issues against its document and tree."""
        # Verify an item is being linked to (reverse links)
        if self.normative:
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
        super().delete(self.path)


# YAML representer classes ###################################################

class Literal(str):  # pylint: disable=R0904
    """Custom type for text which should be dumped in the literal style."""

    @staticmethod
    def representer(dumper, data):
        """Return a custom dumper that formats str in the literal style."""
        return dumper.represent_scalar('tag:yaml.org,2002:str', data,
                                       style='|' if data else '')

yaml.add_representer(Literal, Literal.representer)


# attribute formatters #######################################################

def split_id(text):
    """Split an item's ID into a prefix and number.

    >>> split_id('ABC00123')
    ('ABC', 123)

    >>> split_id('ABC.HLR_01-00123')
    ('ABC.HLR_01', 123)

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

    """
    return "{}{}{}".format(prefix, sep, str(number).zfill(digits))


def convert_level(text):
    """Convert a level string to a tuple.

    >>> convert_level("1.2.3")
    (1, 2, 3)

    >>> convert_level(['4', '5'])
    (4, 5)

    >>> convert_level(4.2)
    (4, 2)

    >>> convert_level([7, 0, 0])
    (7, 0)

    """
    # Correct for integers (42) and floats (4.2) in YAML
    if isinstance(text, int) or isinstance(text, float):
        text = str(text)
    # Split strings by periods
    if isinstance(text, str):
        nums = text.split('.')
    else:
        nums = text
    # Clean up multiple trailing zeros
    parts = [int(n) for n in nums]
    if parts[-1] == 0:
        while parts[-1] == 0:
            del parts[-1]
        parts.append(0)
    # Ensure the top level always a heading (ends in a zero)
    if len(parts) == 1:
        parts.append(0)
    # Convert the level to a tuple
    return tuple(parts)


# http://en.wikipedia.org/wiki/Sentence_boundary_disambiguation
SBD = re.compile(r"((?<=[a-z0-9][.?!])|(?<=[a-z0-9][.?!]\"))(\s|\r\n)(?=\"?[A-Z])")  # pylint: disable=C0301


def sbd(text):
    """Replace sentence boundaries with newlines and append a newline.

    >>> sbd("Hello, world!")
    'Hello, world!\\n'

    >>> sbd("Hello, world! How are you? I'm fine. Good.")
    "Hello, world!\\nHow are you?\\nI'm fine.\\nGood.\\n"

    """
    stripped = text.strip()
    if stripped:
        return SBD.sub('\n', stripped) + '\n'
    else:
        return ''
