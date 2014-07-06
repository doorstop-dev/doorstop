"""Shared command-line functions."""

import os
import ast
import logging

from doorstop import common
from doorstop import settings


def configure_logging(verbosity=0):
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
    formatter = common.WarningFormatter(default_format, verbose_format)
    logging.root.handlers[0].setFormatter(formatter)

    # Warn about excessive verbosity
    if verbosity > common.MAX_VERBOSITY:
        msg = "maximum verbosity level is {}".format(common.MAX_VERBOSITY)
        logging.warn(msg)
        common.VERBOSITY = common.MAX_VERBOSITY
    else:
        common.VERBOSITY = verbosity


def configure_settings(args):
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


def literal_eval(literal, err, default=None):
    """Convert an literal to its value.

    :param literal: string to evaulate
    :param err: function to call for errors
    :param default: default value for empty inputs
    :return: Python literal

    """
    try:
        return ast.literal_eval(literal) if literal else default
    except (SyntaxError, ValueError):
        err("invalid Python literal: {}".format(literal))


def get_ext(args, ext_stdout, ext_file, whole_tree, err):
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


def ask(question, default=None):
    """Display a console yes/no prompt.

    :param question: text of yes/no question ending in '?'
    :param default: 'yes', 'no', or None (for no default)

    :return: True = 'yes', False = 'no'

    """
    valid = {"yes": True,
             "y": True,
             "no": False,
             "n": False}

    if default == 'yes':
        prompt = " [Y/n] "
    elif default == 'no':
        prompt = " [y/N] "
    else:
        prompt = " [y/n] "

    while True:
        try:
            choice = input(question + prompt).lower().strip() or default
        except KeyboardInterrupt as exc:
            print()
            raise exc from None
        try:
            return valid[choice]
        except KeyError:
            options = ', '.join(sorted(valid.keys()))
            print("valid responses: {}".format(options))
