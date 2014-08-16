"""Common classes and functions for the doorstop.core package."""

import os
import re
import textwrap
import logging

import yaml

from doorstop.common import DoorstopError
from doorstop import settings


class Prefix(str):  # pylint: disable=R0904

    """Unique document prefixes."""

    UNKNOWN_MESSGE = "no document with prefix: {}"

    def __new__(cls, value=""):
        if isinstance(value, Prefix):
            return value
        else:
            if str(value).lower() in settings.RESERVED_WORDS:
                raise DoorstopError("cannot use reserved word: %s" % value)
            obj = super().__new__(cls, Prefix.load_prefix(value))
            return obj

    def __repr__(self):
        return "Prefix('{}')".format(self)

    def __hash__(self):
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


class ID(object):

    """Unique item identifier."""

    UNKNOWN_MESSAGE = "no{k} item with ID: {i}"  # k='parent'|'child'|'', i=ID

    def __new__(cls, *values):
        if values and isinstance(values[0], ID):
            return values[0]
        else:
            return super().__new__(cls)

    def __init__(self, *values):
        """Initialize an ID using a string or set of parts.

        Option 1:

        :param *values: string representation of ID

        Option 2:

        :param *values: prefix, separator, number, digit count

        """
        # Join values
        if len(values) == 0:
            self.value = ''
        elif len(values) == 1:
            self.value = str(values[0]) if values[0] else ''
        elif len(values) == 4:
            self.value = ID.join_id(*values)
        else:
            raise TypeError("__init__() takes 1 or 4 positional arguments")
        # Split values
        try:
            parts = ID.split_id(self.value)
            self._prefix = Prefix(parts[0])
            self._number = parts[1]
        except ValueError:
            self._prefix = self._number = None
            self._exc = DoorstopError("invalid ID: {}".format(self.value))
        else:
            self._exc = None

    def __repr__(self):
        return "ID('{}')".format(self.value)

    def __str__(self):
        return self.value

    def __hash__(self):
        return hash((self._prefix, self._number))

    def __eq__(self, other):
        if not other:
            return False
        if not isinstance(other, ID):
            other = ID(other)
        try:
            return all((self.prefix == other.prefix,
                        self.number == other.number))
        except DoorstopError:
            return self.value.lower() == other.value.lower()

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        try:
            if self.prefix == other.prefix:
                return self.number < other.number
            else:
                return self.prefix < other.prefix
        except DoorstopError:
            return self.value < other.value

    @property
    def prefix(self):
        """Get the ID's prefix."""
        self.check()
        return self._prefix

    @property
    def number(self):
        """Get the ID's number."""
        self.check()
        return self._number

    def check(self):
        """Verify an ID is valid."""
        if self._exc:
            raise self._exc

    @staticmethod
    def split_id(text):
        """Split an item's ID string into a prefix and number.

        >>> ID.split_id('ABC00123')
        ('ABC', 123)

        >>> ID.split_id('ABC.HLR_01-00123')
        ('ABC.HLR_01', 123)

        >>> ID.split_id('REQ2-001')
        ('REQ2', 1)

        """
        match = re.match(r"([\w.-]*\D)(\d+)", text)
        if not match:
            raise ValueError("unable to parse ID: {}".format(text))
        prefix = match.group(1).rstrip(settings.SEP_CHARS)
        number = int(match.group(2))
        return prefix, number

    @staticmethod
    def join_id(prefix, sep, number, digits):
        """Join the parts of an item's ID into a string.

        >>> ID.join_id('ABC', '', 123, 5)
        'ABC00123'

        >>> ID.join_id('REQ.H', '-', 42, 4)
        'REQ.H-0042'

        >>> ID.join_id('ABC', '-', 123, 0)
        'ABC-123'

        """
        return "{}{}{}".format(prefix, sep, str(number).zfill(digits))


class Literal(str):  # pylint: disable=R0904

    """Custom type for text which should be dumped in the literal style."""

    @staticmethod
    def representer(dumper, data):
        """Return a custom dumper that formats str in the literal style."""
        return dumper.represent_scalar('tag:yaml.org,2002:str', data,
                                       style='|' if data else '')

yaml.add_representer(Literal, Literal.representer)


class Text(str):  # pylint: disable=R0904

    """Markdown text paragraph."""

    def __new__(cls, value=""):
        assert not isinstance(value, Text)
        obj = super(Text, cls).__new__(cls, Text.load_text(value))
        return obj

    @property
    def yaml(self):
        """Get the value to be used in YAML dumping."""
        return Text.save_text(self)

    @staticmethod
    def load_text(value):
        r"""Convert dumped text to the original string.

        >>> Text.load_text("abc\ndef")
        'abc def'

        >>> Text.load_text("list:\n\n- a\n- b\n")
        'list:\n\n- a\n- b'

        """
        return Text.join(value if value else "")

    @staticmethod
    def save_text(text, end='\n'):
        """Break a string at sentences and dump as wrapped literal YAML."""
        return Literal(Text.wrap(Text.sbd(str(text), end=end)))

    # Based on: http://en.wikipedia.org/wiki/Sentence_boundary_disambiguation
    RE_SENTENCE_BOUNDARIES = re.compile(r"""

    (            # one of the following:

      (?<=[a-z)][.?!])      # lowercase letter + punctuation
      |
      (?<=[a-z0-9][.?!]\")  # lowercase letter/number + punctuation + quote

    )

    (\s)          # any whitespace

    (?=\"?[A-Z])  # optional quote + an upppercase letter

    """, re.VERBOSE)

    @staticmethod
    def sbd(text, end='\n'):
        r"""Replace sentence boundaries with newlines and append a newline.

        :param text: string to line break at sentences
        :param end: appended to the end of the update text

        >>> Text.sbd("Hello, world!", end='')
        'Hello, world!'

        >>> Text.sbd("Hello, world! How are you? I'm fine. Good.")
        "Hello, world!\nHow are you?\nI'm fine.\nGood.\n"

        """
        stripped = text.strip()
        if stripped:
            return Text.RE_SENTENCE_BOUNDARIES.sub('\n', stripped) + end
        else:
            return ''

    @staticmethod
    def wrap(text, width=settings.MAX_LINE_LENTH):
        r"""Wrap lines of text to the maximum line length.

        >>> Text.wrap("Hello, world!", 9)
        'Hello,\nworld!'

        >>> Text.wrap("How are you?\nI'm fine.\n", 14)
        "How are you?\nI'm fine.\n"

        """
        end = '\n' if '\n' in text else ''
        lines = []
        for line in text.splitlines():
            # wrap longs lines of text compensating for the 2-space indent
            lines.extend(textwrap.wrap(line, width=width - 2,
                                       replace_whitespace=True))
            if not line.strip():
                lines.append('')
        return '\n'.join(lines) + end

    RE_MARKDOWN_SPACES = re.compile(r"""

    ([^\n ])  # any character but a newline or space

    (\ ?\n)     # optional space + single newline

    (?!      # none of the following:

      (?:\s)       # whitespace
      |
      (?:[-+*]\s)  # unordered list separator + whitespace
      |
      (?:\d+\.\s)  # number + period + whitespace

    )

    ([^\n])  # any character but a newline

    """, re.VERBOSE | re.IGNORECASE)

    @staticmethod
    def join(text):
        r"""Convert single newlines (ignored by Markdown) to spaces.

        >>> Text.join("abc\n123")
        'abc 123'

        >>> Text.join("abc\n\n123")
        'abc\n\n123'

        >>> Text.join("abc \n123")
        'abc 123'

        """
        return Text.RE_MARKDOWN_SPACES.sub(r'\1 \3', text).strip()


class Level(object):

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
            self.heading = value.heading
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
            return "Level('{}', heading=True)".format(level, self.heading)
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
            logging.warning(msg)
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
    def save_level(parts):
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
            level = int(level)
        elif len(parts) == 2 and not (level.endswith('0') and parts[-1]):
            level = float(level)

        return level

    def copy(self):
        """Return a copy of the level."""
        return Level(self.value)


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
        return obj.lower().strip() in ('yes', 'true', 'enabled')
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
        logging.debug("iterating over tree...")
        for document in obj.documents:
            path2 = os.path.join(path, document.prefix + ext)
            yield document, path2
    else:
        # assume a document-like object
        logging.debug("iterating over document-like object...")
        yield obj, path


def iter_items(obj):
    """Get an iterator of items from from an item, list, or document."""
    if is_document(obj):
        # a document
        logging.debug("iterating over document...")
        return (i for i in obj.items if i.active)
    try:
        # an iterable
        logging.debug("iterating over document-like object...")
        return iter(obj)
    except TypeError:
        # an item
        logging.debug("iterating over an item (in a container)...")
        return [obj]
