"""Functions to publish documents and items."""

import os
import textwrap
import logging

import markdown

from doorstop.common import DoorstopError, create_dirname
from doorstop.core.types import iter_documents, iter_items, is_tree, is_item
from doorstop import settings

CSS = os.path.join(os.path.dirname(__file__), 'files', 'doorstop.css')
INDEX = 'index.html'


def publish(obj, path, ext=None, linkify=None, index=None, **kwargs):
    """Publish an object to a given format.

    The function can be called in two ways:

    1. document or item-like object + output file path
    2. tree-like object + output directory path

    @param obj: (1) Item, list of Items, Document or (2) Tree
    @param path: (1) output file path or (2) output directory path
    @param ext: file extension to override output extension
    @param linkify: turn links into hyperlinks (for Markdown or HTML)
    @param index: create an index.html (for HTML)

    @raise DoorstopError: for unknown file formats

    @return: output location if files created, else None

    """
    # Determine the output format
    ext = ext or os.path.splitext(path)[-1] or '.html'
    linkify = linkify if linkify is not None else is_tree(obj)
    index = index if index is not None else is_tree(obj)
    check(ext)

    # Publish documents
    count = 0
    for obj2, path2 in iter_documents(obj, path, ext):
        count += 1

        # Publish content to the specified path
        create_dirname(path2)
        logging.info("creating file {}...".format(path2))
        with open(path2, 'wb') as outfile:  # pragma: no cover (integration test)
            for line in publish_lines(obj2, ext, linkify=linkify, **kwargs):
                outfile.write((line + '\n').encode('utf-8'))

    # Create index
    if index and count:
        count += 1
        _index(path)

    # Return the published path
    if count:
        msg = "created {} file{}".format(count, 's' if count > 1 else '')
        logging.info(msg)
        return path
    else:
        logging.warning("nothing to publish")
        return None


def _index(directory, extensions=('.html',)):
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


def publish_lines(obj, ext='.txt', **kwargs):
    """Yield lines for a report in the specified format.

    @param obj: Item, list of Items, or Document to publish
    @param ext: file extension to specify the output format

    @raise DoorstopError: for unknown file formats

    """
    gen = check(ext)
    logging.debug("yielding {} as lines of {}...".format(obj, ext))
    yield from gen(obj, **kwargs)


def _lines_text(obj, indent=8, width=79, **_):
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
                ref = _format_ref(item)
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


def _lines_markdown(obj, linkify=False):
    """Yield lines for a Markdown report.

    @param obj: Item, list of Items, or Document to publish
    @param linkify: turn links into hyperlinks (for conversion to HTML)

    @return: iterator of lines of text

    """
    for item in iter_items(obj):

        heading = '#' * item.depth
        level = _format_level(item.level)

        if item.heading:

            # Level and Text
            standard = "{h} {l} {t}".format(h=heading, l=level, t=item.text)
            attr_list = _format_attr_list(item, linkify)
            yield standard + attr_list

        else:

            # Level and ID
            standard = "{h} {l} {i}".format(h=heading, l=level, i=item.id)
            attr_list = _format_attr_list(item, linkify)
            yield standard + attr_list

            # Text
            if item.text:
                yield ""  # break before text
                yield from item.text.splitlines()

            # Reference
            if item.ref:
                yield ""  # break before reference
                yield _format_ref(item)

            # Parent links
            if item.links:
                yield ""  # break before links
                items2 = item.parent_items
                if settings.PUBLISH_CHILD_LINKS:
                    label = "Parent links:"
                else:
                    label = "Links:"
                links = _format_links(items2, linkify)
                label_links = _format_label_links(label, links, linkify)
                yield label_links

            # Child links
            if settings.PUBLISH_CHILD_LINKS:
                items2 = item.find_child_items()
                if items2:
                    yield ""  # break before links
                    label = "Child links:"
                    links = _format_links(items2, linkify)
                    label_links = _format_label_links(label, links, linkify)
                    yield label_links

        yield ""  # break between items


def _format_level(level):
    """Convert a level to a string and keep zeros if not a top level."""
    text = str(level)
    if text.endswith('.0') and len(text) > 3:
        text = text[:-2]
    return text


def _format_attr_list(item, linkify):
    """Create a Markdown attribute list for a heading."""
    return " {{: #{i} }}".format(i=item.id) if linkify else ''


def _format_ref(item):
    """Format an external reference for publishing."""
    if settings.CHECK_REF:
        path, line = item.find_ref()
        path = path.replace('\\', '/')  # always use unix-style paths
        return "Reference: {p} (line {l})".format(p=path, l=line)
    else:
        return "Reference: '{r}'".format(r=item.ref)


def _format_links(items, linkify):
    """Format a list of linked items."""
    links = []
    for item in items:
        if is_item(item) and linkify:
            link = "[{i}]({p}.html#{i})".format(i=item.id,
                                                p=item.document.prefix)
        else:
            link = str(item.id)  # assume this is an `UnknownItem`
        links.append(link)
    return ', '.join(links)


def _format_label_links(label, links, linkify):
    """Join a string of label and links with formatting."""
    if linkify:
        return "*{lb}* {ls}".format(lb=label, ls=links)
    else:
        return "*{lb} {ls}*".format(lb=label, ls=links)


def _lines_html(obj, linkify=False):
    """Yield lines for an HTML report.

    @param obj: Item, list of Items, or Document to publish
    @param linkify: turn links into hyperlinks

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
    text = '\n'.join(_lines_markdown(obj, linkify=linkify))
    html = markdown.markdown(text, extensions=['extra', 'nl2br', 'sane_lists'])
    yield from html.splitlines()
    if document:
        yield '</body>'
        yield '</html>'


# Mapping from file extension to lines generator
FORMAT_LINES = {'.txt': _lines_text,
                '.md': _lines_markdown,
                '.html': _lines_html}


def check(ext):
    """Confirm an extension is supported for publish.

    @raise DoorstopError: for unknown formats

    @return: lines generator if available

    """
    exts = ', '.join(ext for ext in FORMAT_LINES)
    msg = "unknown publish format: {} (options: {})".format(ext or None, exts)
    exc = DoorstopError(msg)

    try:
        gen = FORMAT_LINES[ext]
    except KeyError:
        raise exc from None
    else:
        logging.debug("found lines generator for: {}".format(ext))
        return gen
