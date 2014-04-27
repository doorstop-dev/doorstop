"""Common classes and functions for the doorstop.core package."""


import re
import textwrap
import logging

import yaml

from doorstop.common import DoorstopError
from doorstop import settings


class Literal(str):  # pylint: disable=R0904

    """Custom type for text which should be dumped in the literal style."""

    @staticmethod
    def representer(dumper, data):
        """Return a custom dumper that formats str in the literal style."""
        return dumper.represent_scalar('tag:yaml.org,2002:str', data,
                                       style='|' if data else '')

yaml.add_representer(Literal, Literal.representer)


# ID #########################################################################


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


# text #######################################################################


def load_text(value):
    r"""Convert dumped text to the original string.

    >>> load_text("abc\ndef")
    'abc def'

    >>> load_text("list:\n\n- a\n- b\n")
    'list:\n\n- a\n- b'

    """
    return join(value)


def save_text(text, end='\n'):
    """Break a string at sentences and dump as literal YAML with wrapping."""
    return Literal(wrap(sbd(text, end=end)))


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


def sbd(text, end='\n'):
    r"""Replace sentence boundaries with newlines and append a newline.

    @param text: string to line break at sentences
    @param end: appended to the end of the update text

    >>> sbd("Hello, world!", end='')
    'Hello, world!'

    >>> sbd("Hello, world! How are you? I'm fine. Good.")
    "Hello, world!\nHow are you?\nI'm fine.\nGood.\n"

    """
    stripped = text.strip()
    if stripped:
        return RE_SENTENCE_BOUNDARIES.sub('\n', stripped) + end
    else:
        return ''


def wrap(text, width=settings.MAX_LINE_LENTH):
    r"""Wrap lines of text to the maximum line length.

    >>> wrap("Hello, world!", 9)
    'Hello,\nworld!'

    >>> wrap("How are you?\nI'm fine.\n", 14)
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


def join(text):
    r"""Convert single newlines (ignored by Markdown) to spaces.

    >>> join("abc\n123")
    'abc 123'

    >>> join("abc\n\n123")
    'abc\n\n123'

    >>> join("abc \n123")
    'abc 123'

    """
    return RE_MARKDOWN_SPACES.sub(r'\1 \3', text).strip()


# level #####################################################################


# TODO: use the Level class
class Level:  # pragma: no cover

    """Variable-length numerical outline level values.

    Level values cannot contain zeros. Zeros are reserved for
    identifying "heading" levels when written to file.
    """

    def __init__(self, value):
        parts = self.load_level(value)
        if parts[-1] == 0:
            self._parts = parts[:-1]
            self.heading = True
        else:
            self._parts = parts
            self.heading = False
        self._adjust()

    def __repr__(self):
        return "Level('{}')".format(str(self))

    def __str__(self):
        return '.'.join(str(n) for n in self.value)

    def __iter__(self):
        return iter(self._parts)

    def __len__(self):
        return len(self._parts)

    def __eq__(self, other):
        return self._parts == list(other) if other else False

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        return self._parts < list(other)

    def __hash__(self):
        return hash(self.value)

    def __add__(self, value):
        parts = list(self._parts)
        parts[-1] += value
        return Level(parts)

    def __iadd__(self, value):
        self._parts[-1] += value
        self._adjust()
        return self

    def __sub__(self, value):
        parts = list(self._parts)
        parts[-1] -= value
        return Level(parts)

    def __isub__(self, value):
        self._parts[-1] -= value
        self._adjust()
        return self

    def __rshift__(self, value):
        parts = list(self._parts) + [1] * value
        return Level(parts)

    def __irshift__(self, value):
        self._parts += [1] * value
        self._adjust()
        return self

    def __lshift__(self, value):
        parts = list(self._parts)[:-value]
        return Level(parts)

    def __ilshift__(self, value):
        self._parts = self._parts[:-value]
        self._adjust()
        return self

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
