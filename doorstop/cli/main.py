#!/usr/bin/env python

"""Command-line interface for Doorstop."""

import os
import sys
import ast
import time
import argparse
import logging

from doorstop.cli import utilities
from doorstop.gui.main import _run as gui
from doorstop.core.builder import build
from doorstop.core import editor, importer, exporter, publisher
from doorstop import common
from doorstop.common import HelpFormatter, WarningFormatter, DoorstopError
from doorstop import settings


def main(args=None):  # pylint: disable=R0915
    """Process command-line arguments and run the program."""
    from doorstop import CLI, VERSION, DESCRIPTION

    # Shared options
    debug = argparse.ArgumentParser(add_help=False)
    debug.add_argument('-j', '--project', metavar='PATH',
                       help="path to the root of the project")
    debug.add_argument('-V', '--version', action='version', version=VERSION)
    debug.add_argument('-v', '--verbose', action='count', default=0,
                       help="enable verbose logging")
    shared = {'formatter_class': HelpFormatter, 'parents': [debug]}

    # Main parser
    parser = argparse.ArgumentParser(prog=CLI, description=DESCRIPTION,
                                     **shared)
    parser.add_argument('-F', '--no-reformat', action='store_true',
                        help="do not reformat item files during validation")
    parser.add_argument('-r', '--reorder', action='store_true',
                        help="reorder document levels during validation")
    parser.add_argument('-L', '--no-level-check', action='store_true',
                        help="do not validate document levels")
    parser.add_argument('-R', '--no-ref-check', action='store_true',
                        help="do not validate external file references")
    parser.add_argument('-C', '--no-child-check', action='store_true',
                        help="do not validate child (reverse) links")
    parser.add_argument('-g', '--gui', action='store_true',
                        help="launch the graphical user interface")
    subs = parser.add_subparsers(help="", dest='command', metavar="<command>")

    # Create subparser
    info = "create a new document directory"
    sub = subs.add_parser('create', description=info.capitalize() + '.',
                          help=info, **shared)
    sub.add_argument('prefix', help="document prefix for new item IDs")
    sub.add_argument('path', help="path to a directory for item files")
    sub.add_argument('-p', '--parent', help="prefix for parent item IDS")
    sub.add_argument('-d', '--digits', help="number of digits in item IDs")

    # Delete subparser
    info = "delete a document directory"
    sub = subs.add_parser('delete', description=info.capitalize() + '.',
                          help=info, **shared)
    sub.add_argument('prefix', help="prefix of document to delete")

    # Add subparser
    info = "create an item file in a document directory"
    sub = subs.add_parser('add', description=info.capitalize() + '.',
                          help=info, **shared)
    sub.add_argument('prefix',
                     help="document prefix for the new item")
    sub.add_argument('-l', '--level', help="desired item level (e.g. 1.2.3)")

    # Remove subparser
    info = "remove an item file from a document directory"
    sub = subs.add_parser('remove', description=info.capitalize() + '.',
                          help=info, **shared)
    sub.add_argument('id', metavar='ID',
                     help="item ID to remove from its document")

    # Link subparser
    info = "add a new link between two items"
    sub = subs.add_parser('link', description=info.capitalize() + '.',
                          help=info, **shared)
    sub.add_argument('child',
                     help="child item ID to link to the parent")
    sub.add_argument('parent',
                     help="parent item ID to link from the child")

    # Unlink subparser
    info = "remove a link between two items"
    sub = subs.add_parser('unlink', description=info.capitalize() + '.',
                          help=info, **shared)
    sub.add_argument('child',
                     help="child item ID to unlink from parent")
    sub.add_argument('parent',
                     help="parent item ID child is linked to")

    # Edit subparser
    info = "open an existing item or document for editing"
    sub = subs.add_parser('edit', description=info.capitalize() + '.',
                          help=info, **shared)
    sub.add_argument('label',
                     help="item ID or document prefix to open for editing")
    group = sub.add_mutually_exclusive_group()
    group.add_argument('-i', '--item', action='store_true',
                       help="indicates the 'label' is an item ID")
    group.add_argument('-d', '--document', action='store_true',
                       help="indicates the 'label' is a document prefix")
    group = sub.add_mutually_exclusive_group()
    group.add_argument('-y', '--yaml', action='store_true',
                       help="edit document as exported YAML (default)")
    group.add_argument('-c', '--csv', action='store_true',
                       help="edit document as exported CSV")
    group.add_argument('-t', '--tsv', action='store_true',
                       help="edit document as exported TSV")
    group.add_argument('-x', '--xlsx', action='store_true',
                       help="edit document as exported XLSX")
    sub.add_argument('-T', '--tool', metavar='PROGRAM',
                     help="text editor to open the document item")

    # Import subparser
    info = "import an existing document or item"
    sub = subs.add_parser('import', description=info.capitalize() + '.',
                          help=info, **shared)
    sub.add_argument('path', nargs='?',
                     help="path to previously exported document file")
    sub.add_argument('prefix', nargs='?', help="prefix of document for import")
    group = sub.add_mutually_exclusive_group()
    group.add_argument('-d', '--document', nargs=2, metavar='ARG',
                       help="import an existing document by: PREFIX PATH")
    group.add_argument('-i', '--item', nargs=2, metavar='ARG',
                       help="import an existing item by: PREFIX ID")
    sub.add_argument('-p', '--parent', metavar='PREFIX',
                     help="parent document prefix for imported document")
    sub.add_argument('-a', '--attrs', metavar='DICT',
                     help="dictionary of item attributes to import")
    sub.add_argument('-m', '--map', metavar='DICT',
                     help="dictionary of custom item attribute names")

    # Export subparser
    info = "export a document as YAML or another format"
    sub = subs.add_parser('export', description=info.capitalize() + '.',
                          help=info, **shared)
    sub.add_argument('prefix', help="prefix of document to export or 'all'")
    sub.add_argument('path', nargs='?',
                     help="path to exported file or directory for 'all'")
    group = sub.add_mutually_exclusive_group()
    group.add_argument('-y', '--yaml', action='store_true',
                       help="output YAML (default when no path)")
    group.add_argument('-c', '--csv', action='store_true',
                       help="output CSV (default for 'all')")
    group.add_argument('-t', '--tsv', action='store_true',
                       help="output TSV")
    group.add_argument('-x', '--xlsx', action='store_true',
                       help="output XLSX")
    sub.add_argument('-w', '--width', type=int,
                     help="limit line width on text output")

    # Publish subparser
    info = "publish a document as text or another format"
    sub = subs.add_parser('publish', description=info.capitalize() + '.',
                          help=info, **shared)
    sub.add_argument('prefix', help="prefix of document to publish or 'all'")
    sub.add_argument('path', nargs='?',
                     help="path to published file or directory for 'all'")
    group = sub.add_mutually_exclusive_group()
    group.add_argument('-t', '--text', action='store_true',
                       help="output text (default when no path)")
    group.add_argument('-m', '--markdown', action='store_true',
                       help="output Markdown")
    group.add_argument('-H', '--html', action='store_true',
                       help="output HTML (default for 'all')")
    sub.add_argument('-w', '--width', type=int,
                     help="limit line width on text output")
    sub.add_argument('-C', '--no-child-links', action='store_true',
                     help="include child links in published documents")

    # Parse arguments
    args = parser.parse_args(args=args)

    # Configure logging
    _configure_logging(args.verbose)

    # Configure settings
    _configure_settings(args)

    # Run the program
    if args.gui:
        logging.debug("launching GUI...")
        function = gui
    elif args.command:
        logging.debug("running command '{}'...".format(args.command))
        function = globals()['_run_' + args.command]
    else:
        logging.debug("launching main command...")
        function = _run
    try:
        success = function(args, os.getcwd(), parser.error)
    except KeyboardInterrupt:
        logging.debug("command cancelled")
        success = False
    if success:
        logging.debug("command succeeded")
    else:
        logging.debug("command failed")
        sys.exit(1)


def _configure_logging(verbosity=0):
    """Configure logging using the provided verbosity level (0+)."""
    assert common.STR_VERBOSITY == 3
    assert common.MAX_VERBOSITY == 4

    # Configure the logging level and format
    if verbosity == 0:
        level = settings.DEFAULT_LOGGING_LEVEL
        default_format = settings.DEFAULT_LOGGING_FORMAT
        verbose_format = settings.VERBOSE_LOGGING_FORMAT
    elif verbosity == 1:
        level = settings.VERBOSE_LOGGING_LEVEL
        default_format = settings.DEFAULT_LOGGING_FORMAT
        verbose_format = settings.VERBOSE_LOGGING_FORMAT
    elif verbosity == 2:
        level = settings.VERBOSE_LOGGING_LEVEL
        default_format = verbose_format = settings.VERBOSE_LOGGING_FORMAT
    elif verbosity == 3:
        level = settings.VERBOSE2_LOGGING_LEVEL
        default_format = verbose_format = settings.VERBOSE_LOGGING_FORMAT
    else:
        level = settings.VERBOSE2_LOGGING_LEVEL
        default_format = verbose_format = settings.VERBOSE2_LOGGING_FORMAT

    # Set a custom formatter
    logging.basicConfig(level=level)
    formatter = WarningFormatter(default_format, verbose_format)
    logging.root.handlers[0].setFormatter(formatter)

    # Warn about excessive verbosity
    if verbosity > common.MAX_VERBOSITY:
        msg = "maximum verbosity level is {}".format(common.MAX_VERBOSITY)
        logging.warn(msg)
        common.VERBOSITY = common.MAX_VERBOSITY
    else:
        common.VERBOSITY = verbosity


def _configure_settings(args):
    """Update settings based on the command-line options."""
    # Parse common settings
    if args.no_reformat is not None:
        settings.REFORMAT = not args.no_reformat
    if args.reorder is not None:
        settings.REORDER = args.reorder
    if args.no_level_check is not None:
        settings.CHECK_LEVELS = not args.no_level_check
    if args.no_ref_check is not None:
        settings.CHECK_REF = not args.no_ref_check
    if args.no_child_check is not None:
        settings.CHECK_CHILD_LINKS = not args.no_child_check
    # Parse subcommand settings
    if 'no_child_links' in args and args.no_child_links is not None:
        settings.PUBLISH_CHILD_LINKS = not args.no_child_links


def _run(args, cwd, err, catch=True):  # pylint: disable=W0613
    """Process arguments and run the `doorstop` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param err: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    try:
        print("validating tree...", flush=True)
        tree = build(cwd, root=args.project)
        tree.load()
        valid = tree.validate()
    except DoorstopError as error:
        if catch:
            logging.error(error)
            return False
        else:
            raise error

    if tree and valid:
        print()
        print(tree.draw())
        print()
    return valid


def _run_create(args, cwd, _, catch=True):
    """Process arguments and run the `doorstop create` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param err: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    try:
        tree = build(cwd, root=args.project)
        document = tree.create_document(args.path, args.prefix,
                                        parent=args.parent, digits=args.digits)
    except DoorstopError as error:
        if catch:
            logging.error(error)
            return False
        else:
            raise error

    print("created document: {} ({})".format(document.prefix,
                                             document.relpath))
    return True


def _run_delete(args, cwd, _, catch=True):
    """Process arguments and run the `doorstop delete` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param err: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    try:
        tree = build(cwd, root=args.project)
        document = tree.find_document(args.prefix)
        prefix, relpath = document.prefix, document.relpath
        document.delete()
    except DoorstopError as error:
        if catch:
            logging.error(error)
            return False
        else:
            raise error

    print("deleted document: {} ({})".format(prefix, relpath))
    return True


def _run_add(args, cwd, _, catch=True):
    """Process arguments and run the `doorstop add` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param err: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    try:
        tree = build(cwd, root=args.project)
        item = tree.add_item(args.prefix, level=args.level)
    except DoorstopError as error:
        if catch:
            logging.error(error)
            return False
        else:
            raise error

    print("added item: {} ({})".format(item.id, item.relpath))
    return True


def _run_remove(args, cwd, _, catch=True):
    """Process arguments and run the `doorstop remove` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param err: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    try:
        tree = build(cwd, root=args.project)
        item = tree.find_item(args.id)
        item.delete()
    except DoorstopError as error:
        if catch:
            logging.error(error)
            return False
        else:
            raise error

    print("removed item: {} ({})".format(item.id, item.relpath))
    return True


def _run_link(args, cwd, _, catch=True):
    """Process arguments and run the `doorstop link` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param err: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    try:
        tree = build(cwd, root=args.project)
        child, parent = tree.link_items(args.child, args.parent)
    except DoorstopError as error:
        if catch:
            logging.error(error)
            return False
        else:
            raise error

    msg = "linked items: {} ({}) -> {} ({})"
    print(msg.format(child.id, child.relpath, parent.id, parent.relpath))
    return True


def _run_unlink(args, cwd, _, catch=True):
    """Process arguments and run the `doorstop unlink` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param err: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    try:
        tree = build(cwd, root=args.project)
        child, parent = tree.unlink_items(args.child, args.parent)
    except DoorstopError as error:
        if catch:
            logging.error(error)
            return False
        else:
            raise error

    msg = "unlinked items: {} ({}) -> {} ({})"
    print(msg.format(child.id, child.relpath, parent.id, parent.relpath))
    return True


def _run_edit(args, cwd, err, catch=True):
    """Process arguments and run the `doorstop edit` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param err: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    item = document = None
    ext = _get_extension(args, '.yml', '.yml', whole_tree=False, err=err)

    try:

        # Build tree
        tree = build(cwd, root=args.project)

        # Find item or document
        if not args.document:
            try:
                item = tree.find_item(args.label)
            except DoorstopError as exc:
                if args.item:
                    raise exc from None
        if not item:
            document = tree.find_document(args.label)

        # Edit item
        if item:
            item.edit(tool=args.tool)
        # or edit document
        else:
            export_import(args, cwd, err, document, ext)

    except DoorstopError as error:
        if catch:
            logging.error(error)
            return False
        else:
            raise error

    if item:
        print("opened item: {} ({})".format(item.id, item.relpath))
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
    logging.debug("")
    logging.debug("running command '{}'...".format('export'))
    _run_export(args, cwd, err, catch=False)

    # Open the exported file
    editor.edit(path, tool=args.tool)

    # Import the file to the same document
    if utilities.ask("import from {}?".format(path)):
        logging.debug("running command '{}'...".format('import'))
        _run_import(args, cwd, err, catch=False)
        common.delete(path)
    else:

        # Delete the exported file
        print("import canceled")
        if utilities.ask("delete {}?".format(path), default='no'):
            common.delete(path)
        else:
            print("to manually import: doorstop import {0}".format(path))


def _run_import(args, cwd, err, catch=True):
    """Process arguments and run the `doorstop import` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param err: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    document = item = None

    # Parse arguments
    attrs = _literal_eval(args.attrs, err)
    mapping = _literal_eval(args.map, err)
    if args.path:
        if not args.prefix:
            err("when [path] specified, [prefix] is also required")
        elif args.document:
            err("'--document' cannot be used with [path] [prefix]")
        elif args.item:
            err("'--item' cannot be used with [path] [prefix]")
        ext = _get_extension(args, None, None, False, err)
    elif not (args.document or args.item):
        err("specify [path], '--document', or '--item' to import")

    # Import document or item
    try:
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
    except DoorstopError as error:
        if catch:
            logging.error(error)
            return False
        else:
            raise error

    # Display result
    if document:
        print("imported: {} ({})".format(document.prefix, document.relpath))
    else:
        assert item
        print("imported: {} ({})".format(item.id, item.relpath))
    return True


def _run_export(args, cwd, err, catch=True):
    """Process arguments and run the `doorstop export` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param err: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    # Parse arguments
    whole_tree = args.prefix == 'all'
    ext = _get_extension(args, '.yml', '.csv', whole_tree, err)

    # Export documents
    try:
        exporter.check(ext)
        tree = build(cwd, root=args.project)
        if not whole_tree:
            document = tree.find_document(args.prefix)
    except DoorstopError as error:
        if catch:
            logging.error(error)
            return False
        else:
            raise error

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


def _run_publish(args, cwd, err, catch=True):
    """Process arguments and run the `doorstop publish` subcommand.

    :param args: Namespace of CLI arguments
    :param cwd: current working directory
    :param err: function to call for CLI errors
    :param catch: catch and log :class:`~doorstop.common.DoorstopError`

    """
    # Parse arguments
    whole_tree = args.prefix == 'all'
    ext = _get_extension(args, '.txt', '.html', whole_tree, err)

    # Publish documents
    try:
        publisher.check(ext)
        tree = build(cwd, root=args.project)
        if not whole_tree:
            document = tree.find_document(args.prefix)
    except DoorstopError as error:
        if catch:
            logging.error(error)
            return False
        else:
            raise error

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


def _literal_eval(literal, err, default=None):
    """Convert an literal to its value."""
    try:
        return ast.literal_eval(literal) if literal else default
    except (SyntaxError, ValueError):
        err("invalid Python literal: {}".format(literal))


def _get_extension(args, ext_stdout, ext_file, whole_tree, err):
    """Determine the output file extensions from input arguments.

    :param args: Namespace of CLI arguments
    :param ext_stdout: default extension for standard output
    :param ext_file: default extension for file output
    :param whole_tree: indicates the path is a directory for the whole tree
    :param err: function to call for CLI errors

    :return: chosen extension

    """
    path = args.path if hasattr(args, 'path') else None
    ext = None

    # Get the default argument from a provided output path
    if path:
        if whole_tree:
            ext = ext_file
        else:
            if os.path.isdir(path):
                err("given a prefix, [path] must be a file, not a directory")
            ext = os.path.splitext(path)[-1]
        logging.debug("extension based on path: {}".format(ext or None))

    # Override the extension if a format is specified
    for _ext, option in {'.txt': 'text',
                         '.md': 'markdown',
                         '.html': 'html',
                         '.yml': 'yaml',
                         '.csv': 'csv',
                         '.xlsx': 'xlsx'}.items():
        try:
            if getattr(args, option):
                ext = _ext
                logging.debug("extension based on override: {}".format(ext))
                break
        except AttributeError:
            continue
    else:
        if not ext:
            if path:
                err("given a prefix, [path] must include an extension")
            else:
                ext = ext_stdout
            logging.debug("extension based on default: {}".format(ext))

    return ext


if __name__ == '__main__':  # pragma: no cover (manual test)
    main()
