"""Functions to publish documents and items."""

import os
import textwrap

import markdown

from doorstop import common
from doorstop.common import DoorstopError
from doorstop.core.types import iter_documents, iter_items, is_tree, is_item
from doorstop import settings

EXTENSIONS = [
    'markdown.extensions.extra',
    'markdown.extensions.sane_lists',
]
CSS = os.path.join(os.path.dirname(__file__), 'files', 'doorstop.css')
INDEX = 'index.html'

log = common.logger(__name__)


def publish(obj, path, ext=None, linkify=None, index=None, **kwargs):
    """Publish an object to a given format.

    The function can be called in two ways:

    1. document or item-like object + output file path
    2. tree-like object + output directory path

    :param obj: (1) Item, list of Items, Document or (2) Tree
    :param path: (1) output file path or (2) output directory path
    :param ext: file extension to override output extension
    :param linkify: turn links into hyperlinks (for Markdown or HTML)
    :param index: create an index.html (for HTML)

    :raises: :class:`doorstop.common.DoorstopError` for unknown file formats

    :return: output location if files created, else None

    """
    # Determine the output format
    ext = ext or os.path.splitext(path)[-1] or '.html'
    check(ext)
    if linkify is None:
        linkify = is_tree(obj) and ext in ['.html', '.md']
    if index is None:
        index = is_tree(obj) and ext == '.html'

    # Publish documents
    count = 0
    for obj2, path2 in iter_documents(obj, path, ext):
        count += 1

        # Publish content to the specified path
        common.create_dirname(path2)
        log.info("publishing to {}...".format(path2))
        lines = publish_lines(obj2, ext, linkify=linkify, **kwargs)
        common.write_lines(lines, path2)
        if obj2.assets:
            src = obj2.assets
            dst = os.path.join(os.path.dirname(path2), obj2.ASSETS)
            common.copy(src, dst)

    # Create index
    if index and count:
        _index(path, tree=obj if is_tree(obj) else None)

    # Return the published path
    if count:
        msg = "published to {} file{}".format(count, 's' if count > 1 else '')
        log.info(msg)
        return path
    else:
        log.warning("nothing to publish")
        return None


def _index(directory, index=INDEX, extensions=('.html',), tree=None):
    """Create an HTML index of all files in a directory.

    :param directory: directory for index
    :param index: filename for index
    :param extensions: file extensions to include
    :param tree: optional tree to determine index structure

    """
    # Get paths for the index index
    filenames = []
    for filename in os.listdir(directory):
        if filename.endswith(extensions) and filename != INDEX:
            filenames.append(os.path.join(filename))

    # Create the index
    if filenames:
        path = os.path.join(directory, index)
        log.info("creating an {}...".format(index))
        lines = _lines_index(sorted(filenames), tree=tree)
        common.write_lines(lines, path)
    else:
        log.warning("no files for {}".format(index))


def _lines_index(filenames, charset='UTF-8', tree=None):
    """Yield lines of HTML for index.html.

    :param filesnames: list of filenames to add to the index
    :param charset: character encoding for output
    :param tree: optional tree to determine index structure

    """
    yield '<!DOCTYPE html>'
    yield '<head>'
    yield ('<meta http-equiv="content-type" content="text/html; '
           'charset={charset}">'.format(charset=charset))
    yield '<style type="text/css">'
    yield from _lines_css()
    yield '</style>'
    yield '</head>'
    yield '<body>'
    # Tree structure
    text = tree.draw() if tree else None
    if text:
        yield ''
        yield '<h3>Tree Structure:</h3>'
        yield '<pre><code>' + text + '</pre></code>'
    # Additional files
    if filenames:
        if text:
            yield ''
            yield '<hr>'
        yield ''
        yield '<h3>Published Documents:</h3>'
        yield '<p>'
        yield '<ul>'
        for filename in filenames:
            name = os.path.splitext(filename)[0]
            yield '<li> <a href="{f}">{n}</a> </li>'.format(f=filename, n=name)
        yield '</ul>'
        yield '</p>'
    # Traceability table
    documents = tree.documents if tree else None
    if documents:
        if text or filenames:
            yield ''
            yield '<hr>'
        yield ''
        # table
        yield '<h3>Item Traceability:</h3>'
        yield '<p>'
        yield '<table>'
        # header
        for document in documents:
            yield '<col width="100">'
        yield '<tr>'
        for document in documents:
            link = '<a href="{p}.html">{p}</a>'.format(p=document.prefix)
            yield '  <th height="25" align="center"> {l} </th>'.format(l=link)
        yield '</tr>'
        # data
        for index, row in enumerate(tree.get_traceability()):
            if index % 2:
                yield '<tr class="alt">'
            else:
                yield '<tr>'
            for item in row:
                if item is None:
                    link = ''
                else:
                    link = _format_html_item_link(item)
                yield '  <td height="25" align="center"> {} </td>'.format(link)
            yield '</tr>'
        yield '</table>'
        yield '</p>'
    yield ''
    yield '</body>'
    yield '</html>'


def _lines_css():
    """Yield lines of CSS to embedded in HTML."""
    yield ''
    for line in common.read_lines(CSS):
        yield line.rstrip()
    yield ''


def publish_lines(obj, ext='.txt', **kwargs):
    """Yield lines for a report in the specified format.

    :param obj: Item, list of Items, or Document to publish
    :param ext: file extension to specify the output format

    :raises: :class:`doorstop.common.DoorstopError` for unknown file formats

    """
    gen = check(ext)
    log.debug("yielding {} as lines of {}...".format(obj, ext))
    yield from gen(obj, **kwargs)


def _lines_text(obj, indent=8, width=79, **_):
    """Yield lines for a text report.

    :param obj: Item, list of Items, or Document to publish
    :param indent: number of spaces to indent text
    :param width: maximum line length

    :return: iterator of lines of text

    """
    for item in iter_items(obj):

        level = _format_level(item.level)

        if item.heading:

            # Level and Text
            if settings.PUBLISH_HEADING_LEVELS:
                yield "{l:<{s}}{t}".format(l=level, s=indent, t=item.text)
            else:
                yield "{t}".format(t=item.text)

        else:

            # Level and UID
            yield "{l:<{s}}{u}".format(l=level, s=indent, u=item.uid)

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
                ref = _format_text_ref(item)
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

    :param obj: Item, list of Items, or Document to publish
    :param linkify: turn links into hyperlinks (for conversion to HTML)

    :return: iterator of lines of text

    """
    for item in iter_items(obj):

        heading = '#' * item.depth
        level = _format_level(item.level)

        if item.heading:
            text_lines = item.text.splitlines()
            # Level and Text
            if settings.PUBLISH_HEADING_LEVELS:
                standard = "{h} {l} {t}".format(h=heading, l=level, t=text_lines[0])
            else:
                standard = "{h} {t}".format(h=heading, t=item.text)
            attr_list = _format_md_attr_list(item, linkify)
            yield standard + attr_list
            yield from text_lines[1:]
        else:

            # Level and UID
            if settings.PUBLISH_BODY_LEVELS:
                standard = "{h} {l} {u}".format(h=heading, l=level, u=item.uid)
            else:
                standard = "{h} {u}".format(h=heading, u=item.uid)
            attr_list = _format_md_attr_list(item, linkify)
            yield standard + attr_list

            # Text
            if item.text:
                yield ""  # break before text
                yield from item.text.splitlines()

            # Reference
            if item.ref:
                yield ""  # break before reference
                yield _format_md_ref(item)

            # Parent links
            if item.links:
                yield ""  # break before links
                items2 = item.parent_items
                if settings.PUBLISH_CHILD_LINKS:
                    label = "Parent links:"
                else:
                    label = "Links:"
                links = _format_md_links(items2, linkify)
                label_links = _format_md_label_links(label, links, linkify)
                yield label_links

            # Child links
            if settings.PUBLISH_CHILD_LINKS:
                items2 = item.find_child_items()
                if items2:
                    yield ""  # break before links
                    label = "Child links:"
                    links = _format_md_links(items2, linkify)
                    label_links = _format_md_label_links(label, links, linkify)
                    yield label_links

        yield ""  # break between items


def _format_level(level):
    """Convert a level to a string and keep zeros if not a top level."""
    text = str(level)
    if text.endswith('.0') and len(text) > 3:
        text = text[:-2]
    return text


def _format_md_attr_list(item, linkify):
    """Create a Markdown attribute list for a heading."""
    return " {{#{u} }}".format(u=item.uid) if linkify else ''


def _format_text_ref(item):
    """Format an external reference in text."""
    if settings.CHECK_REF:
        path, line = item.find_ref()
        path = path.replace('\\', '/')  # always use unix-style paths
        if line:
            return "Reference: {p} (line {l})".format(p=path, l=line)
        else:
            return "Reference: {p}".format(p=path)
    else:
        return "Reference: '{r}'".format(r=item.ref)


def _format_md_ref(item):
    """Format an external reference in Markdown."""
    if settings.CHECK_REF:
        path, line = item.find_ref()
        path = path.replace('\\', '/')  # always use unix-style paths
        if line:
            return "> `{p}` (line {l})".format(p=path, l=line)
        else:
            return "> `{p}`".format(p=path)
    else:
        return "> '{r}'".format(r=item.ref)


def _format_md_links(items, linkify):
    """Format a list of linked items in Markdown."""
    links = []
    for item in items:
        link = _format_md_item_link(item, linkify=linkify)
        links.append(link)
    return ', '.join(links)


def _format_md_item_link(item, linkify=True):
    """Format an item link in Markdown."""
    if linkify and is_item(item):
        return "[{u}]({p}.html#{u})".format(u=item.uid, p=item.document.prefix)
    else:
        return str(item.uid)  # if not `Item`, assume this is an `UnknownItem`


def _format_html_item_link(item, linkify=True):
    """Format an item link in HTML."""
    if linkify and is_item(item):
        link = '<a href="{p}.html#{u}">{u}</a>'.format(u=item.uid,
                                                       p=item.document.prefix)
        return link
    else:
        return str(item.uid)  # if not `Item`, assume this is an `UnknownItem`


def _format_md_label_links(label, links, linkify):
    """Join a string of label and links with formatting."""
    if linkify:
        return "*{lb}* {ls}".format(lb=label, ls=links)
    else:
        return "*{lb} {ls}*".format(lb=label, ls=links)


def _lines_html(obj, linkify=False, extensions=EXTENSIONS, charset='UTF-8'):
    """Yield lines for an HTML report.

    :param obj: Item, list of Items, or Document to publish
    :param linkify: turn links into hyperlinks

    :return: iterator of lines of text

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
        yield ('<meta http-equiv="content-type" content="text/html; '
               'charset={charset}">'.format(charset=charset))
        yield '<style type="text/css">'
        yield from _lines_css()
        yield '</style>'
        yield '</head>'
        yield '<body>'
    text = '\n'.join(_lines_markdown(obj, linkify=linkify))
    html = markdown.markdown(text, extensions=extensions)
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

    :raises: :class:`doorstop.common.DoorstopError` for unknown formats

    :return: lines generator if available

    """
    exts = ', '.join(ext for ext in FORMAT_LINES)
    msg = "unknown publish format: {} (options: {})".format(ext or None, exts)
    exc = DoorstopError(msg)

    try:
        gen = FORMAT_LINES[ext]
    except KeyError:
        raise exc from None
    else:
        log.debug("found lines generator for: {}".format(ext))
        return gen
