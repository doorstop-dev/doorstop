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

    @param document: Document to publish
    @param path: output file location with desired extension
    @param ext: file extension to override output path's extension
    @param ignored: function to determine if a path should be skipped

    @raise DoorstopError: for unknown file formats
    """
    ext = ext or os.path.splitext(path)[-1]
    if ext in FORMAT:
        logging.info("creating {}...".format(path))
        with open(path, 'wb') as outfile:  # pragma: no cover, integration test
            for line in lines(document, ext, ignored=ignored, **kwargs):
                outfile.write(bytes(line + '\n', 'utf-8'))
    else:
        raise DoorstopError("unknown format: {}".format(ext))


def lines(obj, ext='.txt', ignored=None, **kwargs):
    """Yield lines for a report in the specified format.

    @param obj: Item, list of Items, or Document to publish
    @param ext: file extension to specify the output format
    @param ignored: function to determine if a path should be skipped

    @raise DoorstopError: for unknown file formats
    """
    if ext in FORMAT:
        logging.debug("yielding {} as lines of {}...".format(obj, ext))
        yield from FORMAT[ext](obj, ignored=ignored, **kwargs)
    else:
        raise DoorstopError("unknown format: {}".format(ext))


def lines_text(obj, ignored=None, indent=8, width=79):
    """Yield lines for a text report.

    @param obj: Item, list of Items, or Document to publish
    @param ignored: function to determine if a path should be skipped
    @param indent: number of spaces to indent text
    @param width: maximum line length

    @return: iterator of lines of text
    """
    for item in _items(obj):

        level = '.'.join(str(l) for l in item.level)
        if level.endswith('.0') and len(level) > 3:
            level = level[:-2]

        if item.heading:

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


def lines_markdown(obj, ignored=None):
    """Yield lines for a Markdown report.

    @param obj: Item, list of Items, or Document to publish
    @param ignored: function to determine if a path should be skipped

    @return: iterator of lines of text
    """
    for item in _items(obj):

        heading = '#' * item.depth
        level = '.'.join(str(l) for l in item.level)
        if level.endswith('.0') and len(level) > 3:
            level = level[:-2]

        if item.heading:

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


def _items(obj):
    """Get an iterator of items from from an item, list, or document."""

    if hasattr(obj, 'items'):
        # a document
        return (i for i in obj.items if i.active)
    try:
        # an iterable
        return iter(obj)
    except TypeError:
        # an item
        return [obj]  # an item


def lines_html(obj, ignored=None):
    """Yield lines for an HTML report.

    @param obj: Item, list of Items, or Document to publish
    @param ignored: function to determine if a path should be skipped

    @return: iterator of lines of text
    """
    # Determine if a full HTML document should be generated
    try:
        iter(obj)
    except TypeError:
        document = False
    else:
        document = True
    # Generate HTML
    if document:
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
    html = markdown.markdown('\n'.join(lines_markdown(obj, ignored=ignored)))
    yield from html.splitlines()
    if document:
        yield '</body>'
        yield '</html>'


# Mapping from file extension to lines generator
FORMAT = {'.txt': lines_text,
          '.md': lines_markdown,
          '.html': lines_html}
