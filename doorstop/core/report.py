#!/usr/bin/env python

"""
Doorstop reporting functionality.
"""

import os
import textwrap


def get_text(document, indent=8, width=79):
    """Yield text for a standard output report.

    @param document: Document to publish
    @param indent: number of spaces to indent text

    @return: iterator of text
    """
    for item in document.items:

        level = '.'.join(str(l) for l in item.level)
        identifier = item.id

        # Level and ID
        yield "{lvl:<{sp}}{id}".format(lvl=level, id=identifier, sp=indent)

        # Text
        if item.text:
            yield ""  # break before text
            for line in item.text.splitlines():
                for chunk in _chunks(line, width, indent):
                    yield chunk

                if not line:  # pragma: no cover - integration test
                    yield ""  # break between paragraphs

        # Reference
        if item.ref:
            yield ""  # break before reference
            path, line = item.find_ref()
            relpath = os.path.relpath(path, item.root)
            ref = "Reference: {p} @ {l}".format(p=relpath, l=line)
            for chunk in _chunks(ref, width, indent):
                yield chunk

        # Links
        if item.links:
            yield ""  # break before links
            links = "Links: " + ', '.join(item.links)
            for chunk in _chunks(links, width, indent):
                yield chunk

        yield ""  # break between items


def _chunks(text, width, indent):
    """Yield wrapped lines of text."""
    for chunk in textwrap.wrap(text, width,
                               initial_indent=' ' * indent,
                               subsequent_indent=' ' * indent):
        yield chunk
