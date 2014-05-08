#!/usr/bin/env python

"""Command-line interface for Doorstop."""

import os
import sys
import ast
import argparse
import logging

from doorstop.gui.main import _run as gui
from doorstop.core.tree import build
from doorstop.core import report, importer
from doorstop import common
from doorstop.common import HelpFormatter, WarningFormatter, DoorstopError
from doorstop import settings


def main(args=None):  # pylint: disable=R0915
    """Process command-line arguments and run the program."""
    from doorstop import CLI, VERSION

    # Shared options
    debug = argparse.ArgumentParser(add_help=False)
    debug.add_argument('-j', '--project', metavar='PATH',
                       help="path to the root of the project")
    debug.add_argument('-V', '--version', action='version', version=VERSION)
    debug.add_argument('-v', '--verbose', action='count', default=0,
                       help="enable verbose logging")
    shared = {'formatter_class': HelpFormatter, 'parents': [debug]}

    # Main parser
    parser = argparse.ArgumentParser(prog=CLI, description=__doc__, **shared)
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

    # New subparser
    sub = subs.add_parser('new',
                          help="create a new document directory",
                          **shared)
    sub.add_argument('prefix', help="document prefix for new item IDs")
    sub.add_argument('path', help="path to a directory for item files")
    sub.add_argument('-p', '--parent', help="prefix for parent item IDS")
    sub.add_argument('-d', '--digits', help="number of digits in item IDs")

    # Add subparser
    sub = subs.add_parser('add',
                          help="create an item file in a document directory",
                          **shared)
    sub.add_argument('prefix',
                     help="document prefix for the new item")
    sub.add_argument('-l', '--level', help="desired item level (e.g. 1.2.3)")

    # Remove subparser
    sub = subs.add_parser('remove',
                          help="remove an item file from a document directory",
                          **shared)
    sub.add_argument('id', metavar='ID',
                     help="item ID to remove from its document")

    # Link subparser
    sub = subs.add_parser('link',
                          help="add a new link between two items",
                          **shared)
    sub.add_argument('child',
                     help="child item ID to link to the parent")
    sub.add_argument('parent',
                     help="parent item ID to link from the child")

    # Unlink subparser
    sub = subs.add_parser('unlink',
                          help="remove a link between two items",
                          **shared)
    sub.add_argument('child',
                     help="child item ID to unlink from parent")
    sub.add_argument('parent',
                     help="parent item ID child is linked to")

    # Edit subparser
    sub = subs.add_parser('edit',
                          help="open an existing item file for editing",
                          **shared)
    sub.add_argument('id', metavar='ID', help="item ID to open for editing")
    sub.add_argument('-t', '--tool', metavar='PROGRAM',
                     help="text editor to open the document item")

    # Import subparser
    sub = subs.add_parser('import',
                          help="import an existing document or item",
                          **shared)
    sub.add_argument('-d', '--document', nargs=2, metavar='ARG',
                     help="import an existing document by: PREFIX PATH")
    sub.add_argument('-i', '--item', nargs=2, metavar='ARG',
                     help="import an existing item by: PREFIX ID")
    sub.add_argument('-p', '--parent', metavar='PREFIX',
                     help="parent document prefix for imported document")
    sub.add_argument('-a', '--attrs', metavar='DICT',
                     help="dictionary of item attributes to import")

    # Publish subparser
    sub = subs.add_parser('publish',
                          help="publish a document as text or another format",
                          **shared)
    sub.add_argument('prefix', help="prefix of document to publish or 'all'")
    sub.add_argument('path', nargs='?',
                     help="path to published file or directory for 'all'")
    sub.add_argument('-t', '--text', action='store_true',
                     help="output text (default when no path)")
    sub.add_argument('-m', '--markdown', action='store_true',
                     help="output Markdown")
    sub.add_argument('-H', '--html', action='store_true',
                     help="output HTML (default for 'all')")
    sub.add_argument('-w', '--width', type=int,
                     help="limit line width on text output")
    sub.add_argument('-C', '--with-child-links', action='store_true',
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
        logging.debug("launching command '{}'...".format(args.command))
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
    if 'with_child_links' in args and args.with_child_links is not None:
        settings.PUBLISH_CHILD_LINKS = args.with_child_links


def _run(args, cwd, err):  # pylint: disable=W0613
    """Process arguments and run the `doorstop` subcommand.

    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param err: function to call for CLI errors

    """
    try:
        tree = build(cwd, root=args.project)
        tree.load()
        valid = tree.validate()
    except DoorstopError as error:
        logging.error(error)
        return False
    else:
        if tree and valid:
            print("valid tree: {}".format(tree))
        return valid


def _run_new(args, cwd, _):
    """Process arguments and run the `doorstop new` subcommand.

    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param err: function to call for CLI errors

    """
    try:
        tree = build(cwd, root=args.project)
        document = tree.new_document(args.path, args.prefix,
                                     parent=args.parent, digits=args.digits)
    except DoorstopError as error:
        logging.error(error)
        return False
    else:
        print("created document: {} ({})".format(document.prefix,
                                                 document.relpath))
        return True


def _run_add(args, cwd, _):
    """Process arguments and run the `doorstop add` subcommand.

    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param err: function to call for CLI errors

    """
    try:
        tree = build(cwd, root=args.project)
        item = tree.add_item(args.prefix, level=args.level)
    except DoorstopError as error:
        logging.error(error)
        return False
    else:
        print("added item: {} ({})".format(item.id, item.relpath))
        return True


def _run_remove(args, cwd, _):
    """Process arguments and run the `doorstop remove` subcommand.

    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param err: function to call for CLI errors

    """
    try:
        tree = build(cwd, root=args.project)
        item = tree.remove_item(args.id)
    except DoorstopError as error:
        logging.error(error)
        return False
    else:
        print("removed item: {} ({})".format(item.id, item.relpath))
        return True


def _run_link(args, cwd, _):
    """Process arguments and run the `doorstop link` subcommand.

    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param err: function to call for CLI errors

    """
    try:
        tree = build(cwd, root=args.project)
        child, parent = tree.link_items(args.child, args.parent)
    except DoorstopError as error:
        logging.error(error)
        return False
    else:
        print("linked items: {} ({}) -> {} ({})".format(child.id,
                                                        child.relpath,
                                                        parent.id,
                                                        parent.relpath))
        return True


def _run_unlink(args, cwd, _):
    """Process arguments and run the `doorstop unlink` subcommand.

    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param err: function to call for CLI errors

    """
    try:
        tree = build(cwd, root=args.project)
        child, parent = tree.unlink_items(args.child, args.parent)
    except DoorstopError as error:
        logging.error(error)
        return False
    else:
        print("unlinked items: {} ({}) -> {} ({})".format(child.id,
                                                          child.relpath,
                                                          parent.id,
                                                          parent.relpath))
        return True


def _run_edit(args, cwd, _):
    """Process arguments and run the `doorstop edit` subcommand.

    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param err: function to call for CLI errors

    """
    try:
        tree = build(cwd, root=args.project)
        item = tree.edit_item(args.id, tool=args.tool, launch=True)
    except DoorstopError as error:
        logging.error(error)
        return False
    else:
        print("opened item: {} ({})".format(item.id, item.relpath))
        return True


def _run_import(args, _, err):
    """Process arguments and run the `doorstop import` subcommand.

    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param err: function to call for CLI errors

    """
    document = item = None
    try:
        if args.document:
            prefix, path = args.document
            document = importer.new_document(prefix, path, parent=args.parent)
        elif args.item:
            prefix, identifier = args.item
            attrs = ast.literal_eval(args.attrs) if args.attrs else None
            item = importer.add_item(prefix, identifier, attrs=attrs)
        else:
            err("specify '--document' or '--item' to import")
    except DoorstopError as error:
        logging.error(error)
        return False
    else:
        if document:
            name = document.prefix
            relpath = document.relpath
        else:
            assert item
            name = item.id
            relpath = item.relpath
        print("imported: {} ({})".format(name, relpath))
        return True


def _run_publish(args, cwd, err):
    """Process arguments and run the `doorstop report` subcommand.

    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param err: function to call for CLI errors

    """
    publish_tree = args.prefix == 'all'
    try:
        tree = build(cwd, root=args.project)
        if publish_tree:
            documents = [document for document in tree]
        else:
            documents = [tree.find_document(args.prefix)]
    except DoorstopError as error:
        logging.error(error)
        return False
    else:

        # Set base arguments
        kwargs = {'ignored': tree.vcs.ignored}
        if args.width:
            kwargs['width'] = args.width

        # Set file extension
        if args.path:
            if publish_tree:
                ext = '.html'
            else:
                ext = os.path.splitext(args.path)[-1]
        if args.text:
            ext = '.txt'
        elif args.markdown:
            ext = '.md'
        elif args.html:
            ext = '.html'
        elif not args.path:
            ext = '.txt'

        # Publish documents
        if args.path:
            if publish_tree:
                print("publishing tree to {}...".format(args.path))
                for document in documents:
                    path = os.path.join(args.path, document.prefix + ext)
                    print("publishing {} to {}...".format(document, path))
                    report.publish(document, path, ext, **kwargs)
                if ext == '.html':
                    report.index(args.path)
            else:
                print("publishing {} to {}...".format(documents[0], args.path))
                report.publish(documents[0], args.path, ext, **kwargs)
        else:
            if publish_tree:
                err("only single documents can be displayed")
            for line in report.lines(documents[0], ext, **kwargs):
                print(line)

        return True


if __name__ == '__main__':  # pragma: no cover, manual test
    main()
