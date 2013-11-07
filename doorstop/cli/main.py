#!/usr/bin/env python

"""
Command-line interface for Doorstop.
"""

import os
import sys
import argparse
import logging

from doorstop import CLI, VERSION
from doorstop.cli import settings
from doorstop.core import processor
from doorstop.common import DoorstopError


class _HelpFormatter(argparse.HelpFormatter):
    """Command-line help text formatter with wider help text."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, max_help_position=32, **kwargs)


class _WarningFormatter(logging.Formatter, object):
    """Logging formatter that always displays a verbose logging
    format for logging level WARNING or higher."""

    def __init__(self, default_format, verbose_format, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_format = default_format
        self.verbose_format = verbose_format

    def format(self, record):
        """Python 3 hack to change the formatting style dynamically."""
        if record.levelno > logging.INFO:
            self._style._fmt = self.verbose_format  # pylint: disable=W0212
        else:
            self._style._fmt = self.default_format  # pylint: disable=W0212
        return super().format(record)


def main(args=None):
    """Process command-line arguments and run the program.
    """
    # Shared options
    debug = argparse.ArgumentParser(add_help=False)
    debug.add_argument('-V', '--version', action='version', version=VERSION)
    debug.add_argument('-v', '--verbose', action='count', default=0,
                       help="enable verbose logging")
    shared = {'formatter_class': _HelpFormatter, 'parents': [debug]}

    # Main parser
    parser = argparse.ArgumentParser(prog=CLI, description=__doc__, **shared)
    parser.add_argument('-g', '--gui', action='store_true',
                        help="launch the GUI")
    subs = parser.add_subparsers(help="", dest='command', metavar="<command>")

    # New subparser
    sub = subs.add_parser('new',
                          help="create a new document directory",
                          **shared)
    sub.add_argument('prefix', help="prefix for item IDs")
    sub.add_argument('root', help="path to directory for document items")
    sub.add_argument('-p', '--parent', help="prefix for parent item IDS")
    sub.add_argument('-d', '--digits', help="number of digits in item IDs")

    # Add subparser
    sub = subs.add_parser('add',
                          help="add a new item to a document",
                          **shared)
    sub.add_argument('prefix',
                     help="prefix of document for the new item")

    # Remove subparser
    sub = subs.add_parser('remove',
                          help="remove an item from a document",
                          **shared)
    sub.add_argument('id', metavar='ID',
                     help="item ID to remove from a document")

    # Link subparser
    sub = subs.add_parser('link',
                          help="add a new link between two document items",
                          **shared)
    sub.add_argument('child',
                     help="child item ID to link to the parent")
    sub.add_argument('parent',
                     help="parent item ID to link from the child")

    # Unlink subparser
    sub = subs.add_parser('unlink',
                          help="remove a link between two document items",
                          **shared)
    sub.add_argument('child',
                     help="child item ID to unlink from parent")
    sub.add_argument('parent',
                     help="parent item ID child is linked to")

    # Edit subparser
    sub = subs.add_parser('edit',
                          help="edit an existing document item",
                          **shared)
    sub.add_argument('id', metavar='ID', help="item to edit")
    sub.add_argument('-t', '--tool', metavar='PROGRAM',
                     help="text editor to open the document item")

    # Import subparser
    sub = subs.add_parser('import',
                          help="import document items from another format",
                          **shared)
    sub.add_argument('input', help="file to import")

    # Export subparser
    sub = subs.add_parser('export',
                          help="export document items to another format",
                          **shared)
    sub.add_argument('output', help="file to export")

    # Report subparser
    sub = subs.add_parser('report',
                          help="publish document items to a report",
                          **shared)
    sub.add_argument('report', help="report to create")

    # Parse arguments
    args = parser.parse_args(args=args)

    # Configure logging
    _configure_logging(args.verbose)

    # Run the program
    if args.command:
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
        logging.debug("command succedded")
    else:
        logging.debug("command failed")
        sys.exit(1)


def _configure_logging(verbosity=0):
    """Configure logging using the provided verbosity level (0+)."""

    # Configure the logging level and format
    if verbosity == 0:
        level = settings.DEFAULT_LOGGING_LEVEL
        default_format = settings.DEFAULT_LOGGING_FORMAT
        verbose_format = settings.VERBOSE_LOGGING_FORMAT
    elif verbosity == 1:
        level = settings.VERBOSE_LOGGING_LEVEL
        default_format = verbose_format = settings.VERBOSE_LOGGING_FORMAT
    elif verbosity == 2:
        level = settings.VERBOSE2_LOGGING_LEVEL
        default_format = verbose_format = settings.VERBOSE_LOGGING_FORMAT
    else:
        level = settings.VERBOSE2_LOGGING_LEVEL
        default_format = verbose_format = settings.VERBOSE2_LOGGING_FORMAT

    # Set a custom formatter
    logging.basicConfig(level=level)
    formatter = _WarningFormatter(default_format, verbose_format)
    logging.root.handlers[0].setFormatter(formatter)


def _run(args, cwd, err):  # pylint: disable=W0613
    """Process arguments and run the `doorstop` subcommand.
    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param err: function to call for CLI errors
    """
    try:
        tree = processor.build(cwd)
        tree.check()
    except DoorstopError as error:
        logging.error(error)
        return False
    else:
        return True


def _run_new(args, cwd, _):
    """Process arguments and run the `doorstop new` subcommand.
    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param err: function to call for CLI errors
    """
    try:
        tree = processor.build(cwd)
        document = tree.new(args.root, args.prefix,
                            parent=args.parent, digits=args.digits)
        print("created: {}".format(document))
    except DoorstopError as error:
        logging.error(error)
        return False
    else:
        return True


def _run_add(args, cwd, _):
    """Process arguments and run the `doorstop add` subcommand.
    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param err: function to call for CLI errors
    """
    try:
        tree = processor.build(cwd)
        item = tree.add(args.prefix)
    except DoorstopError as error:
        logging.error(error)
        return False
    else:
        print("added: {}".format(item))
        return True


def _run_remove(args, cwd, _):
    """Process arguments and run the `doorstop remove` subcommand.
    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param err: function to call for CLI errors
    """
    try:
        tree = processor.build(cwd)
        item = tree.remove(args.id)
    except DoorstopError as error:
        logging.error(error)
        return False
    else:
        print("removed: {}".format(item))
        return True


def _run_link(args, cwd, _):
    """Process arguments and run the `doorstop link` subcommand.
    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param err: function to call for CLI errors
    """
    try:
        tree = processor.build(cwd)
        child, parent = tree.link(args.child, args.parent)
    except DoorstopError as error:
        logging.error(error)
        return False
    else:
        print("linked: {} -> {}".format(child, parent))
        return True


def _run_unlink(args, cwd, _):
    """Process arguments and run the `doorstop unlink` subcommand.
    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param err: function to call for CLI errors
    """
    try:
        tree = processor.build(cwd)
        child, parent = tree.unlink(args.child, args.parent)
    except DoorstopError as error:
        logging.error(error)
        return False
    else:
        print("unlinked: {} -> {}".format(child, parent))
        return True


def _run_edit(args, cwd, _):
    """Process arguments and run the `doorstop edit` subcommand.
    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param err: function to call for CLI errors
    """
    try:
        tree = processor.build(cwd)
        item = tree.edit(args.id, tool=args.tool, launch=True)
    except DoorstopError as error:
        logging.error(error)
        return False
    else:
        print("opened: {}".format(item))
        return True


def _run_import(args, cwd, err):
    """Process arguments and run the `doorstop import` subcommand.
    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param err: function to call for CLI errors
    """
    logging.warning((args, cwd, err))
    raise NotImplementedError("'doorstop import' not implemented")


def _run_export(args, cwd, err):
    """Process arguments and run the `doorstop export` subcommand.
    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param err: function to call for CLI errors
    """
    logging.warning((args, cwd, err))
    raise NotImplementedError("'doorstop export' not implemented")


def _run_report(args, cwd, err):
    """Process arguments and run the `doorstop report` subcommand.
    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param err: function to call for CLI errors
    """
    logging.warning((args, cwd, err))
    raise NotImplementedError("'doorstop report' not implemented")


if __name__ == '__main__':  # pragma: no cover, manual test
    main()
