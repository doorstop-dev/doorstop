"""
Doorstop reporting functionality.
"""

import textwrap
import markdown


def get_text(document, indent=8, width=79, ignored=None):
    """Yield lines for a text report.

    @param document: Document to publish
    @param indent: number of spaces to indent text
    @param width: maximum line length
    @param ignored: function to determine if a path should be skipped

    @return: iterator of lines of text
    """
    for item in document.items:

        level = '.'.join(str(l) for l in item.level)
        identifier = item.id

        # Level and ID
        yield "{l:<{s}}{i}".format(l=level, i=identifier, s=indent)

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


def get_markdown(document, ignored=None):
    """Yield lines for a Markdown report.

    @param document: Document to publish
    @param ignored: function to determine if a path should be skipped

    @return: iterator of lines of text
    """
    for item in document.items:

        heading = '#' * item.heading
        level = '.'.join(str(l) for l in item.level)
        identifier = item.id

        # Level and ID
        yield "{h} {l} ({i})".format(h=heading, l=level, i=identifier)

        # Text
        if item.text:
            yield ""  # break before text
            yield from item.text.splitlines()

        # Reference
        if item.ref:
            yield ""  # break before reference
            path, line = item.find_ref(ignored=ignored)
            path = path.replace('\\', '/')  # always write unix-style paths
            ref = "Reference: {p} (line {l})".format(p=path, l=line)
            yield ref

        # Links
        if item.links:
            yield ""  # break before links
            links = '*' + "Links: " + ', '.join(item.links) + '*'
            yield links

        yield ""  # break between items


def get_html(document, ignored=None):
    """Yield lines for an HTML report.

    @param document: Document to publish
    @param ignored: function to determine if a path should be skipped

    @return: iterator of lines of text
    """
    lines = get_markdown(document, ignored=ignored)
    text = '\n'.join(lines)
    html = markdown.markdown(text)
    yield from html.splitlines()
