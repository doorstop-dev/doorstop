# SPDX-License-Identifier: LGPL-3.0-only

"""Functions to publish documents and items."""

import os
import textwrap

from doorstop import common, settings
from doorstop.core.publishers.base import (
    BasePublisher,
    format_level,
    normalize_link_list,    # ← NEU
    is_link_attribute,      # ← NEU
)
from doorstop.core.types import iter_items

log = common.logger(__name__)


class TextPublisher(BasePublisher):
    """Text publisher."""

    def __init__(self, obj, ext):
        super().__init__(obj, ext)
        self.indent = 8
        self.width = 79

    def create_matrix(self, directory):
        """No traceability matrix for text."""

    def create_index(self, directory, index=None, extensions=(".html",), tree=None):
        """No index for text."""

    def format_attr_list(self, item, linkify):
        """No attribute lists for text."""

    def format_item_link(self, item, linkify=True):
        """No links for text."""

    def format_label_links(self, label, links, linkify):
        """No links for text."""

    def format_links(self, items, linkify, to_html=False):
        """No links for text."""

    def table_of_contents(self, linkify=None, obj=None):
        """No table of contents text."""

    def lines(self, obj, **_):
        """Yield lines for a text report.

        :param obj: Item, list of Items, or Document to publish
        :param indent: number of spaces to indent text
        :param width: maximum line length

        :return: iterator of lines of text

        """
        for item in iter_items(obj):
            level = format_level(item.level)

            if item.heading:
                text_lines = item.text.splitlines()
                if item.header:
                    text_lines.insert(0, item.header)
                text = os.linesep.join(text_lines)
                # Level and Text
                if settings.PUBLISH_HEADING_LEVELS:
                    yield "{lev:<{s}}{t}".format(lev=level, s=self.indent, t=text)
                else:
                    yield "{t}".format(t=text)

            else:
                # Level and UID
                if item.header:
                    yield "{lev:<{s}}{u} {header}".format(
                        lev=level, s=self.indent, u=item.uid, header=item.header
                    )
                else:
                    yield "{lev:<{s}}{u}".format(lev=level, s=self.indent, u=item.uid)

                # Text
                if item.text:
                    yield ""  # break before text
                    for line in item.text.splitlines():
                        yield from self._chunks(line)

                        if not line:
                            yield ""  # break between paragraphs

                # Reference
                if item.ref:
                    yield ""  # break before reference
                    ref = self.format_ref(item)
                    yield from self._chunks(ref)

                # References
                if item.references:
                    yield ""  # break before references
                    ref = self.format_references(item)
                    yield from self._chunks(ref)

                # Links
                if item.links:
                    yield ""  # break before links
                    if settings.PUBLISH_CHILD_LINKS:
                        label = "Parent links: "
                    else:
                        label = "Links: "
                    slinks = label + ", ".join(str(l) for l in item.links)
                    yield from self._chunks(slinks)
                if settings.PUBLISH_CHILD_LINKS:
                    links = item.find_child_links()
                    if links:
                        yield ""  # break before links
                        slinks = "Child links: " + ", ".join(str(l) for l in links)
                        yield from self._chunks(slinks)

                # Attributes
                if item.document and item.document.publish:
                    yield ""
                    for attr in item.document.publish:
                        value = item.attribute(attr)
                        if not value:
                            continue
                        
                        # ========== Handle link attributes specially ==========
                        if is_link_attribute(attr):
                            link_list = normalize_link_list(value)
                            if link_list:
                                # Format each link on a separate line for readability
                                for i, link_text in enumerate(link_list, 1):
                                    if len(link_list) > 1:
                                        attr_line = "{} [{}]: {}".format(attr, i, link_text)
                                    else:
                                        attr_line = "{}: {}".format(attr, link_text)
                                    yield from self._chunks(attr_line)
                        
                        # ========== Handle regular lists ==========
                        elif isinstance(value, list):
                            if len(value) > 0:
                                items = [str(v).strip() for v in value if str(v).strip()]
                                if items:
                                    # Format as comma-separated or numbered list
                                    if len(items) == 1:
                                        attr_line = "{}: {}".format(attr, items[0])
                                        yield from self._chunks(attr_line)
                                    else:
                                        for i, item_text in enumerate(items, 1):
                                            attr_line = "{} [{}]: {}".format(attr, i, item_text)
                                            yield from self._chunks(attr_line)
                        
                        # ========== Handle dictionaries ==========
                        elif isinstance(value, dict):
                            # Format each key-value pair
                            for k, v in value.items():
                                attr_line = "{} [{}]: {}".format(attr, k, str(v).strip())
                                yield from self._chunks(attr_line)
                        
                        # ========== Handle simple values ==========
                        else:
                            attr_line = "{}: {}".format(attr, str(value))
                            yield from self._chunks(attr_line)

            yield ""  # break between items

    def format_ref(self, item):
        """Format an external reference in text."""
        if settings.CHECK_REF:
            path, line = item.find_ref()
            path = path.replace("\\", "/")  # always use unix-style paths
            if line:
                return "Reference: {p} (line {line})".format(p=path, line=line)
            else:
                return "Reference: {p}".format(p=path)
        else:
            return "Reference: '{r}'".format(r=item.ref)

    def format_references(self, item):
        """Format an external reference in text."""
        if settings.CHECK_REF:
            ref = item.find_references()
            text_refs = []
            for ref_item in ref:
                path, line = ref_item
                path = path.replace("\\", "/")  # always use unix-style paths
                if line:
                    text_refs.append("{p} (line {line})".format(p=path, line=line))
                else:
                    text_refs.append("{p}".format(p=path))
            return "Reference: {}".format(", ".join(ref for ref in text_refs))
        else:
            references = item.references
            text_refs = []
            for ref_item in references:
                path = ref_item["path"]
                path = path.replace("\\", "/")  # always use unix-style paths
                text_refs.append("'{p}'".format(p=path))
            return "Reference: {}".format(", ".join(text_ref for text_ref in text_refs))

    def _chunks(self, text):
        """Yield wrapped lines of text."""
        yield from textwrap.wrap(
            text,
            self.width,
            initial_indent=" " * self.indent,
            subsequent_indent=" " * self.indent,
        )
