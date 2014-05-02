"""Common exceptions, classes, and functions for Doorstop."""

import argparse
import logging

VERBOSITY = 0  # global verbosity setting for controlling string formatting
STR_VERBOSITY = 3
MAX_VERBOSITY = 4

_tree = None  # implicit tree for convenience functions, pylint:disable=C0103


def get_tree():
    """Get a shared tree for convenience functions."""
    global _tree  # pylint: disable=W0603,C0103
    if _tree is None:
        from doorstop import build
        _tree = build()
    return _tree


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

    def format(self, record):  # pragma: no cover, manual test
        """Python 3 hack to change the formatting style dynamically."""
        if record.levelno > logging.INFO:
            self._style._fmt = self.verbose_format  # pylint: disable=W0212
        else:
            self._style._fmt = self.default_format  # pylint: disable=W0212
        return super().format(record)
