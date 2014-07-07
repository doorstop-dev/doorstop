#!/usr/bin/env python

"""Command-line interface for Doorstop."""

import os
import sys
import argparse
import logging

from doorstop.cli import utilities, commands
from doorstop.gui.main import _run as gui
from doorstop import common


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
    shared = {'formatter_class': common.HelpFormatter, 'parents': [debug]}

    # Build main parser
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

    # Build sub-parsers
    subs = parser.add_subparsers(help="", dest='command', metavar="<command>")
    _create(subs, shared)
    _delete(subs, shared)
    _add(subs, shared)
    _remove(subs, shared)
    _link(subs, shared)
    _unlink(subs, shared)
    _edit(subs, shared)
    _import(subs, shared)
    _export(subs, shared)
    _publish(subs, shared)

    # Parse arguments
    args = parser.parse_args(args=args)

    # Configure logging
    utilities.configure_logging(args.verbose)

    # Configure settings
    utilities.configure_settings(args)

    # Run the program
    if args.gui:
        logging.debug("launching GUI...")
        function = gui
    else:
        function = commands.get(args.command)
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


def _create(subs, shared):
    """Configure the `doorstop create` subparser."""
    info = "create a new document directory"
    sub = subs.add_parser('create', description=info.capitalize() + '.',
                          help=info, **shared)
    sub.add_argument('prefix', help="document prefix for new item IDs")
    sub.add_argument('path', help="path to a directory for item files")
    sub.add_argument('-p', '--parent', help="prefix for parent item IDS")
    sub.add_argument('-d', '--digits', help="number of digits in item IDs")


def _delete(subs, shared):
    """Configure the `doorstop delete` subparser."""
    info = "delete a document directory"
    sub = subs.add_parser('delete', description=info.capitalize() + '.',
                          help=info, **shared)
    sub.add_argument('prefix', help="prefix of document to delete")


def _add(subs, shared):
    """Configure the `doorstop add` subparser."""
    info = "create an item file in a document directory"
    sub = subs.add_parser('add', description=info.capitalize() + '.',
                          help=info, **shared)
    sub.add_argument('prefix',
                     help="document prefix for the new item")
    sub.add_argument('-l', '--level', help="desired item level (e.g. 1.2.3)")


def _remove(subs, shared):
    """Configure the `doorstop remove` subparser."""
    info = "remove an item file from a document directory"
    sub = subs.add_parser('remove', description=info.capitalize() + '.',
                          help=info, **shared)
    sub.add_argument('id', metavar='ID',
                     help="item ID to remove from its document")


def _link(subs, shared):
    """Configure the `doorstop link` subparser."""
    info = "add a new link between two items"
    sub = subs.add_parser('link', description=info.capitalize() + '.',
                          help=info, **shared)
    sub.add_argument('child',
                     help="child item ID to link to the parent")
    sub.add_argument('parent',
                     help="parent item ID to link from the child")


def _unlink(subs, shared):
    """Configure the `doorstop unlink` subparser."""
    info = "remove a link between two items"
    sub = subs.add_parser('unlink', description=info.capitalize() + '.',
                          help=info, **shared)
    sub.add_argument('child',
                     help="child item ID to unlink from parent")
    sub.add_argument('parent',
                     help="parent item ID child is linked to")


def _edit(subs, shared):
    """Configure the `doorstop edit` subparser."""
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


def _import(subs, shared):
    """Configure the `doorstop import` subparser."""
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


def _export(subs, shared):
    """Configure the `doorstop export` subparser."""
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


def _publish(subs, shared):
    """Configure the `doorstop publish` subparser."""
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
                     help="do not include child links in published documents")


if __name__ == '__main__':  # pragma: no cover (manual test)
    main()
