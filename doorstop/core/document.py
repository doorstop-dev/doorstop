# SPDX-License-Identifier: LGPL-3.0-only

"""Representation of a collection of items."""

import os
import re
from collections import OrderedDict
from itertools import chain
from typing import Dict, List

import yaml

from doorstop import common, settings
from doorstop.common import DoorstopError, DoorstopInfo, DoorstopWarning
from doorstop.core.base import (
    BaseFileObject,
    BaseValidatable,
    add_document,
    auto_load,
    auto_save,
    delete_document,
    edit_document,
)
from doorstop.core.item import Item
from doorstop.core.types import UID, Level, Prefix
from doorstop.core.validators.item_validator import ItemValidator

log = common.logger(__name__)


class Document(BaseValidatable, BaseFileObject):  # pylint: disable=R0902
    """Represents a document directory containing an outline of items."""

    CONFIG = '.doorstop.yml'
    SKIP = '.doorstop.skip'  # indicates this document should be skipped
    ASSETS = 'assets'
    INDEX = 'index.yml'

    DEFAULT_PREFIX = Prefix('REQ')
    DEFAULT_SEP = ''
    DEFAULT_DIGITS = 3

    def __init__(self, path, root=os.getcwd(), **kwargs):
        """Initialize a document from an exiting directory.

        :param path: path to document directory
        :param root: path to root of project

        """
        super().__init__()
        # Ensure the directory is valid
        if not os.path.isfile(os.path.join(path, Document.CONFIG)):
            relpath = os.path.relpath(path, root)
            msg = "no {} in {}".format(Document.CONFIG, relpath)
            raise DoorstopError(msg)
        # Initialize the document
        self.path = path
        self.root = root
        self.tree = kwargs.get('tree')
        self.auto = kwargs.get('auto', Document.auto)
        # Set default values
        self._attribute_defaults = None
        self._data['prefix'] = Document.DEFAULT_PREFIX
        self._data['sep'] = Document.DEFAULT_SEP
        self._data['digits'] = Document.DEFAULT_DIGITS
        self._data['parent'] = None  # the root document does not have a parent
        self._extended_reviewed: List[str] = []
        self._items: List[Item] = []
        self._itered = False
        self.children: List[Document] = []

    def __repr__(self):
        return "Document('{}')".format(self.path)

    def __str__(self):
        if common.verbosity < common.STR_VERBOSITY:
            return self.prefix
        else:
            return "{} ({})".format(self.prefix, self.relpath)

    def __iter__(self):
        yield from self._iter()

    def __len__(self):
        return len(list(i for i in self._iter() if i.active))

    def __bool__(self):
        """Even empty documents should be considered truthy."""
        return True

    @staticmethod
    @add_document
    def new(
        tree, path, root, prefix, sep=None, digits=None, parent=None, auto=None
    ):  # pylint: disable=R0913,C0301
        """Create a new document.

        :param tree: reference to tree that contains this document

        :param path: path to directory for the new document
        :param root: path to root of the project
        :param prefix: prefix for the new document

        :param sep: separator between prefix and numbers
        :param digits: number of digits for the new document
        :param parent: parent UID for the new document
        :param auto: automatically save the document

        :raises: :class:`~doorstop.common.DoorstopError` if the document
            already exists

        :return: new :class:`~doorstop.core.document.Document`

        """
        # Check separator
        if sep and sep not in settings.SEP_CHARS:
            raise DoorstopError("invalid UID separator '{}'".format(sep))

        config = os.path.join(path, Document.CONFIG)

        # Check for an existing document
        if os.path.exists(config):
            raise DoorstopError("document already exists: {}".format(path))

        # Create the document directory
        Document._create(config, name='document')

        # Initialize the document
        document = Document(path, root=root, tree=tree, auto=False)
        document.prefix = (  # type: ignore
            prefix if prefix is not None else document.prefix
        )
        document.sep = sep if sep is not None else document.sep  # type: ignore
        document.digits = (  # type: ignore
            digits if digits is not None else document.digits
        )
        document.parent = (  # type: ignore
            parent if parent is not None else document.parent
        )
        if auto or (auto is None and Document.auto):
            document.save()

        # Return the document
        return document

    def _load_with_include(self, yamlfile):
        """Load the YAML file and process input tags."""
        # Read text from file
        text = self._read(yamlfile)
        # Parse YAML data from text
        class IncludeLoader(yaml.SafeLoader):
            def include(self, node):
                container = IncludeLoader.filenames[0]  # type: ignore
                dirname = os.path.dirname(container)
                filename = os.path.join(dirname, self.construct_scalar(node))
                IncludeLoader.filenames.insert(0, filename)  # type: ignore
                try:
                    with open(filename, 'r') as f:
                        data = yaml.load(f, IncludeLoader)
                except Exception as ex:
                    msg = "include in '{}' failed: {}".format(container, ex)
                    raise DoorstopError(msg)
                IncludeLoader.filenames.pop()  # type: ignore
                return data

        IncludeLoader.add_constructor('!include', IncludeLoader.include)
        IncludeLoader.filenames = [yamlfile]  # type: ignore
        return self._load(text, yamlfile, loader=IncludeLoader)

    def load(self, reload=False):
        """Load the document's properties from its file."""
        if self._loaded and not reload:
            return
        log.debug("loading {}...".format(repr(self)))
        data = self._load_with_include(self.config)
        # Store parsed data
        sets = data.get('settings', {})
        for key, value in sets.items():
            try:
                if key == 'prefix':
                    self._data[key] = Prefix(value)
                elif key == 'sep':
                    self._data[key] = value.strip()
                elif key == 'parent':
                    self._data[key] = value.strip()
                elif key == 'digits':
                    self._data[key] = int(value)
                else:
                    msg = "unexpected document setting '{}' in: {}".format(
                        key, self.config
                    )
                    raise DoorstopError(msg)
            except (AttributeError, TypeError, ValueError):
                msg = "invalid value for '{}' in: {}".format(key, self.config)
                raise DoorstopError(msg)
        # Store parsed attributes
        attributes = data.get('attributes', {})
        for key, value in attributes.items():
            if key == 'defaults':
                self._attribute_defaults = value
            elif key == 'reviewed':
                self._extended_reviewed = sorted(set(v for v in value))
            else:
                msg = "unexpected attributes configuration '{}' in: {}".format(
                    key, self.config
                )
                raise DoorstopError(msg)
        # Set meta attributes
        self._loaded = True
        if reload:
            list(self._iter(reload=reload))

    @edit_document
    def save(self):
        """Save the document's properties to its file."""
        log.debug("saving {}...".format(repr(self)))
        # Format the data items
        data = {}
        sets = {}
        for key, value in self._data.items():
            if key == 'prefix':
                sets[key] = str(value)
            elif key == 'parent':
                if value:
                    sets[key] = value
            else:
                sets[key] = value
        data['settings'] = sets
        # Save the attributes
        attributes = {}
        if self._attribute_defaults:
            attributes['defaults'] = self._attribute_defaults
        if self._extended_reviewed:
            attributes['reviewed'] = self._extended_reviewed
        if attributes:
            data['attributes'] = attributes
        # Dump the data to YAML
        text = self._dump(data)
        # Save the YAML to file
        self._write(text, self.config)
        # Set meta attributes
        self._loaded = False
        self.auto = True

    def _iter(self, reload=False):
        """Yield the document's items."""
        if self._itered and not reload:
            msg = "iterating document {}'s loaded items...".format(self)
            log.debug(msg)
            yield from list(self._items)
            return
        log.info("loading document {}'s items...".format(self))
        # Reload the document's item
        self._items = []
        for dirpath, dirnames, filenames in os.walk(self.path):
            for dirname in list(dirnames):
                path = os.path.join(dirpath, dirname, Document.CONFIG)
                if os.path.exists(path):
                    path = os.path.dirname(path)
                    dirnames.remove(dirname)
                    log.trace(  # type: ignore
                        "skipped embedded document: {}".format(path)
                    )
            for filename in filenames:
                path = os.path.join(dirpath, filename)
                try:
                    item = Item(self, path, root=self.root, tree=self.tree)
                except DoorstopError:
                    pass  # skip non-item files
                else:
                    self._items.append(item)
                    if reload:
                        try:
                            item.load(reload=reload)
                        except Exception:
                            log.error("Unable to load: %s", item)
                            raise
                    if settings.CACHE_ITEMS and self.tree:
                        self.tree._item_cache[  # pylint: disable=protected-access
                            item.uid
                        ] = item
                        log.trace("cached item: {}".format(item))  # type: ignore
        # Set meta attributes
        self._itered = True
        # Yield items
        yield from list(self._items)

    def copy_assets(self, dest):
        """Copy the contents of the assets directory."""
        if not self.assets:
            return
        common.copy_dir_contents(self.assets, dest)

    # properties #############################################################

    @property
    def config(self):
        """Get the path to the document's file."""
        return os.path.join(self.path, Document.CONFIG)

    @property
    def assets(self):
        """Get the path to the document's assets if they exist else `None`."""
        path = os.path.join(self.path, Document.ASSETS)
        return path if os.path.isdir(path) else None

    @property  # type: ignore
    @auto_load
    def prefix(self):
        """Get the document's prefix."""
        return self._data['prefix']

    @prefix.setter  # type: ignore
    @auto_save
    @auto_load
    def prefix(self, value):
        """Set the document's prefix."""
        self._data['prefix'] = Prefix(value)
        # TODO: should the new prefix be applied to all items?

    @property  # type: ignore
    @auto_load
    def extended_reviewed(self):
        """Get the document's extended reviewed attribute keys."""
        return self._extended_reviewed

    @property  # type: ignore
    @auto_load
    def sep(self):
        """Get the prefix-number separator to use for new item UIDs."""
        return self._data['sep']

    @sep.setter  # type: ignore
    @auto_save
    @auto_load
    def sep(self, value):
        """Set the prefix-number separator to use for new item UIDs."""
        # TODO: raise a specific exception for invalid separator characters?
        assert not value or value in settings.SEP_CHARS
        self._data['sep'] = value.strip()
        # TODO: should the new separator be applied to all items?

    @property  # type: ignore
    @auto_load
    def digits(self):
        """Get the number of digits to use for new item UIDs."""
        return self._data['digits']

    @digits.setter  # type: ignore
    @auto_save
    @auto_load
    def digits(self, value):
        """Set the number of digits to use for new item UIDs."""
        self._data['digits'] = value
        # TODO: should the new digits be applied to all items?

    @property  # type: ignore
    @auto_load
    def parent(self):
        """Get the document's parent document prefix."""
        return self._data['parent']

    @parent.setter  # type: ignore
    @auto_save
    @auto_load
    def parent(self, value):
        """Set the document's parent document prefix."""
        self._data['parent'] = str(value) if value else ""

    @property
    def items(self):
        """Get an ordered list of active items in the document."""
        return sorted(i for i in self._iter() if i.active)

    @property
    def depth(self):
        """Return the maximum item level depth."""
        return max(item.depth for item in self)

    @property
    def next_number(self):
        """Get the next item number for the document."""
        try:
            number = max(item.uid.number for item in self) + 1
        except ValueError:
            number = 1
        log.debug("next number (local): {}".format(number))

        if self.tree and self.tree.request_next_number:
            remote_number = 0
            while remote_number is not None and remote_number < number:
                if remote_number:
                    log.warning("server is behind, requesting next number...")
                remote_number = self.tree.request_next_number(self.prefix)
                log.debug("next number (remote): {}".format(remote_number))
            if remote_number:
                number = remote_number

        return number

    @property
    def skip(self):
        """Indicate the document should be skipped."""
        return os.path.isfile(os.path.join(self.path, Document.SKIP))

    @property
    def index(self):
        """Get the path to the document's index if it exists else `None`."""
        path = os.path.join(self.path, Document.INDEX)
        return path if os.path.isfile(path) else None

    @index.setter
    def index(self, value):
        """Create or update the document's index."""
        if value:
            path = os.path.join(self.path, Document.INDEX)
            log.info("creating {} index...".format(self))
            common.write_lines(self._lines_index(self.items), path)

    @index.deleter
    def index(self):
        """Delete the document's index if it exists."""
        log.info("deleting {} index...".format(self))
        common.delete(self.index)

    # actions ################################################################

    # decorators are applied to methods in the associated classes
    def add_item(self, number=None, level=None, reorder=True, defaults=None, name=None):
        """Create a new item for the document and return it.

        :param number: desired item number
        :param level: desired item level
        :param reorder: update levels of document items

        :return: added :class:`~doorstop.core.item.Item`

        """
        uid = None
        if name is None:
            number = max(number or 0, self.next_number)
            log.debug("next number: {}".format(number))
            uid = UID(self.prefix, self.sep, number, self.digits)
        else:
            try:
                uid = UID(self.prefix, self.sep, int(name), self.digits)
            except ValueError:
                if not self.sep:
                    msg = "cannot add item with name '{}' to document '{}' without a separator".format(
                        name, self.prefix
                    )
                    raise DoorstopError(msg)
                if self.sep not in settings.SEP_CHARS:
                    msg = "cannot add item with name '{}' to document '{}' with an invalid separator '{}'".format(
                        name, self.prefix, self.sep
                    )
                    raise DoorstopError(msg)
                uid = UID(self.prefix, self.sep, name)
                if uid.prefix != self.prefix or uid.name != name:
                    msg = "invalid item name '{}'".format(name)
                    raise DoorstopError(msg)

        try:
            last = self.items[-1]
        except IndexError:
            next_level = level
        else:
            if level:
                next_level = level
            elif last.level.heading:
                next_level = last.level >> 1
                next_level.heading = False
            else:
                next_level = last.level + 1
        log.debug("next level: {}".format(next_level))

        # Load more defaults before the item is created to avoid partially
        # constructed items in case the loading fails.
        more_defaults = self._load_with_include(defaults) if defaults else None

        item = Item.new(self.tree, self, self.path, self.root, uid, level=next_level)
        if self._attribute_defaults:
            item.set_attributes(self._attribute_defaults)
        if more_defaults:
            item.set_attributes(more_defaults)
        if level and reorder:
            self.reorder(keep=item)
        return item

    # decorators are applied to methods in the associated classes
    def remove_item(self, value, reorder=True):
        """Remove an item by its UID.

        :param value: item or UID
        :param reorder: update levels of document items

        :raises: :class:`~doorstop.common.DoorstopError` if the item
            cannot be found

        :return: removed :class:`~doorstop.core.item.Item`

        """
        uid = UID(value)
        item = self.find_item(uid)
        item.delete()
        if reorder:
            self.reorder()
        return item

    # decorators are applied to methods in the associated classes
    def reorder(self, manual=True, automatic=True, start=None, keep=None, _items=None):
        """Reorder a document's items.

        Two methods are using to create the outline order:

        - manual: specify the order using an updated index file
        - automatic: shift duplicate levels and compress gaps

        :param manual: enable manual ordering using the index (if one exists)

        :param automatic: enable automatic ordering (after manual ordering)
        :param start: level to start numbering (None = use current start)
        :param keep: item or UID to keep over duplicates

        """
        # Reorder manually
        if manual and self.index:
            log.info("reordering {} from index...".format(self))
            self._reorder_from_index(self, self.index)
            del self.index
        # Reorder automatically
        if automatic:
            log.info("reordering {} automatically...".format(self))
            items = _items or self.items
            keep = self.find_item(keep) if keep else None
            self._reorder_automatic(items, start=start, keep=keep)

    @staticmethod
    def _lines_index(items):
        """Generate (pseudo) YAML lines for the document index."""
        yield '#' * settings.MAX_LINE_LENGTH
        yield '# THIS TEMPORARY FILE WILL BE DELETED AFTER DOCUMENT REORDERING'
        yield '# MANUALLY INDENT, DEDENT, & MOVE ITEMS TO THEIR DESIRED LEVEL'
        yield '# A NEW ITEM WILL BE ADDED FOR ANY UNKNOWN IDS, i.e. - new: '
        yield '# THE COMMENT WILL BE USED AS THE ITEM TEXT FOR NEW ITEMS'
        yield '# CHANGES WILL BE REFLECTED IN THE ITEM FILES AFTER CONFIRMATION'
        yield '#' * settings.MAX_LINE_LENGTH
        yield ''
        yield "initial: {}".format(items[0].level if items else 1.0)
        yield "outline:"
        for item in items:
            space = "    " * item.depth
            lines = item.text.strip().splitlines()
            comment = lines[0] if lines else ""
            line = space + "- {u}: # {c}".format(u=item.uid, c=comment)
            if len(line) > settings.MAX_LINE_LENGTH:
                line = line[: settings.MAX_LINE_LENGTH - 3] + '...'
            yield line

    @staticmethod
    def _read_index(path):
        """Load the index, converting comments to text entries for each item."""
        with open(path, 'r', encoding='utf-8') as stream:
            text = stream.read()
        yaml_text = []
        for line in text.split('\n'):
            m = re.search(r'(\s+)(- [\w\d-]+\s*): # (.+)$', line)
            if m:
                prefix = m.group(1)
                uid = m.group(2)
                item_text = m.group(3).replace('"', '\\"')
                yaml_text.append('{p}{u}:'.format(p=prefix, u=uid))
                yaml_text.append('    {p}- text: "{t}"'.format(p=prefix, t=item_text))
            else:
                yaml_text.append(line)
        return common.load_yaml('\n'.join(yaml_text), path)

    @staticmethod
    def _reorder_from_index(document, path):
        """Reorder a document's item from the index."""
        data = document._read_index(path)  # pylint: disable=protected-access
        # Read updated values
        initial = data.get('initial', 1.0)
        outline = data.get('outline', [])
        # Update levels
        level = Level(initial)
        ids_after_reorder: List[str] = []
        Document._reorder_section(outline, level, document, ids_after_reorder)
        for item in document.items:
            if item.uid not in ids_after_reorder:
                log.info('Deleting %s', item.uid)
                item.delete()

    @staticmethod
    def _reorder_section(section, level, document, list_of_ids):
        """Recursive function to reorder a section of an outline.

        :param section: recursive `list` of `dict` loaded from document index
        :param level: current :class:`~doorstop.core.types.Level`
        :param document: :class:`~doorstop.core.document.Document` to order

        """
        if isinstance(section, dict):  # a section

            # Get the item and subsection
            uid = list(section.keys())[0]
            if uid == 'text':
                return
            subsection = section[uid]

            # An item is a header if it has a subsection
            level.heading = False
            item_text = ''
            if isinstance(subsection, str):
                item_text = subsection
            elif isinstance(subsection, list):
                if 'text' in subsection[0]:
                    item_text = subsection[0]['text']
                    if len(subsection) > 1:
                        level.heading = True

            try:
                item = document.find_item(uid)
                item.level = level
                log.info("Found ({}): {}".format(uid, level))
                list_of_ids.append(uid)
            except DoorstopError:
                item = document.add_item(level=level, reorder=False)
                list_of_ids.append(item.uid)
                if level.heading:
                    item.normative = False
                item.text = item_text
                log.info("Created ({}): {}".format(item.uid, level))

            # Process the heading's subsection
            if subsection:
                Document._reorder_section(subsection, level >> 1, document, list_of_ids)

        elif isinstance(section, list):  # a list of sections

            # Process each subsection
            for index, subsection in enumerate(section):
                Document._reorder_section(
                    subsection, level + index, document, list_of_ids
                )

    @staticmethod
    def _reorder_automatic(items, start=None, keep=None):
        """Reorder a document's items automatically.

        :param items: items to reorder
        :param start: level to start numbering (None = use current start)
        :param keep: item to keep over duplicates

        """
        nlevel = plevel = None
        for clevel, item in Document._items_by_level(items, keep=keep):
            log.debug("current level: {}".format(clevel))
            # Determine the next level
            if not nlevel:
                # Use the specified or current starting level
                nlevel = Level(start) if start else clevel
                nlevel.heading = clevel.heading
                log.debug("next level (start): {}".format(nlevel))
            else:
                # Adjust the next level to be the same depth
                if len(clevel) > len(nlevel):
                    nlevel >>= len(clevel) - len(nlevel)
                    log.debug("matched current indent: {}".format(nlevel))
                elif len(clevel) < len(nlevel):
                    nlevel <<= len(nlevel) - len(clevel)
                    # nlevel += 1
                    log.debug("matched current dedent: {}".format(nlevel))
                nlevel.heading = clevel.heading
                # Check for a level jump
                _size = min(len(clevel.value), len(plevel.value))
                for index in range(max(_size - 1, 1)):
                    if clevel.value[index] > plevel.value[index]:
                        nlevel <<= len(nlevel) - 1 - index
                        nlevel += 1
                        nlevel >>= len(clevel) - len(nlevel)
                        msg = "next level (jump): {}".format(nlevel)
                        log.debug(msg)
                        break
                # Check for a normal increment
                else:
                    if len(nlevel) <= len(plevel):
                        nlevel += 1
                        msg = "next level (increment): {}".format(nlevel)
                        log.debug(msg)
                    else:
                        msg = "next level (indent/dedent): {}".format(nlevel)
                        log.debug(msg)
            # Apply the next level
            if clevel == nlevel:
                log.info("{}: {}".format(item, clevel))
            else:
                log.info("{}: {} to {}".format(item, clevel, nlevel))
            item.level = nlevel.copy()
            # Save the current level as the previous level
            plevel = clevel.copy()

    @staticmethod
    def _items_by_level(items, keep=None):
        """Iterate through items by level with the kept item first."""
        # Collect levels
        levels: Dict[Level, List[Item]] = OrderedDict()
        for item in items:
            if item.level in levels:
                levels[item.level].append(item)
            else:
                levels[item.level] = [item]
        # Reorder levels
        for level, items_at_level in levels.items():
            # Reorder items at this level
            if keep in items_at_level:
                # move the kept item to the front of the list
                log.debug("keeping {} level over duplicates".format(keep))
                items_at_level.remove(keep)
                items_at_level.insert(0, keep)
            for item in items_at_level:
                yield level, item

    def find_item(self, value, _kind=''):
        """Return an item by its UID.

        :param value: item or UID

        :raises: :class:`~doorstop.common.DoorstopError` if the item
            cannot be found

        :return: matching :class:`~doorstop.core.item.Item`

        """
        uid = UID(value)
        for item in self:
            if item.uid == uid:
                if item.active:
                    return item
                else:
                    log.trace("item is inactive: {}".format(item))  # type: ignore

        raise DoorstopError("no matching{} UID: {}".format(_kind, uid))

    def get_issues(
        self, skip=None, document_hook=None, item_hook=None
    ):  # pylint: disable=unused-argument
        """Yield all the document's issues.

        :param skip: list of document prefixes to skip
        :param item_hook: function to call for custom item validation

        :return: generator of :class:`~doorstop.common.DoorstopError`,
                              :class:`~doorstop.common.DoorstopWarning`,
                              :class:`~doorstop.common.DoorstopInfo`

        """
        assert document_hook is None
        skip = [] if skip is None else skip
        hook = item_hook if item_hook else lambda **kwargs: []

        if self.prefix in skip:
            log.info("skipping document %s...", self)
            return
        else:
            log.info("checking document %s...", self)

        # Check for items
        items = self.items
        if not items:
            yield DoorstopWarning("no items")
            return

        # Reorder or check item levels
        if settings.REORDER:
            self.reorder(_items=items)
        elif settings.CHECK_LEVELS:
            yield from self._get_issues_level(items)

        item_validator = ItemValidator()

        # Check each item
        for item in items:

            # Check item
            for issue in chain(
                hook(item=item, document=self, tree=self.tree),
                item_validator.get_issues(item, skip=skip),
            ):

                # Prepend the item's UID to yielded exceptions
                if isinstance(issue, Exception):
                    yield type(issue)("{}: {}".format(item.uid, issue))

    @staticmethod
    def _get_issues_level(items):
        """Yield all the document's issues related to item level."""
        prev = items[0] if items else None
        for item in items[1:]:
            puid = prev.uid
            plev = prev.level
            nuid = item.uid
            nlev = item.level
            log.debug("checking level {} to {}...".format(plev, nlev))
            # Duplicate level
            if plev == nlev:
                uids = sorted((puid, nuid))
                msg = "duplicate level: {} ({}, {})".format(plev, *uids)
                yield DoorstopWarning(msg)
            # Skipped level
            length = min(len(plev.value), len(nlev.value))
            for index in range(length):
                # Types of skipped levels:
                #         1. over: 1.0 --> 1.2
                #         2. out: 1.1 --> 3.0
                if (
                    nlev.value[index] - plev.value[index] > 1
                    or
                    # 3. over and out: 1.1 --> 2.2
                    (
                        plev.value[index] != nlev.value[index]
                        and index + 1 < length
                        and nlev.value[index + 1] not in (0, 1)
                    )
                ):
                    msg = "skipped level: {} ({}), {} ({})".format(
                        plev, puid, nlev, nuid
                    )
                    yield DoorstopInfo(msg)
                    break
            prev = item

    @delete_document
    def delete(self, path=None):
        """Delete the document and its items."""
        for item in self:
            item.delete()
        # the document is deleted in the decorated method
