"""
Doorstop reporting functionality.
"""

import os
import textwrap
import logging

import markdown

from doorstop.common import DoorstopError

CSS = os.path.join(os.path.dirname(__file__), 'files', 'doorstop.css')


def publish(document, path, ext=None, ignored=None, **kwargs):
    """Publish a document to a given format.

    @param document: Doorstop document to publish
    @param path: output file location with desired extension
    @param ext: file extension to override output path's extension
    @param ignored: function to determine if a path should be skipped

    @raise DoorstopError: for unknown file formats
    """
    ext = ext or os.path.splitext(path)[-1]
    if ext in FORMAT:
        logging.info("writing {} as {} to {}...".format(document, ext, path))
        with open(path, 'wb') as outfile:  # pragma: no cover, integration test
            for line in iter_lines(document, ext, ignored=ignored, **kwargs):
                outfile.write(bytes(line + '\n', 'utf-8'))
    else:
        raise DoorstopError("unknown format: {}".format(ext))


def iter_lines(document, ext='.txt', ignored=None, **kwargs):
    """Yield lines for a report in the specified format.

    @param document: Doorstop document to publish
    @param ext: file extension to specify the output format
    @param ignored: function to determine if a path should be skipped

    @raise DoorstopError: for unknown file formats
    """
    if ext in FORMAT:
        logging.info("yielding {} as lines of {}...".format(document, ext))
        yield from FORMAT[ext](document, ignored=ignored, **kwargs)
    else:
        raise DoorstopError("unknown format: {}".format(ext))


def iter_lines_text(document, ignored=None, indent=8, width=79):
    """Yield lines for a text report.

    @param document: Document to publish
    @param ignored: function to determine if a path should be skipped
    @param indent: number of spaces to indent text
    @param width: maximum line length

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
    yield '<!DOCTYPE html>'
    yield '<head>'
    yield '<style type="text/css">'
    yield ''
    with open(CSS) as infile:
        for line in infile:
            yield line
    yield '</style>'
    yield '</head>'
    yield '<body>'
    lines = iter_lines_markdown(document, ignored=ignored)
    text = '\n'.join(lines)
    html = markdown.markdown(text)
    yield from html.splitlines()
    yield '</body>'
    yield '</html>'


# Mapping from file extension to lines generator
FORMAT = {'.txt': iter_lines_text,
          '.md': iter_lines_markdown,
          '.html': iter_lines_html}
