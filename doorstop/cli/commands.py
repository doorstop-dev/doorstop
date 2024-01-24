# SPDX-License-Identifier: LGPL-3.0-only

"""Command functions."""

import os
import time
from typing import Set

from doorstop import common, server
from doorstop.cli import utilities
from doorstop.core import editor, exporter, importer, publisher
from doorstop.core.builder import build

log = common.logger(__name__)


class CycleTracker:
    """A cycle tracker to detect cyclic references between items.

    The cycle tracker uses a standard algorithm to detect cycles in a directed
    graph (not necessarily connected) using a depth first search with a bit of
    graph colouring.  The time complexity is O(|V| + |E|).  The vertices are
    the items.  The edges are the links between items.

    """

    def __init__(self):
        """Initialize a cycle tracker."""
        self.discovered: Set[str] = set()
        self.finished: Set[str] = set()

    def _dfs_visit(self, uid, tree):
        """Do a depth first search visit of the specified item.

        :param uid: the UID of the item to visit
        :param tree: the document hierarchy tree

        :return: generator of :class:`~doorstop.common.DoorstopWarning`

        """
        self.discovered.add(uid)
        item = tree.find_item(uid)

        for pid in item.links:
            # Detect cycles via a back edge
            if pid in self.discovered:
                msg = "detected a cycle with a back edge from {} to {}".format(pid, uid)
                yield common.DoorstopWarning(msg)

            # Recurse, if this a fresh item
            if pid not in self.discovered and pid not in self.finished:
                yield from self._dfs_visit(pid, tree)

        self.discovered.remove(uid)
        self.finished.add(uid)

    def __call__(self, item, document, tree):
        """Get cycles which include the specified item.

        :param item: the UID of the item to get the cycles for
        :param document: unused
        :param tree: the document hierarchy tree

        :return: generator of :class:`~doorstop.common.DoorstopWarning`

        """
        if item not in self.discovered and item not in self.finished:
            yield from self._dfs_visit(item, tree)


def get(name):
    """Get a command function by name."""
    if name:
        log.debug("running command '{}'...".format(name))
        return globals()["run_" + name]
    else:
        log.debug("launching main command...")
        return run


def run(args, cwd, error, catch=True):  # pylint: disable=W0613
    """Process arguments and run the `doorstop` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param error: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    with utilities.capture(catch=catch) as success:
        # get the tree
        tree = _get_tree(args, cwd, load=True)

        # validate it
        utilities.show("validating items...", flush=True)
        cycle_tracker = CycleTracker()
        valid = tree.validate(skip=args.skip, item_hook=cycle_tracker)

    if not success:
        return False

    if len(tree) > 1 and valid:
        utilities.show("\n" + tree.draw() + "\n")

    return valid


def run_create(args, cwd, _, catch=True):
    """Process arguments and run the `doorstop create` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param error: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    with utilities.capture(catch=catch) as success:
        # get the tree
        tree = _get_tree(args, cwd)

        # create a new document
        document = tree.create_document(
            args.path,
            args.prefix,
            parent=args.parent,
            digits=args.digits,
            sep=args.separator,
            itemformat=args.itemformat,
        )

    if not success:
        return False

    utilities.show(
        "created document: {} ({})".format(document.prefix, document.relpath)
    )
    return True


def run_delete(args, cwd, _, catch=True):
    """Process arguments and run the `doorstop delete` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param error: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    with utilities.capture(catch=catch) as success:
        # get the document
        tree = _get_tree(args, cwd)
        document = tree.find_document(args.prefix)

        # delete it
        prefix, relpath = document.prefix, document.relpath
        document.delete()

    if not success:
        return False

    utilities.show("deleted document: {} ({})".format(prefix, relpath))

    return True


def run_add(args, cwd, _, catch=True):
    """Process arguments and run the `doorstop add` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param error: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    with utilities.capture(catch=catch) as success:
        # get the document
        request_next_number = _request_next_number(args)
        tree = _get_tree(args, cwd, request_next_number=request_next_number)
        document = tree.find_document(args.prefix)

        # add items to it
        for _ in range(args.count):
            item = document.add_item(
                level=args.level, defaults=args.defaults, name=args.name, reorder=args.noreorder
            )
            utilities.show("added item: {} ({})".format(item.uid, item.relpath))

        # Edit item if requested
        if args.edit:
            item.edit(tool=args.tool)

    if not success:
        return False

    return True


def run_remove(args, cwd, _, catch=True):
    """Process arguments and run the `doorstop remove` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param error: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    with utilities.capture(catch=catch) as success:
        # get the item
        tree = _get_tree(args, cwd)
        item = tree.find_item(args.uid)

        # delete it
        item.delete()

    if not success:
        return False

    utilities.show("removed item: {} ({})".format(item.uid, item.relpath))

    return True


def run_edit(args, cwd, error, catch=True):
    """Process arguments and run the `doorstop edit` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param error: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    item = document = None
    ext = utilities.get_ext(args, error, ".yml", ".yml", whole_tree=False)

    with utilities.capture(catch=catch) as success:
        # get the item or document
        request_next_number = _request_next_number(args)
        tree = _get_tree(args, cwd, request_next_number=request_next_number)
        if not args.document:
            try:
                item = tree.find_item(args.label)
            except common.DoorstopError as exc:
                if args.item:
                    raise exc from None  # pylint: disable=raising-bad-type
        if not item:
            document = tree.find_document(args.label)

        # edit it
        if item:
            item.edit(tool=args.tool, edit_all=args.all)
        else:
            _export_import(args, cwd, error, document, ext)

    if not success:
        return False

    if item:
        utilities.show("opened item: {} ({})".format(item.uid, item.relpath))

    return True


def run_reorder(args, cwd, error, catch=True, _tree=None):
    """Process arguments and run the `doorstop reorder` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param error: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    reordered = False

    with utilities.capture(catch=catch) as success:
        # get the document
        tree = _tree or _get_tree(args, cwd)
        document = tree.find_document(args.prefix)

    if not success:
        return False

    with utilities.capture(catch=catch) as success:
        # automatically order
        if args.auto:
            msg = "reordering document {}...".format(document)
            utilities.show(msg, flush=True)
            document.reorder(manual=False)
            reordered = True

        # or, reorder from a previously updated index
        elif document.index:
            relpath = os.path.relpath(document.index, cwd)
            if utilities.ask("reorder from '{}'?".format(relpath)):
                msg = "reordering document {}...".format(document)
                utilities.show(msg, flush=True)
                document.reorder(automatic=not args.manual)
                reordered = True
            else:
                del document.index

        # or, create a new index to update
        else:
            document.index = True  # create index
            relpath = os.path.relpath(document.index, cwd)
            editor.edit(relpath, tool=args.tool)
            get("reorder")(args, cwd, error, catch=False, _tree=tree)

    if not success:
        msg = "after fixing the error: doorstop reorder {}".format(document)
        utilities.show(msg)
        return False

    if reordered:
        utilities.show("reordered document: {}".format(document))

    return True


def run_link(args, cwd, _, catch=True):
    """Process arguments and run the `doorstop link` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param error: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    with utilities.capture(catch=catch) as success:
        # get the tree
        tree = _get_tree(args, cwd)

        # link items
        child, parent = tree.link_items(args.child, args.parent)

    if not success:
        return False

    msg = "linked items: {} ({}) -> {} ({})".format(
        child.uid, child.relpath, parent.uid, parent.relpath
    )
    utilities.show(msg)

    return True


def run_unlink(args, cwd, _, catch=True):
    """Process arguments and run the `doorstop unlink` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param error: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    with utilities.capture(catch=catch) as success:
        # get the tree
        tree = _get_tree(args, cwd)

        # unlink items
        child, parent = tree.unlink_items(args.child, args.parent)

    if not success:
        return False

    msg = "unlinked items: {} ({}) -> {} ({})".format(
        child.uid, child.relpath, parent.uid, parent.relpath
    )
    utilities.show(msg)

    return True


def run_clear(args, cwd, error, catch=True):
    """Process arguments and run the `doorstop clear` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param error: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    with utilities.capture(catch=catch) as success:
        tree = _get_tree(args, cwd)

        if args.parents:
            # Check that the parent item UIDs exist
            for pid in args.parents:
                tree.find_item(pid)

            pids = " to " + ", ".join(args.parents)
        else:
            pids = ""

        for item in _iter_items(args, tree, error):
            msg = "clearing item {}'s suspect links{}...".format(item.uid, pids)
            utilities.show(msg)
            item.clear(parents=args.parents)

    if not success:
        return False

    return True


def run_review(args, cwd, error, catch=True):
    """Process arguments and run the `doorstop review` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param error: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    with utilities.capture(catch=catch) as success:
        tree = _get_tree(args, cwd)

        for item in _iter_items(args, tree, error):
            utilities.show("marking item {} as reviewed...".format(item.uid))
            item.review()

    if not success:
        return False

    return True


def run_import(args, cwd, error, catch=True, _tree=None):
    """Process arguments and run the `doorstop import` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param error: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    document = item = None
    attrs = utilities.literal_eval(args.attrs, error)
    mapping = utilities.literal_eval(args.map, error)
    if args.path:
        if not args.prefix:
            error("when [path] specified, [prefix] is also required")
        elif args.document:
            error("'--document' cannot be used with [path] [prefix]")
        elif args.item:
            error("'--item' cannot be used with [path] [prefix]")
        ext = utilities.get_ext(args, error, None, None)
    elif not (args.document or args.item):
        error("specify [path], '--document', or '--item' to import")

    with utilities.capture(catch=catch) as success:
        if args.path:
            # get the document
            request_next_number = _request_next_number(args)
            tree = _tree or _get_tree(
                args, cwd, request_next_number=request_next_number
            )
            document = tree.find_document(args.prefix)

            # import items into it
            msg = "importing '{}' into document {}...".format(args.path, document)
            utilities.show(msg, flush=True)
            importer.import_file(args.path, document, ext, mapping=mapping)

        elif args.document:
            prefix, path = args.document
            document = importer.create_document(prefix, path, parent=args.parent)
        elif args.item:
            prefix, uid = args.item
            request_next_number = _request_next_number(args)
            item = importer.add_item(
                prefix, uid, attrs=attrs, request_next_number=request_next_number
            )
    if not success:
        return False

    if document:
        utilities.show(
            "imported document: {} ({})".format(document.prefix, document.relpath)
        )
    else:
        assert item
        utilities.show("imported item: {} ({})".format(item.uid, item.relpath))

    return True


def run_export(args, cwd, error, catch=True, auto=False, _tree=None):
    """Process arguments and run the `doorstop export` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param error: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    :param auto: include placeholders for new items on import

    """
    whole_tree = args.prefix == "all"
    ext = utilities.get_ext(args, error, ".yml", ".csv", whole_tree=whole_tree)

    # Get the tree or document
    with utilities.capture(catch=catch) as success:
        exporter.check(ext)
        tree = _tree or _get_tree(args, cwd, load=whole_tree)
        if not whole_tree:
            document = tree.find_document(args.prefix)

    if not success:
        return False

    # Write to output file(s)
    if args.path:
        if whole_tree:
            msg = "exporting tree to '{}'...".format(args.path)
            utilities.show(msg, flush=True)
            path = exporter.export(tree, args.path, ext, auto=auto)
        else:
            msg = "exporting document {} to '{}'...".format(document, args.path)
            utilities.show(msg, flush=True)
            path = exporter.export(document, args.path, ext, auto=auto)
        if path:
            utilities.show("exported: {}".format(path))

    # Or, display to standard output
    else:
        if whole_tree:
            error("only single documents can be displayed")
        for line in exporter.export_lines(document, ext):
            utilities.show(line)

    return True


def run_publish(args, cwd, error, catch=True):
    """Process arguments and run the `doorstop publish` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param error: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    whole_tree = args.prefix == "all"
    ext = utilities.get_ext(args, error, ".txt", ".html", whole_tree)

    # Get the tree or document
    with utilities.capture(catch=catch) as success:
        publisher.check(ext)
        tree = _get_tree(args, cwd, load=whole_tree)
        if not whole_tree:
            document = tree.find_document(args.prefix)

    if not success:
        return False

    # Set publishing arguments
    kwargs = {}
    if args.width:
        kwargs["width"] = args.width

    # Write to output file(s)
    if args.path:
        path = os.path.abspath(os.path.join(cwd, args.path))
        if whole_tree:
            msg = "publishing tree to '{}'...".format(path)
            utilities.show(msg, flush=True)
            published_path = publisher.publish(
                tree, path, ext, template=args.template, **kwargs
            )
        else:
            msg = "publishing document {} to '{}'...".format(document, path)
            utilities.show(msg, flush=True)
            published_path = publisher.publish(
                document, path, ext, template=args.template, **kwargs
            )
        if published_path:
            utilities.show("published: {}".format(published_path))

    # Or, display to standard output
    else:
        if whole_tree:
            error("only single documents can be displayed")
        for line in publisher.publish_lines(document, ext, **kwargs):
            utilities.show(line)

    return True


def _request_next_number(args):
    """Get the server's "next number" method if a server exists."""
    if args.force:
        log.warning("creating items without the server...")
        return None
    else:
        server.check()
        return server.get_next_number


def _get_tree(args, cwd, request_next_number=None, load=False):
    """Build a tree and optionally load all documents.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param request_next_number: server method to get a document's next number
    :param load: force the early loading of all documents

    :return: built :class:`~doorstop.core.tree.Tree`

    """
    utilities.show("building tree...", flush=True)
    tree = build(cwd=cwd, root=args.project, request_next_number=request_next_number)

    if load:
        utilities.show("loading documents...", flush=True)
        tree.load()

    return tree


def _iter_items(args, tree, error):
    """Iterate through items.

    :param args: Namespace of CLI arguments
    :param tree: the document hierarchy tree
    :param error: function to call for CLI errors

    Items are filtered to:

    - `args.label` == 'all': all items
    - `args.label` == document prefix: the document's items
    - `args.label` == item UID: a single item

    Documents and items are inferred unless flagged by:

    - `args.document`: `args.label` is a prefix
    - `args.item`: `args.label` is an UID

    """
    # Parse arguments
    if args.label == "all":
        if args.item:
            error("argument -i/--item: not allowed with 'all'")
        if args.document:
            error("argument -d/--document: not allowed with 'all'")

    # Build tree
    item = None
    document = None

    # Determine if tree, document, or item was requested
    if args.label != "all":
        if not args.item:
            try:
                document = tree.find_document(args.label)
            except common.DoorstopError as exc:
                if args.document:
                    raise exc from None  # pylint: disable=raising-bad-type
        if not document:
            item = tree.find_item(args.label)

    # Yield items from the requested object
    if item:
        yield item
    elif document:
        for item in document:
            yield item
    else:
        for document in tree:
            for item in document:
                yield item


def _export_import(args, cwd, error, document, ext):
    """Edit a document by calling export followed by import.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param error: function to call for CLI errors
    :param document: :class:`~doorstop.core.document.Document` to edit
    :param ext: extension for export format

    """
    # Export the document to file
    args.prefix = document.prefix
    path = "{}-{}{}".format(args.prefix, int(time.time()), ext)
    args.path = path
    get("export")(args, cwd, error, catch=False, auto=True, _tree=document.tree)

    # Open the exported file
    editor.edit(path, tool=args.tool)

    # Import the file to the same document
    if utilities.ask("import from '{}'?".format(path)):
        args.attrs = {}
        args.map = {}
        get("import")(args, cwd, error, catch=False, _tree=document.tree)
        common.delete(path)
    else:
        utilities.show("import canceled")
        if utilities.ask("delete '{}'?".format(path)):
            common.delete(path)
        else:
            msg = "to manually import: doorstop import {0}".format(path)
            utilities.show(msg)
