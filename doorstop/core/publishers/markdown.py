# SPDX-License-Identifier: LGPL-3.0-only

"""Functions to publish documents and items."""

import os
from re import sub

from doorstop import common, settings
from doorstop.core.publishers.base import (
    BasePublisher,
    extract_prefix,
    format_level,
    get_document_attributes,
)
from doorstop.core.types import is_item, iter_items

log = common.logger(__name__)
INDEX = "index.md"


class MarkdownPublisher(BasePublisher):
    """Markdown publisher."""

    def create_index(self, directory, index=INDEX, extensions=(".md",), tree=None):
        """Create an markdown index of all files in a directory.

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
            lines = self.lines_index(sorted(filenames), tree=tree)
            common.write_text("# Requirements index\n" + "\n".join(lines), path)
        else:
            log.warning("no files for {}".format(index))

    def _index_tree(self, tree, depth):
        """Recursively generate markdown index.

        :param tree: optional tree to determine index structure
        :param depth: depth recursed into tree
        """

        depth = depth + 1

        title = get_document_attributes(tree.document)["title"]
        prefix = extract_prefix(tree.document)
        filename = f"{prefix}.md"

        # Tree structure
        yield " " * (depth * 2 - 1) + f"* [{prefix}]({filename}) - {title}"
        # yield self.table_of_contents(linkify=True, obj=tree.document, depth=depth, heading=False)
        for child in tree.children:
            yield from self._index_tree(tree=child, depth=depth)

    def lines_index(self, filenames, tree=None):
        """Yield lines of Markdown for index.md.

        :param filenames: list of filenames to add to the index
        :param tree: optional tree to determine index structure
        """
        if tree:
            yield from self._index_tree(tree, depth=0)

        # Additional files
        if filenames:
            yield ""
            yield "### Published Documents:"
            for filename in filenames:
                name = os.path.splitext(filename)[0]
                yield " * [{n}]({f})".format(f=filename, n=name)

    def create_matrix(self, directory):
        """No traceability matrix for Markdown."""

    def format_attr_list(self, item, linkify):
        """Create a Markdown attribute list for a heading."""
        return " {{#{u}}}".format(u=item.uid) if linkify else ""

    def format_ref(self, item):
        """Format an external reference in Markdown."""
        if settings.CHECK_REF:
            path, line = item.find_ref()
            path = path.replace("\\", "/")  # always use unix-style paths
            if line:
                return "> `{p}` (line {line})".format(p=path, line=line)
            else:
                return "> `{p}`".format(p=path)
        else:
            return "> '{r}'".format(r=item.ref)

    def format_references(self, item):
        """Format an external reference in Markdown."""
        if settings.CHECK_REF:
            references = item.find_references()
            text_refs = []
            for ref_item in references:
                path, line = ref_item
                path = path.replace("\\", "/")  # always use unix-style paths

                if line:
                    text_refs.append("> `{p}` (line {line})".format(p=path, line=line))
                else:
                    text_refs.append("> `{p}`".format(p=path))

            return "\n".join(ref for ref in text_refs)
        else:
            references = item.references
            text_refs = []
            for ref_item in references:
                path = ref_item["path"]
                path = path.replace("\\", "/")  # always use unix-style paths
                text_refs.append("> '{r}'".format(r=path))
            return "\n".join(ref for ref in text_refs)

    def format_links(self, items, linkify):
        """Format a list of linked items in Markdown."""
        links = []
        for item in items:
            link = self.format_item_link(item, linkify=linkify)
            links.append(link)
        return ", ".join(links)

    def format_item_link(self, item, linkify=True):
        """Format an item link in Markdown."""
        if linkify and is_item(item):
            link = clean_link("{u}".format(u=self._generate_heading_from_item(item)))
            if item.header:
                return "[{u} {h}]({p}.md#{l})".format(
                    u=item.uid, l=link, h=item.header, p=item.document.prefix
                )
            return "[{u}]({p}.md#{l})".format(
                u=item.uid, l=link, p=item.document.prefix
            )
        else:
            return str(item.uid)  # if not `Item`, assume this is an `UnknownItem`

    def format_label_links(self, label, links, linkify):
        """Join a string of label and links with formatting."""
        if linkify:
            return "*{lb}* {ls}".format(lb=label, ls=links)
        else:
            return "*{lb} {ls}*".format(lb=label, ls=links)

    def table_of_contents(self, linkify=None, obj=None):
        """Generate a table of contents for a Markdown document."""

        toc = "### Table of Contents\n\n"
        toc_doc = obj

        for item in iter_items(toc_doc):
            if item.depth == 1:
                prefix = " * "
            else:
                prefix = "    " * (item.depth - 1)
                prefix += "* "

            # Check if item has the attribute heading.
            if item.heading:
                lines = item.text.splitlines()
                heading = lines[0] if lines else ""
            elif item.header:
                heading = "{h}".format(h=item.header)
            else:
                heading = item.uid

            if settings.PUBLISH_HEADING_LEVELS:
                level = format_level(item.level)
                lbl = "{lev} {h}".format(lev=level, h=heading)
            else:
                lbl = heading

            if linkify:
                link = clean_link(self._generate_heading_from_item(item))
                line = "{p}[{lbl}](#{l})\n".format(p=prefix, lbl=lbl, l=link)
            else:
                line = "{p}{lbl}\n".format(p=prefix, lbl=lbl)
            toc += line
        return toc

    def lines(self, obj, **kwargs):
        """Yield lines for a Markdown report.

        :param obj: Item, list of Items, or Document to publish
        :param linkify: turn links into hyperlinks

        :return: iterator of lines of text

        """
        linkify = kwargs.get("linkify", False)
        toc = kwargs.get("toc", False)
        if toc:
            yield self.table_of_contents(linkify=linkify, obj=obj)

        yield from self._lines_markdown(obj, **kwargs)

    def _generate_heading_from_item(self, item, to_html=False):
        """Generate a heading from an item in a consistent way for Markdown.

        This ensures that references between documents are consistent.
        """
        result = ""
        heading = "#" * item.depth
        level = format_level(item.level)
        if item.heading:
            text_lines = item.text.splitlines()
            if item.header:
                text_lines.insert(0, item.header)
            # Level and Text
            if settings.PUBLISH_HEADING_LEVELS:
                standard = "{h} {lev} {t}".format(
                    h=heading, lev=level, t=text_lines[0] if text_lines else ""
                )
            else:
                standard = "{h} {t}".format(
                    h=heading, t=text_lines[0] if text_lines else ""
                )
            attr_list = self.format_attr_list(item, True)
            result = standard + attr_list
        else:
            uid = item.uid
            if settings.ENABLE_HEADERS:
                if item.header:
                    if to_html:
                        uid = "{h} <small>{u}</small>".format(h=item.header, u=item.uid)
                    else:
                        uid = "{h} _{u}_".format(h=item.header, u=item.uid)
                else:
                    uid = "{u}".format(u=item.uid)

            # Level and UID
            if settings.PUBLISH_BODY_LEVELS:
                standard = "{h} {lev} {u}".format(h=heading, lev=level, u=uid)
            else:
                standard = "{h} {u}".format(h=heading, u=uid)

            attr_list = self.format_attr_list(item, True)
            result = standard + attr_list
        return result

    def _lines_markdown(self, obj, **kwargs):
        """Yield lines for a Markdown report.

        :param obj: Item, list of Items, or Document to publish
        :param linkify: turn links into hyperlinks

        :return: iterator of lines of text

        """
        linkify = kwargs.get("linkify", False)
        to_html = kwargs.get("to_html", False)
        for item in iter_items(obj):
            # Create iten heading.
            complete_heading = self._generate_heading_from_item(item, to_html=to_html)
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
                yield ""  # break before reference
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
                header_printed = False
                for attr in item.document.publish:
                    if not item.attribute(attr):
                        continue
                    if not header_printed:
                        header_printed = True
                        yield ""
                        yield "| Attribute | Value |"
                        yield "| --------- | ----- |"
                    yield "| {} | {} |".format(attr, item.attribute(attr))
                yield ""

            yield ""  # break between items


def clean_link(uid):
    """Clean a UID for use in a link.

    1. Strip leading # and spaces.
    2. Only smallcaps are allowed.
    3. Spaces are replaced with hyphens.
    5. All other special characters are removed.
    """
    uid = sub(r"^#*\s*", "", uid)
    uid = uid.lower()
    uid = uid.replace(" ", "-")
    uid = sub("[^a-z0-9-]", "", uid)
    return uid
