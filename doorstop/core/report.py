"""
Doorstop reporting functionality.
"""

import os
import shutil
import textwrap

import markdown

from doorstop.common import DoorstopError

CSS = os.path.join(os.path.dirname(__file__), 'files', 'doorstop.css')


def publish(document, path, ext, **kwargs):
    """Publish a document to a given format.


    """
    if ext in FORMAT:
        with open(path, 'wb') as outfile:
            for line in iter_lines(document, ext, **kwargs):
                outfile.write(bytes(line + '\n', 'utf-8'))
        if ext == '.html':
            directory = os.path.dirname(path)
            copy_css(directory)
    else:
        raise DoorstopError("unknown format: {}".format(ext))


def iter_lines(document, ext, **kwargs):
    """Yield lines for a report in the specified format.



    """
    if ext in FORMAT:
        yield from FORMAT[ext](document, **kwargs)
    else:
        raise DoorstopError("unknown format: {}".format(ext))


def iter_lines_text(document, indent=8, width=79, ignored=None):
    """Yield lines for a text report.

    @param document: Document to publish
    @param indent: number of spaces to indent text
    @param width: maximum line length
    @param ignored: function to determine if a path should be skipped

    @return: iterator of lines of text
    """
    for item in document.items:

        level = '.'.join(str(l) for l in item.level)
        if level.endswith('.0') and len(level) > 3:
            level = level[:-2]

        if item.header:

            # Level and Text
            yield "{l:<{s}}{t}".format(l=level, s=indent, t=item.text)

        else:

            # Level and ID
            yield "{l:<{s}}{i}".format(l=level, s=indent, i=item.id)

            # Text
            if item.text:
                yield ""  # break before text
                for line in item.text.splitlines():
                    yield from _chunks(line, width, indent)

                    if not line:  # pragma: no cover - integration test
                        yield ""  # break between paragraphs

            # Reference
            if item.ref:
                yield ""  # break before reference
                path, line = item.find_ref(ignored=ignored)
                path = path.replace('\\', '/')  # always write unix-style paths
                ref = "Reference: {p} (line {l})".format(p=path, l=line)
                yield from _chunks(ref, width, indent)

            # Links
            if item.links:
                yield ""  # break before links
                links = "Links: " + ', '.join(item.links)
                yield from _chunks(links, width, indent)

        yield ""  # break between items


def _chunks(text, width, indent):
    """Yield wrapped lines of text."""
    yield from textwrap.wrap(text, width,
                             initial_indent=' ' * indent,
                             subsequent_indent=' ' * indent)


def iter_lines_markdown(document, ignored=None):
    """Yield lines for a Markdown report.

    @param document: Document to publish
    @param ignored: function to determine if a path should be skipped

    @return: iterator of lines of text
    """
    for item in document.items:

        heading = '#' * item.depth
        level = '.'.join(str(l) for l in item.level)
        if level.endswith('.0') and len(level) > 3:
            level = level[:-2]

        if item.header:

            # Level and Text
            yield "{h} {l} {t}".format(h=heading, l=level, t=item.text)

        else:

            # Level and ID
            yield "{h} {l} {i}".format(h=heading, l=level, i=item.id)

            # Text
            if item.text:
                yield ""  # break before text
                yield from item.text.splitlines()

            # Reference
            if item.ref:
                yield ""  # break before reference
                path, line = item.find_ref(ignored=ignored)
                path = path.replace('\\', '/')  # always use unix-style paths
                ref = "Reference: {p} (line {l})".format(p=path, l=line)
                yield ref

            # Links
            if item.links:
                yield ""  # break before links
                links = '*' + "Links: " + ', '.join(item.links) + '*'
                yield links

        yield ""  # break between items


def iter_lines_html(document, ignored=None):
    """Yield lines for an HTML report.

    @param document: Document to publish
    @param ignored: function to determine if a path should be skipped

    @return: iterator of lines of text
    """
    yield '<p><link href="doorstop.css" rel="stylesheet"></link></p>'
    lines = iter_lines_markdown(document, ignored=ignored)
    text = '\n'.join(lines)
    html = markdown.markdown(text)
    yield from html.splitlines()


def copy_css(directory):
    """Copy the style sheet for generated HTML to the specified directory."""
    shutil.copy(CSS, directory)


# Mapping from file extension to lines generator
FORMAT = {'.txt': iter_lines_text,
          '.md': iter_lines_markdown,
          '.html': iter_lines_html}
