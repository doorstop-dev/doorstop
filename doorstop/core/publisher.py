"""Functions to publish documents and items."""

import os
import textwrap
import logging

import markdown

from doorstop.common import DoorstopError, create_dirname
from doorstop.core.types import iter_documents, iter_items, is_tree
from doorstop import settings

CSS = os.path.join(os.path.dirname(__file__), 'files', 'doorstop.css')
INDEX = 'index.html'


def publish(obj, path, ext=None, create_index=None, **kwargs):
    """Publish a document to a given format.

    @param obj: Item, list of Items, Document, or Tree to publish
    @param path: output file location with desired extension
    @param ext: file extension to override output path's extension
    @param create_index: indicates an HTML index should be created

    @raise DoorstopError: for unknown file formats

    """
    # Determine the output format
    ext = ext or os.path.splitext(path)[-1] or '.html'
    check(ext)

    # Publish documents
    for obj2, path2 in iter_documents(obj, path, ext):

        # Publish content to the specified path
        create_dirname(path2)
        logging.info("creating file {}...".format(path2))
        with open(path2, 'w') as outfile:  # pragma: no cover (integration test)
            for line in lines(obj2, ext, **kwargs):
                outfile.write(line + '\n')

    # Create index
    if create_index or (create_index is None and is_tree(obj)):
        index(path)


def index(directory, extensions=('.html',)):
    """Create an HTML index of all files in a directory.

    @param directory: directory for index
    @param extensions: file extensions to include

    """
    # Get paths for the index index
    filenames = []
    for filename in os.listdir(directory):
        if filename.endswith(extensions) and filename != INDEX:
            filenames.append(os.path.join(filename))

    # Create the index
    if filenames:
        path = os.path.join(directory, INDEX)
        logging.info("publishing {}...".format(path))
        with open(path, 'w') as outfile:
            for line in _lines_index(filenames):
                outfile.write(line + '\n')
    else:
        logging.warning("no files for {}".format(INDEX))


def _lines_index(filenames):
    """Yield lines of HTML for index.html."""
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
    for filename in filenames:
        name = os.path.splitext(filename)[0]
        yield '<li> <a href="{f}">{n}</a> </li>'.format(f=filename, n=name)
    yield '</body>'
    yield '</html>'


def lines(obj, ext='.txt', **kwargs):
    """Yield lines for a report in the specified format.

    @param obj: Item, list of Items, or Document to publish
    @param ext: file extension to specify the output format

    @raise DoorstopError: for unknown file formats

    """
    gen = check(ext)
    logging.debug("yielding {} as lines of {}...".format(obj, ext))
    yield from gen(obj, **kwargs)


def lines_text(obj, indent=8, width=79):
    """Yield lines for a text report.

    @param obj: Item, list of Items, or Document to publish
    @param indent: number of spaces to indent text
    @param width: maximum line length

    @return: iterator of lines of text

    """
    for item in iter_items(obj):

        level = _format_level(item.level)

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

                    if not line:  # pragma: no cover (integration test)
                        yield ""  # break between paragraphs

            # Reference
            if item.ref:
                yield ""  # break before reference
                ref = _ref(item)
                yield from _chunks(ref, width, indent)

            # Links
            if item.links:
                yield ""  # break before links
                if settings.PUBLISH_CHILD_LINKS:
                    label = "Parent links: "
                else:
                    label = "Links: "
                slinks = label + ', '.join(str(l) for l in item.links)
                yield from _chunks(slinks, width, indent)
            if settings.PUBLISH_CHILD_LINKS:
                links = item.find_child_links()
                if links:
                    yield ""  # break before links
                    slinks = "Child links: " + ', '.join(str(l) for l in links)
                    yield from _chunks(slinks, width, indent)

        yield ""  # break between items


def _chunks(text, width, indent):
    """Yield wrapped lines of text."""
    yield from textwrap.wrap(text, width,
                             initial_indent=' ' * indent,
                             subsequent_indent=' ' * indent)


def lines_markdown(obj, linkify=False):
    """Yield lines for a Markdown report.

    @param obj: Item, list of Items, or Document to publish

    @return: iterator of lines of text

    """
    for item in iter_items(obj):

        heading = '#' * item.depth
        level = _format_level(item.level)

        if item.heading:

            # Level and Text
            standard = "{h} {l} {t}".format(h=heading, l=level, t=item.text)
            attr_list = " {{: #{i} }}".format(i=item.id) if linkify else ''
            yield standard + attr_list

        else:

            # Level and ID
            standard = "{h} {l} {i}".format(h=heading, l=level, i=item.id)
            attr_list = " {{: #{i} }}".format(i=item.id) if linkify else ''
            yield standard + attr_list

            # Text
            if item.text:
                yield ""  # break before text
                yield from item.text.splitlines()

            # Reference
            if item.ref:
                yield ""  # break before reference
                yield _ref(item)

            # Links
            if item.links:
                yield ""  # break before links
                if settings.PUBLISH_CHILD_LINKS:
                    label = "Parent links:"
                else:
                    label = "Links:"
                if linkify:
                    links = []
                    for item2 in item.parent_items:
                        links.append("[{i}]({p}.html#{i})".format(i=item2.id, p=item2.document.prefix))
                    yield '*' + label + '*' + ' ' + ', '.join(links)
                else:
                    slinks = label + ' ' + ', '.join(str(l) for l in item.links)
                    yield '*' + slinks + '*'
            if settings.PUBLISH_CHILD_LINKS:
                items2 = item.find_child_items()
                if items2:
                    yield ""  # break before links
                    if linkify:
                        links = []
                        for item2 in items2:
                            links.append("[{i}]({p}.html#{i})".format(i=item2.id, p=item2.document.prefix))
                        yield'*' + "Child links:" + '*' + ' ' + ', '.join(links)
                    else:
                        slinks = "Child links: " + ', '.join(str(i.id) for i in items2)
                        yield '*' + slinks + '*'

        yield ""  # break between items


def _format_level(level):
    """Convert a level to a string and keep zeros if not a top level."""
    text = str(level)
    if text.endswith('.0') and len(text) > 3:
        text = text[:-2]
    return text


def _ref(item):
    """Format an external reference for publishing."""
    if settings.CHECK_REF:
        path, line = item.find_ref()
        path = path.replace('\\', '/')  # always use unix-style paths
        return "Reference: {p} (line {l})".format(p=path, l=line)
    else:
        return "Reference: '{r}'".format(r=item.ref)


def lines_html(obj):
    """Yield lines for an HTML report.

    @param obj: Item, list of Items, or Document to publish

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
            for line in infile:  # pragma: no cover (integration test)
                yield line
        yield '</style>'
        yield '</head>'
        yield '<body>'
    text = '\n'.join(lines_markdown(obj, linkify=True))
    html = markdown.markdown(text, extensions=['extra', 'nl2br', 'sane_lists'])
    yield from html.splitlines()
    if document:
        yield '</body>'
        yield '</html>'


# Mapping from file extension to lines generator
FORMAT_LINES = {'.txt': lines_text,
                '.md': lines_markdown,
                '.html': lines_html}


def check(ext):
    """Confirm an extension is supported for publish.

    @raise DoorstopError: for unknown formats

    @return: lines generator if available

    """
    try:
        gen = FORMAT_LINES[ext]
    except KeyError:
        exts = ', '.join(ext for ext in FORMAT_LINES)
        msg = "unknown publish format: {} (options: {})".format(ext, exts)
        exc = DoorstopError(msg)
        raise exc from None
    else:
        logging.debug("found lines generator for: {}".format(ext))
        return gen
