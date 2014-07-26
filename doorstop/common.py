"""Common exceptions, classes, and functions for Doorstop."""

import os
import shutil
import argparse
import logging

import yaml

VERBOSITY = 0  # global verbosity setting for controlling string formatting
STR_VERBOSITY = 4
MAX_VERBOSITY = 4


class DoorstopError(Exception):

    """Generic Doorstop error."""


class DoorstopWarning(DoorstopError, Warning):

    """Generic Doorstop warning."""


class DoorstopInfo(DoorstopError, Warning):

    """Generic Doorstop info."""


class HelpFormatter(argparse.HelpFormatter):

    """Command-line help text formatter with wider help text."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, max_help_position=40, **kwargs)


class WarningFormatter(logging.Formatter, object):

    """Logging formatter that displays verbose formatting for WARNING+."""

    def __init__(self, default_format, verbose_format, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_format = default_format
        self.verbose_format = verbose_format

    def format(self, record):  # pragma: no cover (manual test)
        """Python 3 hack to change the formatting style dynamically."""
        if record.levelno > logging.INFO:
            self._style._fmt = self.verbose_format  # pylint: disable=W0212
        else:
            self._style._fmt = self.default_format  # pylint: disable=W0212
        return super().format(record)


def create_dirname(path):
    """Ensure a parent directory exists for a path."""
    dirpath = os.path.dirname(path)
    if dirpath and not os.path.isdir(dirpath):
        logging.info("creating directory {}...".format(dirpath))
        os.makedirs(dirpath)


def read_text(path, encoding='utf-8'):
    """Read text from a file.

    :param path: file path to read from
    :param encoding: input file encoding

    :return: string

    """
    logging.debug("reading text from '{}'...".format(path))
    with open(path, 'r', encoding=encoding) as stream:
        text = stream.read()
    return text


def load_yaml(text, path):
    """Parse a dictionary from YAML text.

    :param text: string containing dumped YAML data
    :param path: file path for error messages

    :return: dictionary

    """
    # Load the YAML data
    try:
        data = yaml.load(text) or {}
    except yaml.error.YAMLError as exc:  # pylint: disable=E1101
        msg = "invalid contents: {}:\n{}".format(path, exc)
        raise DoorstopError(msg) from None
    # Ensure data is a dictionary
    if not isinstance(data, dict):
        msg = "invalid contents: {}".format(path)
        raise DoorstopError(msg)
    # Return the parsed data
    return data


def write_lines(lines, path, end='\n', encoding='utf-8'):
    """Write lines of text to a file.

    :param lines: iterator of strings
    :param path: file to write lines
    :param end: string to end lines
    :param encoding: output file encoding

    :return: path of new file

    """
    logging.debug("writing lines to '{}'...".format(path))
    with open(path, 'wb') as stream:
        for line in lines:
            data = (line + end).encode(encoding)
            stream.write(data)
    return path


def write_text(text, path, encoding='utf-8'):
    """Write text to a file.

    :param text: string
    :param path: file to write text
    :param encoding: output file encoding

    :return: path of new file

    """
    if text:
        logging.debug("writing text to '{}'...".format(path))
    with open(path, 'wb') as stream:
        data = text.encode(encoding)
        stream.write(data)
    return path


def touch(path):  # pragma: no cover (integration test)
    """Ensure a file exists."""
    if not os.path.exists(path):
        logging.debug("creating empty '{}'...".format(path))
        write_text('', path)


def delete(path):  # pragma: no cover (integration test)
    """Delete a file or directory with error handling."""
    if os.path.isdir(path):
        try:
            logging.debug("deleting '{}'...".format(path))
            shutil.rmtree(path)
        except IOError:
            # bug: http://code.activestate.com/lists/python-list/159050
            msg = "unable to delete: {}".format(path)
            logging.warning(msg)
    elif os.path.isfile(path):
        logging.debug("deleting '{}'...".format(path))
        os.remove(path)
