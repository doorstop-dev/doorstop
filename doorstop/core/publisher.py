# SPDX-License-Identifier: LGPL-3.0-only

"""Functions to publish documents and items."""

import os

from doorstop import common, settings
from doorstop.common import DoorstopError
from doorstop.core.publishers.html import HtmlPublisher
from doorstop.core.publishers.latex import LaTeXPublisher
from doorstop.core.publishers.markdown import MarkdownPublisher
from doorstop.core.publishers.text import TextPublisher
from doorstop.core.types import is_tree, iter_documents

log = common.logger(__name__)


def publish(
    obj,
    path,
    ext=None,
    linkify=None,
    index=None,
    matrix=None,
    template=None,
    toc=True,
    **kwargs,
):
    """Publish an object to a given format.

    The function can be called in two ways:

    1. document or item-like object + output file path
    2. tree-like object + output directory path

    :param obj: (1) Item, list of Items, Document or (2) Tree
    :param path: (1) output file path or (2) output directory path
    :param ext: file extension to override output extension
    :param linkify: turn links into hyperlinks (for Markdown, HTML or LaTeX)
    :param index: create an index.html (for HTML)
    :param matrix: create a traceability matrix, traceability.csv

    :raises: :class:`doorstop.common.DoorstopError` for unknown file formats

    :return: output location if files created, else None

    """
    # Check that we have something to publish first.
    if is_tree(obj):
        if len(obj) == 0:
            raise DoorstopError("nothing to publish")

    # Determine the output format
    ext = ext or os.path.splitext(path)[-1] or ".html"
    publisher = check(ext, obj=obj)

    # Setup publisher.
    publisher.setPath(path)
    publisher.setup(linkify, index, matrix)

    # Process templates.
    publisher.processTemplates(template)
    log.info("Template = {}".format(publisher.getTemplate()))
    # Run all preparations.
    publisher.preparePublish()

    # Publish documents
    count = 0
    for obj2, path2 in iter_documents(obj, path, ext):
        count += 1
        # Run all special actions.
        publisher.publishAction(obj2, path2)

        # Publish content to the specified path
        log.info("publishing to {}...".format(publisher.getDocumentPath()))
        lines = publish_lines(
            obj2,
            ext,
            publisher=publisher,
            linkify=publisher.getLinkify(),
            template=publisher.getTemplate(),
            toc=toc,
            **kwargs,
        )
        common.write_lines(
            lines, publisher.getDocumentPath(), end=settings.WRITE_LINESEPERATOR
        )
        if obj2.copy_assets(publisher.getAssetsPath()):
            log.info(
                "Copied assets from %s to %s", obj.assets, publisher.getAssetsPath()
            )

    # Create index
    if publisher.getIndex():
        publisher.create_index(path, tree=obj if is_tree(obj) else None)

    # Create traceability matrix
    if (publisher.getIndex() or ext == ".tex") and (publisher.getMatrix()):
        publisher.create_matrix(path)

    # Run all concluding operations.
    publisher.concludePublish()

    # Return the published path
    msg = "published to {} file{}".format(count, "s" if count > 1 else "")
    log.info(msg)
    return path


def publish_lines(obj, ext=".txt", publisher=None, **kwargs):
    """Yield lines for a report in the specified format.

    :param obj: Item, list of Items, or Document to publish
    :param ext: file extension to specify the output format

    """
    if not publisher:
        publisher = check(ext, obj=obj)
    gen = publisher.get_line_generator()
    log.debug("yielding {} as lines of {}...".format(obj, ext))
    yield from gen(obj, **kwargs)


def check(ext, obj=None):
    """Confirm an extension is supported for publish.

    :raises: :class:`doorstop.common.DoorstopError` for unknown formats

    :return: publisher class if available

    """
    # Mapping from file extension to class.
    PUBLISHER_LIST = {
        ".txt": TextPublisher(obj, ext),
        ".md": MarkdownPublisher(obj, ext),
        ".html": HtmlPublisher(obj, ext),
        ".tex": LaTeXPublisher(obj, ext),
    }

    exts = ", ".join(ext for ext in PUBLISHER_LIST)
    msg = "unknown publish format: {} (options: {})".format(ext or None, exts)
    exc = DoorstopError(msg)

    try:
        publisherClass = PUBLISHER_LIST[ext]
    except KeyError:
        raise exc from None
    else:
        log.debug("found publisher class for: {}".format(ext))
        return publisherClass
