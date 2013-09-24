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
        if record.levelno > logging.INFO:
            self._fmt = self.verbose_format
        else:
            self._fmt = self.default_format
        return super().format(record)


def main(args=None):
    """Process command-line arguments and run the program.
    """
    # Main parser
    parser = argparse.ArgumentParser(prog=CLI, description=__doc__,
                                     formatter_class=_HelpFormatter)
    parser.add_argument('-g', '--gui', action='store_true',
                        help="launch the GUI")
    parser.add_argument('-V', '--version', action='version', version=VERSION)
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help="enable verbose logging")
    subs = parser.add_subparsers(help="", dest='command', metavar="<command>")

    # New subparser
    sub = subs.add_parser('new', formatter_class=_HelpFormatter,
                          help="create a new document directory")
    sub.add_argument('-r', '--root', help="root directory for document items")
    sub.add_argument('-p', '--prefix', help="prefix for item IDs")
    sub.add_argument('-d', '--digits', help="number of digits in item IDs")

    # Add subparser
    sub = subs.add_parser('add', formatter_class=_HelpFormatter,
                          help="add a new item or link to a document")
    sub.add_argument('-i', '--item', action='store_true',
                     help="add a new item")
    sub.add_argument('-l', '--link', nargs=2, metavar='ID',
                     help="add a new link between items")

    # Remove subparser
    sub = subs.add_parser('remove', formatter_class=_HelpFormatter,
                          help="remove an item or link from a document")
    sub.add_argument('-i', '--item', help="remove an existing item")
    sub.add_argument('-l', '--link', nargs=2, metavar='ID',
                     help="remove an existing link between items")

    # Import subparser
    sub = subs.add_parser('import', formatter_class=_HelpFormatter,
                          help="import document items from another format")
    sub.add_argument('input', help="file to import")

    # Export subparser
    sub = subs.add_parser('export', formatter_class=_HelpFormatter,
                          help="export document items to another format")
    sub.add_argument('output', help="file to export")

    # Report subparser
    sub = subs.add_parser('report', formatter_class=_HelpFormatter,
                          help="publish document items to a report")
    sub.add_argument('report', help="report to create")

    # Parse arguments
    args = parser.parse_args(args=args)

    # Configure logging
    _configure_logging(args.verbose)

    # Run the program
    if args.command:
        function = globals()['_run_' + args.command]
    else:
        function = _run
    try:
        success = function(args, os.getcwd(), parser.error)
    except KeyboardInterrupt:  # pragma: no cover, manual test
        logging.debug("cancelled manually")
        success = False
    if not success:
        sys.exit(1)


def _configure_logging(verbosity=0):
    """Configure logging using the provided verbosity level (0+)."""

    # Configure the logging level and format
    if verbosity >= 1:
        level = settings.VERBOSE_LOGGING_LEVEL
        if verbosity >= 3:
            default_format = verbose_format = settings.VERBOSE3_LOGGING_FORMAT
        elif verbosity >= 2:
            default_format = verbose_format = settings.VERBOSE2_LOGGING_FORMAT
        else:
            default_format = verbose_format = settings.VERBOSE_LOGGING_FORMAT
    else:
        level = settings.DEFAULT_LOGGING_LEVEL
        default_format = settings.DEFAULT_LOGGING_FORMAT
        verbose_format = settings.VERBOSE_LOGGING_FORMAT

    # Set a custom formatter
    logging.basicConfig(level=level)
    formatter = _WarningFormatter(default_format, verbose_format)
    logging.root.handlers[0].setFormatter(formatter)


def _run(args, cwd, error):
    """Process arguments and run the `doorstop` subcommand.
    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param error: function to call for CLI errors
    """
    raise NotImplementedError((args, cwd, error))


def _run_new(args, cwd, error):
    """Process arguments and run the `doorstop new` subcommand.
    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param error: function to call for CLI errors
    """
    raise NotImplementedError((args, cwd, error))


def _run_add(args, cwd, error):
    """Process arguments and run the `doorstop add` subcommand.
    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param error: function to call for CLI errors
    """
    raise NotImplementedError((args, cwd, error))


def _run_remove(args, cwd, error):
    """Process arguments and run the `doorstop remove` subcommand.
    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param error: function to call for CLI errors
    """
    raise NotImplementedError((args, cwd, error))


def _run_import(args, cwd, error):
    """Process arguments and run the `doorstop import` subcommand.
    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param error: function to call for CLI errors
    """
    raise NotImplementedError((args, cwd, error))


def _run_export(args, cwd, error):
    """Process arguments and run the `doorstop export` subcommand.
    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param error: function to call for CLI errors
    """
    raise NotImplementedError((args, cwd, error))


def _run_report(args, cwd, error):
    """Process arguments and run the `doorstop report` subcommand.
    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param error: function to call for CLI errors
    """
    raise NotImplementedError((args, cwd, error))


if __name__ == '__main__':  # pragma: no cover, manual test
    main()
