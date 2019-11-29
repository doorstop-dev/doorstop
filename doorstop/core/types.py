# SPDX-License-Identifier: LGPL-3.0-only

"""Common classes and functions for the `doorstop.core` package."""

import hashlib
import os
import re
from base64 import urlsafe_b64encode
from typing import Union

import yaml

from doorstop import common, settings
from doorstop.common import DoorstopError

log = common.logger(__name__)


class Prefix(str):
    """Unique document prefixes."""

    UNKNOWN_MESSAGE = "no document with prefix: {}"

    def __new__(cls, value=""):
        if isinstance(value, Prefix):
            return value
        else:
            if str(value).lower() in settings.RESERVED_WORDS:
                raise DoorstopError("cannot use reserved word: %s" % value)
            obj = super().__new__(cls, Prefix.load_prefix(value))  # type: ignore
            return obj

    def __repr__(self):
        return "Prefix('{}')".format(self)

    def __hash__(self):  # pylint: disable=useless-super-delegation
        return super().__hash__()

    def __eq__(self, other):
        if other in settings.RESERVED_WORDS:
            return False
        if not isinstance(other, Prefix):
            other = Prefix(other)
        return self.lower() == other.lower()

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        return self.lower() < other.lower()

    @staticmethod
    def load_prefix(value):
        """Convert a value to a prefix.

        >>> Prefix.load_prefix("abc 123")
        'abc'
        """
        return str(value).split(' ')[0] if value else ''


class UID:
    """Unique item ID built from document prefix and number."""

    UNKNOWN_MESSAGE = "no{k} item with UID: {u}"  # k='parent'|'child', u=UID

    def __new__(cls, *args, **kwargs):  # pylint: disable=W0613
        if args and isinstance(args[0], UID):
            return args[0]
        else:
            return super().__new__(cls)

    def __init__(self, *values, stamp=None):
        """Initialize an UID using a string, dictionary, or set of parts.

        Option 1:

        :param *values: UID + optional stamp ("UID:stamp")
        :param stamp: stamp of :class:`~doorstop.core.item.Item` (if known)

        Option 2:

        :param *values: {UID: stamp}
        :param stamp: stamp of :class:`~doorstop.core.item.Item` (if known)

        Option 3:

        :param *values: prefix, separator, number, digit count
        param stamp: stamp of :class:`~doorstop.core.item.Item` (if known)

        Option 4:

        :param *values: prefix, separator, name
        param stamp: stamp of :class:`~doorstop.core.item.Item` (if known)

        """
        if values and isinstance(values[0], UID):
            self.stamp: Stamp = stamp or values[0].stamp
            return
        self.stamp = stamp or Stamp()
        # Join values
        if len(values) == 0:  # pylint: disable=len-as-condition
            self.value = ''
        elif len(values) == 1:
            value = values[0]
            if isinstance(value, str) and ':' in value:
                # split UID:stamp into a dictionary
                pair = value.rsplit(':', 1)
                value = {pair[0]: pair[1]}
            if isinstance(value, dict):
                first = list(value.items())[0]
                self.value = str(first[0])
                self.stamp = self.stamp or Stamp(first[1])
            else:
                self.value = str(value) if values[0] else ''
        elif len(values) == 4:
            # pylint: disable=no-value-for-parameter
            self.value = UID.join_uid_4(*values)
        elif len(values) == 3:
            # pylint: disable=no-value-for-parameter
            self.value = UID.join_uid_3(*values)
        else:
            raise TypeError("__init__() takes 1, 3, or 4 positional arguments")
        # Split values
        self._prefix, self._number, self._name, self._exc = UID.split_uid(self.value)

    def __repr__(self):
        if self.stamp:
            return "UID('{}', stamp='{}')".format(self.value, self.stamp)
        else:
            return "UID('{}')".format(self.value)

    def __str__(self):
        return self.value

    def __hash__(self):
        return hash((self._prefix, self._number, self._name))

    def __eq__(self, other):
        if not other:
            return False
        if not isinstance(other, UID):
            other = UID(other)
        try:
            self.check()
            other.check()
            # pylint: disable=protected-access
            return (
                self._prefix == other._prefix
                and self._number == other._number
                and self._name == other._name
            )
        except DoorstopError:
            return self.value.lower() == other.value.lower()

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        try:
            self.check()
            other.check()
            # pylint: disable=protected-access
            if self._prefix == other._prefix:
                if self._number == other._number:
                    return self._name < other._name
                else:
                    return self._number < other._number
            else:
                return self._prefix < other._prefix
        except DoorstopError:
            return self.value < other.value

    @property
    def prefix(self):
        """Get the UID's prefix."""
        self.check()
        return self._prefix

    @property
    def number(self):
        """Get the UID's number."""
        self.check()
        return self._number

    @property
    def name(self):
        """Get the UID's name."""
        self.check()
        return self._name

    @property
    def string(self):
        """Convert the UID and stamp to a single string."""
        if self.stamp:
            return "{}:{}".format(self.value, self.stamp)
        else:
            return "{}".format(self.value)

    def check(self):
        """Verify an UID is valid."""
        if self._exc:
            raise self._exc  # pylint: disable=raising-bad-type

    @staticmethod
    def split_uid(value):
        """Split an item's UID string into a prefix, number, name, and exception.

        >>> UID.split_uid('ABC00123')
        (Prefix('ABC'), 123, '', None)

        >>> UID.split_uid('ABC.HLR_01-00123')
        (Prefix('ABC.HLR_01'), 123, '', None)

        >>> UID.split_uid('REQ2-001')
        (Prefix('REQ2'), 1, '', None)

        >>> UID.split_uid('REQ2-NAME')
        (Prefix('REQ2'), -1, 'NAME', None)

        >>> UID.split_uid('REQ2-NAME007')
        (Prefix('REQ2'), -1, 'NAME007', None)

        >>> UID.split_uid('REQ2-123NAME')
        (Prefix('REQ2'), -1, '123NAME', None)

        """
        m = re.match("([\\w.-]+)[" + settings.SEP_CHARS + "](\\w+)", value)
        if m:
            try:
                num = int(m.group(2))
                return Prefix(m.group(1)), num, '', None
            except ValueError:
                return Prefix(m.group(1)), -1, m.group(2), None
        m = re.match(r"([\w.-]*\D)(\d+)", value)
        if m:
            num = m.group(2)
            return Prefix(m.group(1).rstrip(settings.SEP_CHARS)), int(num), '', None
        return None, None, None, DoorstopError("invalid UID: {}".format(value))

    @staticmethod
    def join_uid_4(prefix, sep, number, digits):
        """Join the four parts of an item's UID into a string.

        >>> UID.join_uid_4('ABC', '', 123, 5)
        'ABC00123'

        >>> UID.join_uid_4('REQ.H', '-', 42, 4)
        'REQ.H-0042'

        >>> UID.join_uid_4('ABC', '-', 123, 0)
        'ABC-123'

        """
        return "{}{}{}".format(prefix, sep, str(number).zfill(digits))

    @staticmethod
    def join_uid_3(prefix, sep, name):
        """Join the three parts of an item's UID into a string."""
        return "{}{}{}".format(prefix, sep, name)


class _Literal(str):
    """Custom type for text which should be dumped in the literal style."""

    @staticmethod
    def representer(dumper, data):
        """Return a custom dumper that formats str in the literal style."""
        return dumper.represent_scalar(
            'tag:yaml.org,2002:str', data, style='|' if data else ''
        )


yaml.add_representer(_Literal, _Literal.representer)


class Text(str):
    """Markdown text paragraph."""

    def __new__(cls, value=""):
        assert not isinstance(value, Text)
        obj = super(Text, cls).__new__(cls, Text.load_text(value))  # type: ignore
        return obj

    @property
    def yaml(self):
        """Get the value to be used in YAML dumping."""
        return Text.save_text(self)

    @staticmethod
    def load_text(value):
        r"""Convert dumped text to the original string.

        >>> Text.load_text("abc\ndef")
        'abc\ndef'

        >>> Text.load_text("list:\n\n- a\n- b\n")
        'list:\n\n- a\n- b'

        """
        if not value:
            return ""
        text_value = re.sub('^\n+', '', value)
        text_value = re.sub('\n+$', '', text_value)
        text_value = '\n'.join([s.rstrip() for s in text_value.split('\n')])
        return text_value

    @staticmethod
    def save_text(text, end='\n'):
        """Break a string at sentences and dump as wrapped literal YAML."""
        if text:
            return _Literal(text + end)
        else:
            return ''


class Level:
    """Variable-length numerical outline level values.

    Level values cannot contain zeros. Zeros are reserved for
    identifying "heading" levels when written to file.
    """

    def __init__(self, value=None, heading=None):
        """Initialize an item level from a sequence of numbers.

        :param value: sequence of int, float, or period-delimited string
        :param heading: force a heading value (or inferred from trailing zero)

        """
        if isinstance(value, Level):
            self._parts = list(value)
            self.heading: bool = value.heading
        else:
            parts = self.load_level(value)
            if parts and parts[-1] == 0:
                self._parts = parts[:-1]
                self.heading = True
            else:
                self._parts = parts
                self.heading = False
        self.heading = self.heading if heading is None else heading
        if not value:
            self._adjust()

    def __repr__(self):
        if self.heading:
            level = '.'.join(str(n) for n in self._parts)
            return "Level('{}', heading=True)".format(level)
        else:
            return "Level('{}')".format(str(self))

    def __str__(self):
        return '.'.join(str(n) for n in self.value)

    def __iter__(self):
        return iter(self._parts)

    def __len__(self):
        return len(self._parts)

    def __eq__(self, other):
        if other:
            parts = list(other)
            if parts and not parts[-1]:
                parts.pop(-1)
            return self._parts == parts
        else:
            return False

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        return self._parts < list(other)

    def __gt__(self, other):
        return self._parts > list(other)

    def __le__(self, other):
        return self._parts <= list(other)

    def __ge__(self, other):
        return self._parts >= list(other)

    def __hash__(self):
        return hash(self.value)

    def __add__(self, value):
        parts = list(self._parts)
        parts[-1] += value
        return Level(parts, heading=self.heading)

    def __iadd__(self, value):
        self._parts[-1] += value
        self._adjust()
        return self

    def __sub__(self, value):
        parts = list(self._parts)
        parts[-1] -= value
        return Level(parts, heading=self.heading)

    def __isub__(self, value):
        self._parts[-1] -= value
        self._adjust()
        return self

    def __rshift__(self, value):
        if value > 0:
            parts = list(self._parts) + [1] * value
            return Level(parts, heading=self.heading)
        else:
            return self.__lshift__(abs(value))

    def __irshift__(self, value):
        if value > 0:
            self._parts += [1] * value
            self._adjust()
            return self
        else:
            return self.__ilshift__(abs(value))

    def __lshift__(self, value):
        if value >= 0:
            parts = list(self._parts)
            if value:
                parts = parts[:-value]
            return Level(parts, heading=self.heading)
        else:
            return self.__rshift__(abs(value))

    def __ilshift__(self, value):
        if value >= 0:
            if value:
                self._parts = self._parts[:-value]
            self._adjust()
            return self
        else:
            return self.__irshift__(abs(value))

    @property
    def value(self):
        """Get a tuple for the level's value with heading indications."""
        parts = self._parts + ([0] if self.heading else [])
        return tuple(parts)

    @property
    def yaml(self):
        """Get the value to be used in YAML dumping."""
        return self.save_level(self.value)

    def _adjust(self):
        """Force all non-zero values."""
        old = self
        new = None
        if not self._parts:
            new = Level(1)
        elif 0 in self._parts:
            new = Level(1 if not n else n for n in self._parts)
        if new:
            msg = "minimum level reached, reseting: {} -> {}".format(old, new)
            log.warning(msg)
            self._parts = list(new.value)

    @staticmethod
    def load_level(value):
        """Convert an iterable, number, or level string to a tuple.

        >>> Level.load_level("1.2.3")
        [1, 2, 3]

        >>> Level.load_level(['4', '5'])
        [4, 5]

        >>> Level.load_level(4.2)
        [4, 2]

        >>> Level.load_level([7, 0, 0])
        [7, 0]

        >>> Level.load_level(1)
        [1]

        """
        # Correct for default values
        if not value:
            value = 1
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
        if parts and parts[-1] == 0:
            while parts and parts[-1] == 0:
                del parts[-1]
            parts.append(0)

        return parts

    @staticmethod
    def save_level(parts) -> Union[int, float, str]:
        """Convert a level's part into non-quoted YAML value.

        >>> Level.save_level((1,))
        1

        >>> Level.save_level((1,0))
        1.0

        >>> Level.save_level((1,0,0))
        '1.0.0'

        """
        # Join the level's parts
        level = '.'.join(str(n) for n in parts)

        # Convert formats to cleaner YAML formats
        if len(parts) == 1:
            return int(level)
        elif len(parts) == 2 and not (level.endswith('0') and parts[-1]):
            return float(level)

        return level

    def copy(self):
        """Return a copy of the level."""
        return Level(self.value)


class Stamp:
    """Hashed content for change tracking.

    :param values: one of the following:

        - objects to hash as strings
        - existing string stamp
        - `True` - manually-confirmed matching hash, to be replaced later
        - `False` | `None` | (nothing) - manually-confirmed mismatching hash

    """

    def __init__(self, *values):
        if not values:
            self.value = None
            return
        if len(values) == 1:
            value = values[0]
            if to_bool(value):
                self.value = True
                return
            if not value:
                self.value = None
                return
            if isinstance(value, str):
                self.value = value
                return
        self.value = self.digest(*values)

    def __repr__(self):
        return "Stamp({})".format(repr(self.value))

    def __str__(self):
        if isinstance(self.value, str):
            return self.value
        else:
            return ''

    def __bool__(self):
        return bool(self.value)

    def __eq__(self, other):
        return self.value == other

    def __ne__(self, other):
        return not self == other

    @property
    def yaml(self):
        """Get the value to be used in YAML dumping."""
        return self.value

    @staticmethod
    def digest(*values) -> str:
        """Hash the values for later comparison."""
        hsh = hashlib.sha256()
        for value in values:
            hsh.update(str(value).encode())
        return urlsafe_b64encode(hsh.digest()).decode('utf-8')


def to_bool(obj):
    """Convert a boolean-like object.

    >>> to_bool(1)
    True

    >>> to_bool(0)
    False

    >>> to_bool(' True ')
    True

    >>> to_bool('F')
    False

    """
    if isinstance(obj, str):
        return obj.lower().strip() in ('yes', 'true', 'enabled', '1')
    else:
        return bool(obj)


def is_tree(obj):
    """Determine if the object is a tree-like."""
    return hasattr(obj, 'documents')


def is_document(obj):
    """Determine if the object is a document-like."""
    return hasattr(obj, 'items')


def is_item(obj):
    """Determine if the object is item-like."""
    return hasattr(obj, 'text')


def iter_documents(obj, path, ext):
    """Get an iterator if documents from a tree or document-like object."""
    if is_tree(obj):
        # a tree
        log.debug("iterating over tree...")
        for document in obj.documents:
            path2 = os.path.join(path, document.prefix + ext)
            yield document, path2
    else:
        # assume a document-like object
        log.debug("iterating over document-like object...")
        yield obj, path


def iter_items(obj):
    """Get an iterator of items from from an item, list, or document."""
    if is_document(obj):
        # a document
        log.debug("iterating over document...")
        return (i for i in obj.items)
    try:
        # an iterable (of items)
        log.debug("iterating over document-like object...")
        return iter(obj)
    except TypeError:
        # assume an item
        log.debug("iterating over an item (in a container)...")
        return [obj]
