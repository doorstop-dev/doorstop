# SPDX-License-Identifier: LGPL-3.0-only

"""Functions to publish documents and items in AsciiDoc."""

import os
import shutil
from pathlib import Path

from doorstop import common, settings
from doorstop.core.publishers.base import BasePublisher, format_level
from doorstop.core.publishers.markdown import clean_link
from doorstop.core.types import is_item, iter_items

log = common.logger(__name__)


class AsciiDocPublisher(BasePublisher):
    """AsciiDoc publisher."""

    def __init__(self, obj, ext):
        super().__init__(obj, ext)

        # Per-document overrides
        # These are off by default, but can be enabled by including the indicated
        # reference in a document's attributes: publish section

        self.levels = False  # document.publish["asciidoc_levels"]
        self.toc = False  # document.publish["asciidoc_toc"]
        self.references = False  # document.publish["asciidoc_references"]

        # Output directory for the publish action
        self.directory = None

    def publishAction(self, document, path):
        """Publish action."""
        super().publishAction(document, path)

        # Store output directory for the publish action
        self.directory = Path(path).parent

        # This function is called per document, so we need to set these
        # back to the default (False) before checking the config for
        # the current document
        self.levels = False
        self.toc = False
        self.references = False

        if document.publish:
            for attr in document.publish:
                if attr == "asciidoc_levels":
                    self.levels = True
                elif attr == "asciidoc_toc":
                    self.toc = True
                if attr == "asciidoc_references":
                    self.references = True

    def create_index(self, directory, index=None, extensions=(".adoc",), tree=None):
        """No index for AsciiDoc."""

    def create_matrix(self, directory):
        """No traceability matrix for AsciiDoc."""

    def format_attr_list(self, item, linkify):
        """Create a AsciiDoc attribute list for a heading."""
        link = clean_link("{u}".format(u=item.uid))
        return "[[{l}]]\n".format(l=link) if linkify else ""

    def format_ref(self, item):
        """Format an external reference in AsciiDoc."""
        if settings.CHECK_REF:
            path, line = item.find_ref()
            path = Path(path)
            if line:
                return "> `{p}` (line {line})".format(p=path, line=line)
            else:
                return "> `{p}`".format(p=path)
        else:
            return "> '{r}'".format(r=item.ref)

    def format_references(self, item):
        """Format an external reference in AsciiDoc."""
        if settings.CHECK_REF:
            references = item.find_references()
            text_refs = []
            for ref_item in references:
                path, line = ref_item
                path = Path(path)

                # If 'asciidoc_references' option is enabled for document and referenced file
                # is an AsciiDoc source file, then include the content in the output
                if self.references and path.suffix == ".adoc":
                    self.copy_reference(path)
                    text_refs.append("")
                    text_refs.append("---")
                    text_refs.append("include::{p}[]".format(p=path))
                    text_refs.append("")
                    text_refs.append("---")
                elif line:
                    text_refs.append("> `{p}` (line {line})".format(p=path, line=line))
                else:
                    text_refs.append("> `{p}`".format(p=path))

            return "\n".join(ref for ref in text_refs)
        else:
            references = item.references
            text_refs = []
            for ref_item in references:
                path = ref_item["path"]
                path = Path(path)

                # If 'asciidoc_references' option is enabled for document and referenced file
                # is an AsciiDoc source file, then include the content in the output
                if self.references and path.suffix == ".adoc":
                    self.copy_reference(path)
                    text_refs.append("include::{p}[]".format(p=path))
                else:
                    text_refs.append("> '{r}'".format(r=path))
            return "\n".join(ref for ref in text_refs)

    def format_links(self, items, linkify):
        """Format a list of linked items in AsciiDoc."""
        links = []
        for item in items:
            link = self.format_item_link(item, linkify=linkify)
            links.append(link)
        return ", ".join(links)

    def format_item_link(self, item, linkify=True):
        """Format an item link in AsciiDoc."""
        if linkify and is_item(item):
            link = clean_link("{u}".format(u=item.uid))
            if item.header:
                return "xref:{p}.adoc#{l}[{u} {h}]".format(
                    u=item.uid, l=link, h=item.header, p=item.document.prefix
                )
            return "xref:{p}.adoc#{l}[{u}]".format(
                u=item.uid, l=link, p=item.document.prefix
            )
        else:
            return str(item.uid)  # if not `Item`, assume this is an `UnknownItem`

    def format_label_links(self, label, links, linkify):
        """Join a string of label and links with formatting."""
        if linkify:
            return "_{lb}_ {ls}".format(lb=label, ls=links)
        else:
            return "_{lb}_ {ls}".format(lb=label, ls=links)

    def table_of_contents(self, linkify=None, obj=None):
        """Generate a table of contents for an AsciiDoc document."""
        toc = ":toc:\n"
        return toc

    def lines(self, obj, **kwargs):
        """Yield lines for a AsciiDoc report.

        :param obj: Item, list of Items, or Document to publish
        :param linkify: turn links into hyperlinks

        :return: iterator of lines of text

        """
        linkify = kwargs.get("linkify", False)
        toc = kwargs.get("toc", False)
        if self.toc and toc:
            yield self.table_of_contents(linkify=linkify, obj=obj)

        yield from self._lines_asciidoc(obj, **kwargs)

    def _generate_heading_from_item(self, item):
        """Generate a heading from an item in a consistent way for AsciiDoc.

        This ensures that references between documents are consistent.
        """
        result = ""

        # Start at level 2 (==), because level 1 (=) is the document title
        heading = "=" * (item.depth + 1)
        level = format_level(item.level)
        if item.heading:
            text_lines = item.text.splitlines()
            if item.header:
                text_lines.insert(0, item.header)
            # Level and Text
            if self.levels and settings.PUBLISH_HEADING_LEVELS:
                standard = "{h} {lev} {t}".format(
                    h=heading, lev=level, t=text_lines[0] if text_lines else ""
                )
            else:
                standard = "{h} {t}".format(
                    h=heading, t=text_lines[0] if text_lines else ""
                )
            attr_list = self.format_attr_list(item, True)
            result = attr_list + standard
        else:
            uid = item.uid
            if settings.ENABLE_HEADERS:
                if item.header:
                    uid = "{h} _{u}_".format(h=item.header, u=item.uid)
                else:
                    uid = "{u}".format(u=item.uid)

            # Level and UID
            if self.levels and settings.PUBLISH_BODY_LEVELS:
                standard = "{h} {lev} {u}".format(h=heading, lev=level, u=uid)
            else:
                standard = "{h} {u}".format(h=heading, u=uid)

            attr_list = self.format_attr_list(item, True)
            result = attr_list + standard
        return result

    def _lines_asciidoc(self, obj, **kwargs):
        """Yield lines for a AsciiDoc report.

        :param obj: Item, list of Items, or Document to publish
        :param linkify: turn links into hyperlinks

        :return: iterator of lines of text

        """
        linkify = kwargs.get("linkify", False)
        for item in iter_items(obj):
            # Create item heading.
            complete_heading = self._generate_heading_from_item(item)
            yield complete_heading

            # Text
            if item.text:
                yield ""  # break before text
                yield from item.text.splitlines()

            # Reference
            if item.ref:
                yield ""  # break before reference
                yield self.format_ref(item)

            # Reference
            if item.references:
                yield ""  # break before references
                yield self.format_references(item)

            # Parent links
            if item.links:
                yield ""  # break before links
                items2 = item.parent_items
                if settings.PUBLISH_CHILD_LINKS:
                    label = "Parent links:"
                else:
                    label = "Links:"
                links = self.format_links(items2, linkify)
                label_links = self.format_label_links(label, links, linkify)
                yield label_links

            # Child links
            if settings.PUBLISH_CHILD_LINKS:
                items2 = item.find_child_items()
                if items2:
                    yield ""  # break before links
                    label = "Child links:"
                    links = self.format_links(items2, linkify)
                    label_links = self.format_label_links(label, links, linkify)
                    yield label_links

            # Add custom publish attributes
            if item.document and item.document.publish:
                for attr in item.document.publish:
                    if not item.attribute(attr):
                        continue
                    yield ""  # break before attribute name
                    yield "*{}*".format(attr)
                    yield ""  # break before attribute content
                    yield "{}".format(item.attribute(attr))
                yield ""

            yield ""  # break between items

    def copy_reference(self, path):
        """Copy a referenced AsciiDoc file to the output, including directory structure."""
        src = Path.cwd().joinpath(path)
        newpath = self.directory / path
        os.makedirs(os.path.dirname(newpath), exist_ok=True)
        shutil.copy(src, newpath)
