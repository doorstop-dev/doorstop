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


def main():
    """Process command-line arguments and run the program.
    """
    # Main parser
    parser = argparse.ArgumentParser(prog=CLI, description=__doc__)
    parser.add_argument('-g', '--gui', action='store_true', help="launch the GUI")
    parser.add_argument('-V', '--version', action='version', version=VERSION)
    parser.add_argument('-v', '--verbose', action='count', help="enable verbose logging")
    subparsers = parser.add_subparsers(help="", dest='command', metavar="<command>")

    # Init subparser
    init_parser = subparsers.add_parser('init', help="initialize a new document")
    init_parser.add_argument('-r', '--root', help="root directory for document items")
    init_parser.add_argument('-p', '--prefix', help="prefix for item IDs")
    init_parser.add_argument('-d', '--digits', help="number of digits in item IDs")

    # Add subparser
    add_parser = subparsers.add_parser('add', help="add a new requirement or link")
    add_parser.add_argument('-i', '--item', action='store_true', help="add a new item")
    add_parser.add_argument('-l', '--link', nargs=2, help="add a new link between items")

    # Remove subparser
    remove_parser = subparsers.add_parser('remove', help="remove an existing requirement or link")
    remove_parser.add_parser('-i', '--item', help="remove an existing requirement")
    remove_parser.add_parser('-l', '--link', nargs=2, help="remove an existing link")

    # Import subparser
    import_parser = subparsers.add_parser('import', help="import requirements from anther format")
    import_parser.add_parser('input', help="file to import")

    # Export subparser
    export_parser = subparsers.add_parser('export', help="export requirements to another format")
    export_parser.add_parser('output', help="file to export")

    # Report subparser
    report_parser = subparsers.add_parser('report', help="publish the requirements to a report")
    report_parser.add_parser('report', help="report to create")

    # Parse arguments
    args = parser.parse_args()

    # Configure logging
    _configure_logging(args.verbose)

    # Run the program
    success = False
    if args.command:
        function = globals()['_run_' + args.command]
    else:
        function = _run
    try:
        success = function(args, os.getcwd(), parser.error)
    except KeyboardInterrupt:  # pylint: disable=W0703
        logging.debug("cancelled manually")
    if not success:
        sys.exit(1)


def _configure_logging(verbosity=0):
    """Configure logging using the provided verbosity level (0+)."""

    class WarningFormatter(logging.Formatter, object):
        """Always displays the verbose logging format for warnings or higher."""

        def __init__(self, default_format, verbose_format, *args, **kwargs):
            super(WarningFormatter, self).__init__(*args, **kwargs)
            self.default_format = default_format
            self.verbose_format = verbose_format

        def format(self, record):
            if record.levelno > logging.INFO or logging.root.getEffectiveLevel() < logging.INFO:
                self._fmt = self.verbose_format
            else:
                self._fmt = self.default_format
            return super(WarningFormatter, self).format(record)

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
    logging.root.handlers[0].setFormatter(WarningFormatter(default_format, verbose_format))


def _run(args, cwd, error):
    """Process arguments and run the `doorstop` subcommand.
    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param error: function to call for CLI errors
    """
    return True


def _run_init(args, cwd, error):
    """Process arguments and run the `doorstop init` subcommand.
    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param error: function to call for CLI errors
    """
    return True


def _run_add(args, cwd, error):
    """Process arguments and run the `doorstop add` subcommand.
    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param error: function to call for CLI errors
    """
    return True


def _run_remove(args, cwd, error):
    """Process arguments and run the `doorstop remove` subcommand.
    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param error: function to call for CLI errors
    """
    return True


def _run_import(args, cwd, error):
    """Process arguments and run the `doorstop import` subcommand.
    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param error: function to call for CLI errors
    """
    return True


def _run_export(args, cwd, error):
    """Process arguments and run the `doorstop export` subcommand.
    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param error: function to call for CLI errors
    """
    return True


def _run_report(args, cwd, error):
    """Process arguments and run the `doorstop report` subcommand.
    @param args: Namespace of CLI arguments
    @param cwd: current working directory
    @param error: function to call for CLI errors
    """
    return True


if __name__ == '__main__':  # pragma: no cover, manual test
    main()
