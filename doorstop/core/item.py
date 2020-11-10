# SPDX-License-Identifier: LGPL-3.0-only

"""Representation of an item in a document."""

import functools
import linecache
import os
from typing import Any, List

from doorstop import common, settings
from doorstop.common import DoorstopError
from doorstop.core import editor
from doorstop.core.base import (
    BaseFileObject,
    add_item,
    auto_load,
    auto_save,
    delete_item,
    edit_item,
)
from doorstop.core.reference_finder import ReferenceFinder
from doorstop.core.types import UID, Level, Prefix, Stamp, Text, to_bool
from doorstop.core.yaml_validator import YamlValidator

log = common.logger(__name__)


def _convert_to_yaml(indent, prefix, value):
    """Convert value to YAML output format.

    :param indent: the indentation level
    :param prefix: the length of the prefix before the value, e.g. '- ' for
    lists or 'key: ' for keys
    :param value: the value to convert

    :return: the value converted to YAML output format

    """
    if isinstance(value, str):
        length = indent + prefix + len(value)
        if length > settings.MAX_LINE_LENGTH or '\n' in value:
            value = Text.save_text(value.strip())
        else:
            value = str(value)  # line is short enough as a string
    elif isinstance(value, list):
        value = [_convert_to_yaml(indent, 2, v) for v in value]
    elif isinstance(value, dict):
        value = {
            k: _convert_to_yaml(indent + 2, len(k) + 2, v) for k, v in value.items()
        }
    return value


def _convert_to_str(value, result):
    """Convert value to a string serialization.

    This function is independent of the YAML format and may be used for data
    which should be independent of the actual item storage format.  It depends
    only on the Python sorting function, type information, and string
    representation.

    :param value: the value to convert
    :param result: the current result of the string serialization

    :return: the updated result of the string serialization
    """
    if isinstance(value, list):
        result += "\\L"
        for v in value:
            result = _convert_to_str(v, result)
        return result
    if isinstance(value, dict):
        result += "\\D"
        for k in sorted(value.keys()):
            result = _convert_to_str(value[k], result)
        return result
    return result + "\\T" + str(type(value)) + "\\V" + str(value).replace("\\", "\\\\")


def requires_tree(func):
    """Require a tree reference."""

    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        if not self.tree:
            name = func.__name__
            log.critical("`{}` can only be called with a tree".format(name))
            return None
        return func(self, *args, **kwargs)

    return wrapped


class Item(BaseFileObject):  # pylint: disable=R0902
    """Represents an item file with linkable text."""

    EXTENSIONS = '.yml', '.yaml'

    DEFAULT_LEVEL = Level('1.0')
    DEFAULT_ACTIVE = True
    DEFAULT_NORMATIVE = True
    DEFAULT_DERIVED = False
    DEFAULT_REVIEWED = Stamp()
    DEFAULT_TEXT = Text()
    DEFAULT_REF = ""
    DEFAULT_HEADER = Text()

    def __init__(self, document, path, root=os.getcwd(), **kwargs):
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
        self.root: str = root
        self.document = document
        self.tree = kwargs.get('tree')
        self.auto = kwargs.get('auto', Item.auto)
        self.reference_finder = ReferenceFinder()
        self.yaml_validator = YamlValidator()
        # Set default values
        self._data['level'] = Item.DEFAULT_LEVEL
        self._data['active'] = Item.DEFAULT_ACTIVE
        self._data['normative'] = Item.DEFAULT_NORMATIVE
        self._data['derived'] = Item.DEFAULT_DERIVED
        self._data['reviewed'] = Item.DEFAULT_REVIEWED
        self._data['text'] = Item.DEFAULT_TEXT
        self._data['ref'] = Item.DEFAULT_REF
        self._data['references'] = None
        self._data['links'] = set()
        if settings.ENABLE_HEADERS:
            self._data['header'] = Item.DEFAULT_HEADER

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
    def new(
        tree, document, path, root, uid, level=None, auto=None
    ):  # pylint: disable=R0913
        """Create a new item.

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
        item = Item(document, path2, root=root, tree=tree, auto=False)
        item.level = level if level is not None else item.level  # type: ignore
        if auto or (auto is None and Item.auto):
            item.save()
        # Return the item
        return item

    def _set_attributes(self, attributes):
        """Set the item's attributes."""
        self.yaml_validator.validate_item_yaml(attributes)
        for key, value in attributes.items():
            if key == 'level':
                value = Level(value)
            elif key == 'active':
                value = to_bool(value)
            elif key == 'normative':
                value = to_bool(value)
            elif key == 'derived':
                value = to_bool(value)
            elif key == 'reviewed':
                value = Stamp(value)
            elif key == 'text':
                value = Text(value)
            elif key == 'ref':
                value = value.strip()
            elif key == 'references':
                stripped_value = []
                for ref_dict in value:
                    ref_type = ref_dict['type']
                    ref_path = ref_dict['path']

                    stripped_ref_dict = {"type": ref_type, "path": ref_path.strip()}
                    if 'keyword' in ref_dict:
                        ref_keyword = ref_dict['keyword']
                        stripped_ref_dict['keyword'] = ref_keyword

                    stripped_value.append(stripped_ref_dict)

                value = stripped_value
            elif key == 'links':
                value = set(UID(part) for part in value)
            elif key == 'header':
                value = Text(value)
            self._data[key] = value

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
        self._set_attributes(data)
        # Set meta attributes
        self._loaded = True

    @edit_item
    def save(self):
        """Format and save the item's properties to its file."""
        log.debug("saving {}...".format(repr(self)))
        # Format the data items
        data = self._yaml_data()
        # Dump the data to YAML
        text = self._dump(data)
        # Save the YAML to file
        self._write(text, self.path)
        # Set meta attributes
        self._loaded = True
        self.auto = True

    # properties #############################################################

    def _yaml_data(self):
        """Get all the item's data formatted for YAML dumping."""
        data = {}
        for key, value in self._data.items():
            if key == 'level':
                value = value.yaml
            elif key == 'text':
                value = value.yaml
            elif key == 'header':
                # Handle for case if the header is undefined in YAML
                if hasattr(value, 'yaml'):
                    value = value.yaml
                else:
                    value = ''
            elif key == 'ref':
                value = value.strip()
            elif key == 'references':
                if value is None:
                    continue
                stripped_value = []
                for el in value:
                    ref_dict = {"path": el["path"].strip(), "type": "file"}

                    if 'keyword' in el:
                        ref_dict['keyword'] = el['keyword']

                    stripped_value.append(ref_dict)

                value = stripped_value
            elif key == 'links':
                value = [{str(i): i.stamp.yaml} for i in sorted(value)]
            elif key == 'reviewed':
                value = value.yaml
            else:
                value = _convert_to_yaml(0, len(key) + 2, value)
            data[key] = value
        return data

    @property  # type: ignore
    @auto_load
    def data(self):
        """Load and get all the item's data formatted for YAML dumping."""
        return self._yaml_data()

    @property
    def uid(self):
        """Get the item's UID."""
        filename = os.path.basename(self.path)
        return UID(os.path.splitext(filename)[0])

    @property  # type: ignore
    @auto_load
    def level(self):
        """Get the item's level."""
        return self._data['level']

    @level.setter  # type: ignore
    @auto_save
    def level(self, value):
        """Set the item's level."""
        self._data['level'] = Level(value)

    @property
    def depth(self):
        """Get the item's heading order based on it's level."""
        return len(self.level)

    @property  # type: ignore
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

    @active.setter  # type: ignore
    @auto_save
    def active(self, value):
        """Set the item's active status."""
        self._data['active'] = to_bool(value)

    @property  # type: ignore
    @auto_load
    def derived(self):
        """Get the item's derived status.

        A derived item does not have links to items in its parent
        document, but should still be linked to by items in its child
        documents.

        """
        return self._data['derived']

    @derived.setter  # type: ignore
    @auto_save
    def derived(self, value):
        """Set the item's derived status."""
        self._data['derived'] = to_bool(value)

    @property  # type: ignore
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

    @normative.setter  # type: ignore
    @auto_save
    def normative(self, value):
        """Set the item's normative status."""
        self._data['normative'] = to_bool(value)

    @property
    def heading(self):
        """Indicate if the item is a heading.

        Headings have a level that ends in zero and are non-normative.

        """
        return self.level.heading and not self.normative

    @heading.setter  # type: ignore
    @auto_save
    def heading(self, value):
        """Set the item's heading status."""
        heading = to_bool(value)
        if heading and not self.heading:
            self.level.heading = True
            self.normative = False
        elif not heading and self.heading:
            self.level.heading = False
            self.normative = True

    @property  # type: ignore
    @auto_load
    def cleared(self):
        """Indicate if no links are suspect."""
        for uid, item in self._get_parent_uid_and_item():
            if uid.stamp != item.stamp():
                return False
        return True

    @property  # type: ignore
    @auto_load
    def reviewed(self):
        """Indicate if the item has been reviewed."""
        stamp = self.stamp(links=True)
        if self._data['reviewed'] == Stamp(True):
            self._data['reviewed'] = stamp
        return self._data['reviewed'] == stamp

    @reviewed.setter  # type: ignore
    @auto_save
    def reviewed(self, value):
        """Set the item's review status."""
        self._data['reviewed'] = Stamp(value)

    @property  # type: ignore
    @auto_load
    def text(self):
        """Get the item's text."""
        return self._data['text']

    @text.setter  # type: ignore
    @auto_save
    def text(self, value):
        """Set the item's text."""
        self._data['text'] = Text(value)

    @property  # type: ignore
    @auto_load
    def header(self):
        """Get the item's header."""
        if settings.ENABLE_HEADERS:
            return self._data['header']
        return None

    @header.setter  # type: ignore
    @auto_save
    def header(self, value):
        """Set the item's header."""
        if settings.ENABLE_HEADERS:
            self._data['header'] = Text(value)

    @property  # type: ignore
    @auto_load
    def ref(self):
        """Get the item's external file reference.

        An external reference can be part of a line in a text file or
        the filename of any type of file.

        """
        return self._data['ref']

    @ref.setter  # type: ignore
    @auto_save
    def ref(self, value):
        """Set the item's external file reference."""
        self._data['ref'] = str(value) if value else ""

    @property  # type: ignore
    @auto_load
    def references(self):
        """Get the item's external file references."""
        return self._data['references']

    @references.setter  # type: ignore
    @auto_save
    def references(self, value):
        """Set the item's external file references."""
        if value is not None:
            assert isinstance(value, list)
        self._data['references'] = value

    @property  # type: ignore
    @auto_load
    def links(self):
        """Get a list of the item UIDs this item links to."""
        return sorted(self._data['links'])

    @links.setter  # type: ignore
    @auto_save
    def links(self, value):
        """Set the list of item UIDs this item links to."""
        self._data['links'] = set(UID(v) for v in value)

    @property
    def parent_links(self):
        """Get a list of the item UIDs this item links to."""
        return self.links  # alias

    @parent_links.setter
    def parent_links(self, value):
        """Set the list of item UIDs this item links to."""
        self.links = value  # alias

    @requires_tree
    def _get_parent_uid_and_item(self):
        """Yield UID and item of all links of this item."""
        for uid in self.links:
            try:
                item = self.tree.find_item(uid)
            except DoorstopError:
                item = UnknownItem(uid)
                log.warning(item.exception)
            yield uid, item

    @property
    def parent_items(self):
        """Get a list of items that this item links to."""
        return [item for uid, item in self._get_parent_uid_and_item()]

    @property  # type: ignore
    @requires_tree
    def parent_documents(self):
        """Get a list of documents that this item's document should link to.

        .. note::

           A document only has one parent.

        """
        try:
            return [self.tree.find_document(self.document.prefix)]
        except DoorstopError:
            log.warning(Prefix.UNKNOWN_MESSAGE.format(self.document.prefix))
            return []

    # actions ################################################################

    @auto_save
    def set_attributes(self, attributes):
        """Set the item's attributes and save them."""
        self._set_attributes(attributes)

    def edit(self, tool=None, edit_all=True):
        """Open the item for editing.

        :param tool: path of alternate editor
        :param edit_all: True to edit the whole item,
            False to only edit the text.

        """
        # Lock the item
        if self.tree:
            self.tree.vcs.lock(self.path)
        # Edit the whole file in an editor
        if edit_all:
            self.save()
            editor.edit(self.path, tool=tool)
            self.load(True)
        # Edit only the text part in an editor
        else:
            # Edit the text in a temporary file
            edited_text = editor.edit_tmp_content(
                title=str(self.uid), original_content=str(self.text), tool=tool
            )
            # Save the text in the actual item file
            self.text = edited_text

    @auto_save
    def link(self, value):
        """Add a new link to another item UID.

        :param value: item or UID

        """
        uid = UID(value)
        log.info("linking to '{}'...".format(uid))
        self._data['links'].add(uid)

    @auto_save
    def unlink(self, value):
        """Remove an existing link by item UID.

        :param value: item or UID

        """
        uid = UID(value)
        try:
            self._data['links'].remove(uid)
        except KeyError:
            log.warning("link to {0} does not exist".format(uid))

    def is_reviewed(self):
        return self._data['reviewed']

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
            linecache.clearcache()
        # Search for the external reference
        return self.reference_finder.find_ref(self.ref, self.tree, self.path)

    @requires_tree
    def find_references(self):
        """Get the array of references. Check each references before returning.

        :raises: :class:`~doorstop.common.DoorstopError` when no
            reference is found

        :return: Array of tuples:
            (
              relative path to file or None (when no reference set),
              line number (when found in file) or None (when found as
              filename) or None (when no reference set)
            )

        """

        if not self.references:
            log.debug("no external reference to search for")
            return []
        if not settings.CACHE_PATHS:
            linecache.clearcache()

        references = []
        for ref_item in self.references:
            path = ref_item["path"]
            keyword = ref_item["keyword"] if "keyword" in ref_item else None

            reference = self.reference_finder.find_file_reference(
                path, self.root, self.tree, self.path, keyword
            )
            references.append(reference)
        return references

    def find_child_links(self, find_all=True):
        """Get a list of item UIDs that link to this item (reverse links).

        :param find_all: find all items (not just the first) before returning

        :return: list of found item UIDs

        """
        items, _ = self.find_child_items_and_documents(find_all=find_all)
        identifiers = [item.uid for item in items]
        return identifiers

    child_links = property(find_child_links)

    def find_child_items(self, find_all=True):
        """Get a list of items that link to this item.

        :param find_all: find all items (not just the first) before returning

        :return: list of found items

        """
        items, _ = self.find_child_items_and_documents(find_all=find_all)
        return items

    child_items = property(find_child_items)

    def find_child_documents(self):
        """Get a list of documents that should link to this item's document.

        :return: list of found documents

        """
        _, documents = self.find_child_items_and_documents(find_all=False)
        return documents

    child_documents = property(find_child_documents)

    def find_child_items_and_documents(self, document=None, tree=None, find_all=True):
        """Get lists of child items and child documents.

        :param document: document containing the current item
        :param tree: tree containing the current item
        :param find_all: find all items (not just the first) before returning

        :return: list of found items, list of all child documents

        """
        child_items: List[Item] = []
        child_documents: List[Any] = []  # `List[Document]`` creats an import cycle
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
                            if not item2.active:
                                item2 = UnknownItem(item2.uid)
                                log.warning(item2.exception)
                                child_items.append(item2)
                            else:
                                child_items.append(item2)
                                if not find_all and item2.active:
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

        if self.references:
            values.append(self.references)

        if links:
            values.extend(self.links)
        for key in self.document.extended_reviewed:
            if key in self._data:
                values.append(_convert_to_str(self._data[key], ""))
        return Stamp(*values)

    @auto_save
    def clear(self, parents=None):
        """Clear suspect links."""
        log.info("clearing suspect links...")
        for uid, item in self._get_parent_uid_and_item():
            if not parents or uid in parents:
                uid.stamp = item.stamp()

    @auto_save
    def review(self):
        """Mark the item as reviewed."""
        log.info("marking item as reviewed...")
        self._data['reviewed'] = self.stamp(links=True)

    @delete_item
    def delete(self, path=None):
        """Delete the item."""


class UnknownItem:
    """Represents an unknown item, which doesn't have a path."""

    UNKNOWN_PATH = '???'  # string to represent an unknown path

    normative = False  # do not include unknown items in traceability
    level = Item.DEFAULT_LEVEL

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

    def __lt__(self, other):
        return self.uid < other.uid

    @property
    def uid(self):
        """Get the item's UID."""
        return self._uid

    @property
    def relpath(self):
        """Get the unknown item's relative path string."""
        return "@{}{}".format(os.sep, self.UNKNOWN_PATH)

    def stamp(self):  # pylint: disable=R0201
        """Return an empty stamp."""
        return Stamp(None)
