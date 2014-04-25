"""Common classes and functions for the doorstop.core package."""


import re
import textwrap

import yaml

from doorstop import settings


class Literal(str):  # pylint: disable=R0904

    """Custom type for text which should be dumped in the literal style."""

    @staticmethod
    def representer(dumper, data):
        """Return a custom dumper that formats str in the literal style."""
        return dumper.represent_scalar('tag:yaml.org,2002:str', data,
                                       style='|' if data else '')

yaml.add_representer(Literal, Literal.representer)

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
