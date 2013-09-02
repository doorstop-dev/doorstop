#!/usr/bin/env python

"""
Command-line interface for Doorstop.
"""

import sys
import argparse
import logging

from doorstop import CLI, VERSION
from doorstop import settings
from doorstop import processor


def main():  # pragma: no cover, integration test
    """Process command-line arguments and run the program.
    """
    # Main parser
    parser = argparse.ArgumentParser(prog=CLI, description=__doc__)
    parser.add_argument('-V', '--version', action='version', version=VERSION)
    parser.add_argument('-v', '--verbose', action='count', help="enable verbose logging")
    parser.add_argument('-d', '--daemon', action='store_true', help="keep the process running")
    subparsers = parser.add_subparsers()

    # Init subparser
    init_parser = subparsers.add_parser('init', help="initialize a new Doorstop project")

    # Add subparser
    add_parser = subparsers.add_parser('add', help="add a new requirement or link")

    # Remove subparser
    remove_parser = subparsers.add_parser('remove', help="remove an existing requirement or link")

    # Import subparser
    import_parser = subparsers.add_parser('import', help="import requirements from anther format")

    # Export subparser
    export_parser = subparsers.add_parser('export', help="export requirements to another format")

    # Report subparser
    report_parser = subparsers.add_parser('report', help="publish the requirements to a report")

    # Parse arguments
    args = parser.parse_args()

    # Run the program
    success = False
    try:
        success = run()
    except KeyboardInterrupt:  # pylint: disable=W0703
        logging.debug("cancelled manually")
    if not success:
        sys.exit(1)


def run():

    return False


def configure_logging(verbosity=0):  # pragma: no cover, integration test
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


if __name__ == '__main__':
    main()
