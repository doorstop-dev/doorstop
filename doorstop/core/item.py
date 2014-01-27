"""
Representation of items in a Doorstop document.
"""

import os
import re
import functools
import logging

import yaml

from doorstop import common
from doorstop.common import DoorstopError, DoorstopWarning, DoorstopInfo
from doorstop.settings import SEP_CHARS


def auto_load(func):
    """Decorator for methods that should automatically load from file."""
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        """Wrapped method to call self.load() before execution."""
        self.load()
        return func(self, *args, **kwargs)
    return wrapped


def auto_save(func):
    """Decorator for methods that should automatically save to file."""
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        """Wrapped method to call self.save() after execution."""
        result = func(self, *args, **kwargs)
        if self.auto:
            self.save()
        return result

    return wrapped


class Item(object):  # pylint: disable=R0904
    """Represents a file with linkable text that is part of a document."""

    EXTENSIONS = '.yml', '.yaml'

    DEFAULT_LEVEL = (1, 0)
    DEFAULT_ACTIVE = True
    DEFAULT_NORMATIVE = True
    DEFAULT_DERIVED = False
    DEFAULT_TEXT = ""
    DEFAULT_REF = ""

    auto = True  # set to False to delay automatic save until explicit save

    def __init__(self, path, root=os.getcwd()):
        """Load an item from an existing file.

        Internally, this constructor is also used to initialize new
        items by providing default properties.

        @param path: path to Item file
        @param root: path to root of project
        """
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
        # Initialize Item
        self.path = path
        self.root = root
        self._exists = True
        self._data = {}
        # Set defaults
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
        if common.VERBOSITY <= 1:
            return self.id
        else:
            return self.id_relpath

    def __eq__(self, other):
        return isinstance(other, Item) and self.path == other.path

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        return self.level < other.level

    @staticmethod
    def new(path, root, prefix, sep, number, digits, level, auto=None):  # pylint: disable=R0913
        """Create a new item.

        @param path: path to directory for the new item
        @param root: path to root of the project
        @param prefix: prefix for the new item
        @param sep: separator between prefix and number
        @param number: number for the new item
        @param digits: number of digits for the new document
        @param level: level for the new item (None for default)
        @param auto: enables automatic save

        @raise DoorstopError: if the item already exists
        """
        identifier = join_id(prefix, sep, number, digits)
        filename = identifier + Item.EXTENSIONS[0]
        path2 = os.path.join(path, filename)
        # Create the initial item file
        logging.debug("creating item file at {}...".format(path2))
        Item._new(path2)
        # Initialize the item
        item = Item(path2, root=root)
        item.auto = False
        item.level = level or Item.DEFAULT_LEVEL
        item.auto = Item.auto if auto is None else auto
        # Return the new item
        return item

    @staticmethod
    def _new(path):  # pragma: no cover, integration test
        """Create a new item file.

        @param config: path to new item file
        """
        if os.path.exists(path):
            raise DoorstopError("item already exists: {}".format(path))
        with open(path, 'w'):
            pass  # just touch the file

    def load(self, reload=False):
        """Load the item's properties from a file."""
        if getattr(self, '_loaded', False) and not reload:
            return
        logging.debug("loading {}...".format(repr(self)))
        # Read the YAML from file
        text = self._read()
        # Parse the YAML data
        try:
            data = yaml.load(text) or {}
        except yaml.scanner.ScannerError as error:  # pylint: disable=E1101
            msg = "invalid contents: {}:\n{}".format(self, error)
            raise DoorstopError(msg)
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
        setattr(self, '_loaded', True)

    def _read(self):  # pragma: no cover, integration test
        """Read text from the file."""
        if not self._exists:
            raise DoorstopError("cannot load from deleted: {}".format(self))
        with open(self.path, 'rb') as infile:
            return infile.read().decode('UTF-8')

    def save(self):
        """Format and save the item's properties to a file."""
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
                data[key] = value
        # Dump the data to YAML
        dump = yaml.dump(data, default_flow_style=False)
        # Save the YAML to file
        self._write(dump)
        # Set meta attributes
        setattr(self, '_loaded', False)
        self.auto = True

    def _write(self, text):  # pragma: no cover, integration test
        """Write text to the file."""
        if not self._exists:
            raise DoorstopError("cannot save to deleted: {}".format(self))
        with open(self.path, 'wb') as outfile:
            outfile.write(bytes(text, 'UTF-8'))

    # standard attributes ####################################################

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
        """Get the item's ID and relative path string."""
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
        """Get the item level."""
        return self._data['level']

    @level.setter
    @auto_save
    def level(self, level):
        """Set the item's level."""
        self._data['level'] = convert_level(level)

    @property
    def depth(self):
        """Get the heading order based on the level."""
        level = list(self.level)
        while level[-1] == 0:
            del level[-1]
        return len(level)

    @property
    @auto_load
    def active(self):
        """Indicates the item should be considered for linking.

        Inactive items are intended to be used for:
         - future requirements
         - temporarily disabled requirements or tests
         - externally implemented requirements

        """
        return self._data['active']

    @active.setter
    @auto_save
    def active(self, status):
        """Set the item's active status."""
        self._data['active'] = bool(status)

    @property
    @auto_load
    def normative(self):
        """Get the item's normative status.

        A non-normative item should not have or be linked to.
        Non-normative items are intended to be used for:
         - headings
         - comments

        """
        return self._data['normative']

    @normative.setter
    @auto_save
    def normative(self, status):
        """Set the item's normative status."""
        self._data['normative'] = bool(status)

    @property
    @auto_load
    def derived(self):
        """Get the item's derived status.

        A derived item does not have links to items in its parent
        document, but should still be linked to by items in its child
        document.
        """
        return self._data['derived']

    @derived.setter
    @auto_save
    def derived(self, status):
        """Set the item's derived status."""
        self._data['derived'] = bool(status)

    @property
    def header(self):
        """Indicates if the item is a header."""
        return self.level[-1] == 0 and not self.normative

    @property
    @auto_load
    def text(self):
        """Get the item's text."""
        return self._data['text']

    @text.setter
    @auto_save
    def text(self, text):
        """Set the item's text."""
        self._data['text'] = text

    @property
    @auto_load
    def ref(self):
        """Get the item's external file reference."""
        return self._data['ref']

    @ref.setter
    @auto_save
    def ref(self, ref):
        """Set the item's external file reference."""
        self._data['ref'] = ref

    @property
    @auto_load
    def links(self):
        """Get the items this item links to."""
        return sorted(self._data['links'])

    @links.setter
    @auto_save
    def links(self, links):
        """Set the items this item links to."""
        self._data['links'] = set(links)

    # extended attributes ####################################################

    @auto_load
    def get(self, name, default=None):
        """Get an extended attribute."""
        if hasattr(self, name):
            cname = self.__class__.__name__
            msg = "'{n}' can be accessed from {c}.{n}".format(n=name, c=cname)
            logging.info(msg)
            return getattr(self, name)
        else:
            return self._data.get(name, default)

    @auto_load
    @auto_save
    def set(self, name, value):
        """Set an extended attribute."""
        if hasattr(self, name):
            cname = self.__class__.__name__
            msg = "'{n}' can be set from {c}.{n}".format(n=name, c=cname)
            logging.info(msg)
            return setattr(self, name, value)
        else:
            self._data[name] = value

    # actions ################################################################

    @auto_load
    @auto_save
    def add_link(self, item):
        """Add a new link to another item."""
        self._data['links'].add(item)

    @auto_load
    @auto_save
    def remove_link(self, item):
        """Remove an existing link."""
        try:
            self._data['links'].remove(item)
        except KeyError:
            logging.warning("link to {0} does not exist".format(item))

    def valid(self, document=None, tree=None, ignored=None):
        """Check the item for validity.

        @param document: document to validate the item
        @param tree: tree to validate the item
        @param ignored: function to determine if a path should be skipped

        @return: indication that the item is valid
        """
        valid = True
        # Display all issues
        for issue in self.iter_issues(document=document, tree=tree,
                                      ignored=ignored):
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

    def iter_issues(self, document=None, tree=None, ignored=None):
        """Yield all the item's issues.

        @param document: document to validate the item
        @param tree: tree to validate the item
        @param ignored: function to determine if a path should be skipped

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
            self.find_ref(ignored=ignored)
        except DoorstopError as exc:
            yield exc
        # Check links
        if not self.normative and self.links:
            yield DoorstopWarning("non-normative, but has links")
        # Check links against the document
        if document:
            yield from self._iter_issues_document(document)
        # Check links against the tree
        if tree:
            yield from self._iter_issues_tree(tree)
        # Reformat the file
        self.save()

    def _iter_issues_document(self, document):
        """Yield all the item's issues against its document."""
        # Verify an item has upward links
        if all((document.parent,
                self.normative,
                not self.derived)) and not self.links:
            msg = "no links to parent document: {}".format(document.parent)
            yield DoorstopWarning(msg)
        # Verify an item's links are to the correct parent
        for identifier in self.links:
            prefix = split_id(identifier)[0]
            if prefix.lower() != document.parent.lower():
                msg = "linked to non-parent item: {}".format(identifier)
                yield DoorstopInfo(msg)

    def _iter_issues_tree(self, tree):
        """Yield all the item's issues against the full tree."""
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
        # Verify an item is being linked to (reverse links)
        rlinks = []
        children = []
        for document in tree:
            if document.parent == self.prefix:
                children.append(document)
                for item in document:
                    if self.id in item.links:
                        rlinks.append(item.id)
        if rlinks:
            msg = "reverse links: {}".format(', '.join(rlinks))
            logging.debug(msg)
        elif self.normative:
            for child in children:
                msg = "no links from child document: {}".format(child)
                yield DoorstopWarning(msg)

    def find_ref(self, root=None, ignored=None):
        """Find the external file reference and line number.

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

    def delete(self):
        """Delete the item from the file system."""
        logging.info("deleting {}...".format(self.path))
        os.remove(self.path)
        self._exists = False  # prevent future access


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
    prefix = match.group(1).rstrip(SEP_CHARS)
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
    # Ensure the top level always a header (ends in a zero)
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
