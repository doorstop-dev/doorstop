# SPDX-License-Identifier: LGPL-3.0-only

"""Functions to publish documents and items."""


from doorstop import common, settings
from doorstop.core.publishers.base import BasePublisher, format_level
from doorstop.core.types import is_item, iter_items

log = common.logger(__name__)


class MarkdownPublisher(BasePublisher):
    """Markdown publisher."""

    def create_index(self, directory, index=None, extensions=(".html",), tree=None):
        """No index for Markdown."""

    def create_matrix(self, directory):
        """No traceability matrix for Markdown."""

    def format_attr_list(self, item, linkify):
        """Create a Markdown attribute list for a heading."""
        return " {{#{u} }}".format(u=item.uid) if linkify else ""

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

    def format_links(self, items, linkify, to_html=False):
        """Format a list of linked items in Markdown."""
        links = []
        for item in items:
            link = self.format_item_link(item, linkify=linkify)
            links.append(link)
        return ", ".join(links)

    def format_item_link(self, item, linkify=True):
        """Format an item link in Markdown."""
        if linkify and is_item(item):
            if item.header:
                return "[{u} {h}]({p}.md#{u})".format(
                    u=item.uid, h=item.header, p=item.document.prefix
                )
            return "[{u}]({p}.md#{u})".format(u=item.uid, p=item.document.prefix)
        else:
            return str(item.uid)  # if not `Item`, assume this is an `UnknownItem`

    def format_label_links(self, label, links, linkify):
        """Join a string of label and links with formatting."""
        if linkify:
            return "*{lb}* {ls}".format(lb=label, ls=links)
        else:
            return "*{lb} {ls}*".format(lb=label, ls=links)

    def lines(self, obj, **kwargs):
        """Yield lines for a Markdown report.

        :param obj: Item, list of Items, or Document to publish
        :param linkify: turn links into hyperlinks (for conversion to HTML)

        :return: iterator of lines of text

        """
        yield from self._lines_markdown(obj, **kwargs)

    def _lines_markdown(self, obj, **kwargs):
        """Yield lines for a Markdown report.

        :param obj: Item, list of Items, or Document to publish
        :param linkify: turn links into hyperlinks (for conversion to HTML)

        :return: iterator of lines of text

        """
        linkify = kwargs.get("linkify", False)
        to_html = kwargs.get("to_html", False)
        for item in iter_items(obj):
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
                yield standard + attr_list
                yield from text_lines[1:]
            else:
                uid = item.uid
                if settings.ENABLE_HEADERS:
                    if item.header:
                        uid = "{h} <small>{u}</small>".format(h=item.header, u=item.uid)
                    else:
                        uid = "{u}".format(u=item.uid)

                # Level and UID
                if settings.PUBLISH_BODY_LEVELS:
                    standard = "{h} {lev} {u}".format(h=heading, lev=level, u=uid)
                else:
                    standard = "{h} {u}".format(h=heading, u=uid)

                attr_list = self.format_attr_list(item, True)
                yield standard + attr_list

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
                    links = self.format_links(items2, linkify, to_html=to_html)
                    label_links = self.format_label_links(label, links, linkify)
                    yield label_links

                # Child links
                if settings.PUBLISH_CHILD_LINKS:
                    items2 = item.find_child_items()
                    if items2:
                        yield ""  # break before links
                        label = "Child links:"
                        links = self.format_links(items2, linkify, to_html=to_html)
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
