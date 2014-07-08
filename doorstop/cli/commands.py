"""Command functions."""

import time
import logging

from doorstop import common
from doorstop.cli import utilities
from doorstop.core.builder import build
from doorstop.core import editor, importer, exporter, publisher


def get(name):
    """Get a command function by name."""
    if name:
        logging.debug("running command '{}'...".format(name))
        return globals()['run_' + name]
    else:
        logging.debug("launching main command...")
        return run


def run(args, cwd, err, catch=True):  # pylint: disable=W0613
    """Process arguments and run the `doorstop` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param err: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    with utilities.capture(catch=catch) as success:
        print("validating tree...", flush=True)
        tree = build(cwd, root=args.project)
        tree.load()
        valid = tree.validate()
    if not success:
        return False

    if tree and valid:
        print()
        print(tree.draw())
        print()

    return valid


def run_create(args, cwd, _, catch=True):
    """Process arguments and run the `doorstop create` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param err: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    with utilities.capture(catch=catch) as success:
        tree = build(cwd, root=args.project)
        document = tree.create_document(args.path, args.prefix,
                                        parent=args.parent, digits=args.digits)
    if not success:
        return False

    print("created document: {} ({})".format(document.prefix,
                                             document.relpath))
    return True


def run_delete(args, cwd, _, catch=True):
    """Process arguments and run the `doorstop delete` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param err: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    with utilities.capture(catch=catch) as success:
        tree = build(cwd, root=args.project)
        document = tree.find_document(args.prefix)
        prefix, relpath = document.prefix, document.relpath
        document.delete()
    if not success:
        return False

    print("deleted document: {} ({})".format(prefix, relpath))

    return True


def run_add(args, cwd, _, catch=True):
    """Process arguments and run the `doorstop add` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param err: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    with utilities.capture(catch=catch) as success:
        tree = build(cwd, root=args.project)
        item = tree.add_item(args.prefix, level=args.level)
    if not success:
        return False

    print("added item: {} ({})".format(item.id, item.relpath))

    return True


def run_remove(args, cwd, _, catch=True):
    """Process arguments and run the `doorstop remove` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param err: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    with utilities.capture(catch=catch) as success:
        tree = build(cwd, root=args.project)
        item = tree.find_item(args.id)
        item.delete()
    if not success:
        return False

    print("removed item: {} ({})".format(item.id, item.relpath))

    return True


def run_link(args, cwd, _, catch=True):
    """Process arguments and run the `doorstop link` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param err: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    with utilities.capture(catch=catch) as success:
        tree = build(cwd, root=args.project)
        child, parent = tree.link_items(args.child, args.parent)
    if not success:
        return False

    msg = "linked items: {} ({}) -> {} ({})"
    print(msg.format(child.id, child.relpath, parent.id, parent.relpath))

    return True


def run_unlink(args, cwd, _, catch=True):
    """Process arguments and run the `doorstop unlink` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param err: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    with utilities.capture(catch=catch) as success:
        tree = build(cwd, root=args.project)
        child, parent = tree.unlink_items(args.child, args.parent)
    if not success:
        return False

    msg = "unlinked items: {} ({}) -> {} ({})"
    print(msg.format(child.id, child.relpath, parent.id, parent.relpath))

    return True


def run_edit(args, cwd, err, catch=True):
    """Process arguments and run the `doorstop edit` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param err: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    item = document = None
    ext = utilities.get_ext(args, '.yml', '.yml', whole_tree=False, err=err)

    with utilities.capture(catch=catch) as success:
        tree = build(cwd, root=args.project)
        # find item or document
        if not args.document:
            try:
                item = tree.find_item(args.label)
            except common.DoorstopError as exc:
                if args.item:
                    raise exc from None
        if not item:
            document = tree.find_document(args.label)
        # edit item or document
        if item:
            item.edit(tool=args.tool)
        else:
            export_import(args, cwd, err, document, ext)
    if not success:
        return False

    if item:
        print("opened item: {} ({})".format(item.id, item.relpath))

    return True


def run_import(args, cwd, err, catch=True):
    """Process arguments and run the `doorstop import` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param err: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    document = item = None

    # Parse arguments
    attrs = utilities.literal_eval(args.attrs, err)
    mapping = utilities.literal_eval(args.map, err)
    if args.path:
        if not args.prefix:
            err("when [path] specified, [prefix] is also required")
        elif args.document:
            err("'--document' cannot be used with [path] [prefix]")
        elif args.item:
            err("'--item' cannot be used with [path] [prefix]")
        ext = utilities.get_ext(args, None, None, False, err)
    elif not (args.document or args.item):
        err("specify [path], '--document', or '--item' to import")

    # Import document or item
    with utilities.capture(catch=catch) as success:
        if args.path:
            tree = build(cwd, root=args.project)
            document = tree.find_document(args.prefix)
            msg = "importing {} into {}...".format(args.path, document)
            print(msg, flush=True)
            importer.import_file(args.path, document, ext, mapping=mapping)
        elif args.document:
            prefix, path = args.document
            document = importer.create_document(prefix, path,
                                                parent=args.parent)
        elif args.item:
            prefix, identifier = args.item
            item = importer.add_item(prefix, identifier, attrs=attrs)
    if not success:
        return False

    # Display result
    if document:
        print("imported: {} ({})".format(document.prefix, document.relpath))
    else:
        assert item
        print("imported: {} ({})".format(item.id, item.relpath))

    return True


def run_export(args, cwd, err, catch=True):
    """Process arguments and run the `doorstop export` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param err: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    # Parse arguments
    whole_tree = args.prefix == 'all'
    ext = utilities.get_ext(args, '.yml', '.csv', whole_tree, err)

    # Export documents
    with utilities.capture(catch=catch) as success:
        exporter.check(ext)
        tree = build(cwd, root=args.project)
        if not whole_tree:
            document = tree.find_document(args.prefix)
    if not success:
        return False

    # Write to output file(s)
    if args.path:
        if whole_tree:
            print("exporting tree to {}...".format(args.path), flush=True)
            path = exporter.export(tree, args.path, ext)
        else:
            msg = "exporting {} to {}...".format(document, args.path)
            print(msg, flush=True)
            path = exporter.export(document, args.path, ext)
        if path:
            print("exported: {}".format(path))

    # Display to standard output
    else:
        if whole_tree:
            err("only single documents can be displayed")
        for line in exporter.export_lines(document, ext):
            print(line)

    return True


def run_publish(args, cwd, err, catch=True):
    """Process arguments and run the `doorstop publish` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param err: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    # Parse arguments
    whole_tree = args.prefix == 'all'
    ext = utilities.get_ext(args, '.txt', '.html', whole_tree, err)

    # Publish documents
    with utilities.capture(catch=catch) as success:
        publisher.check(ext)
        tree = build(cwd, root=args.project)
        if not whole_tree:
            document = tree.find_document(args.prefix)
    if not success:
        return False

    # Set publishing arguments
    kwargs = {}
    if args.width:
        kwargs['width'] = args.width

    # Write to output file(s)
    if args.path:
        if whole_tree:
            print("publishing tree to {}...".format(args.path), flush=True)
            path = publisher.publish(tree, args.path, ext, **kwargs)
        else:
            msg = "publishing {} to {}...".format(document, args.path)
            print(msg, flush=True)
            path = publisher.publish(document, args.path, ext, **kwargs)
        if path:
            print("published: {}".format(path))

    # Display to standard output
    else:
        if whole_tree:
            err("only single documents can be displayed")
        for line in publisher.publish_lines(document, ext, **kwargs):
            print(line)

    return True


def export_import(args, cwd, err, document, ext):
    """Edit a document by calling export followed by import.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param err: function to call for CLI errors
    :param document: :class:`~doorstop.core.document.Document` to edit
    :param ext: extension for export format

    """
    # Export the document to file
    args.prefix = document.prefix
    path = "{}-{}{}".format(args.prefix, int(time.time()), ext)
    args.path = path
    get('export')(args, cwd, err, catch=False)

    # Open the exported file
    editor.edit(path, tool=args.tool)

    # Import the file to the same document
    if utilities.ask("import from {}?".format(path)):
        args.attrs = {}
        args.map = {}
        get('import')(args, cwd, err, catch=False)
        common.delete(path)
    else:
        print("import canceled")
        if utilities.ask("delete {}?".format(path), default='no'):
            common.delete(path)
        else:
            print("to manually import: doorstop import {0}".format(path))
