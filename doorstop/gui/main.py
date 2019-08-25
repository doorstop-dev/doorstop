#!/usr/bin/env python
# SPDX-License-Identifier: LGPL-3.0-only
# type: ignore

"""Graphical interface for Doorstop."""

import argparse
import functools
import logging
import os
import sys
from unittest.mock import Mock

from doorstop import common, settings
from doorstop.common import HelpFormatter, WarningFormatter
from doorstop.gui import application, widget

try:
    import tkinter as tk
    from tkinter import ttk
except ImportError as _exc:
    sys.stderr.write("WARNING: {}\n".format(_exc))
    tk = Mock()
    ttk = Mock()


log = common.logger(__name__)


def main(args=None):
    """Process command-line arguments and run the program."""
    from doorstop import GUI, VERSION

    # Shared options
    debug = argparse.ArgumentParser(add_help=False)
    debug.add_argument('-V', '--version', action='version', version=VERSION)
    debug.add_argument(
        '-v', '--verbose', action='count', default=0, help="enable verbose logging"
    )
    shared = {'formatter_class': HelpFormatter, 'parents': [debug]}
    parser = argparse.ArgumentParser(prog=GUI, description=__doc__, **shared)

    # Build main parser
    parser.add_argument(
        '-j', '--project', metavar="PATH", help="path to the root of the project"
    )

    # Parse arguments
    args = parser.parse_args(args=args)

    # Configure logging
    _configure_logging(args.verbose)

    # Run the program
    try:
        success = run(args, os.getcwd(), parser.error)
    except KeyboardInterrupt:
        log.debug("program interrupted")
        success = False
    if success:
        log.debug("program exited")
        return 0
    else:
        log.debug("program exited with error")
        return 1


def _configure_logging(verbosity=0):
    """Configure logging using the provided verbosity level (0+)."""
    # Configure the logging level and format
    if verbosity == 0:
        level = settings.VERBOSE_LOGGING_LEVEL
        default_format = settings.VERBOSE_LOGGING_FORMAT
        verbose_format = settings.VERBOSE_LOGGING_FORMAT
    elif verbosity == 1:
        level = settings.VERBOSE2_LOGGING_LEVEL
        default_format = settings.VERBOSE_LOGGING_FORMAT
        verbose_format = settings.VERBOSE_LOGGING_FORMAT
    else:
        level = settings.VERBOSE2_LOGGING_LEVEL
        default_format = settings.TIMED_LOGGING_FORMAT
        verbose_format = settings.TIMED_LOGGING_FORMAT

    # Set a custom formatter
    logging.basicConfig(level=level)
    formatter = WarningFormatter(default_format, verbose_format)
    logging.root.handlers[0].setFormatter(formatter)


def run(args, cwd, error):
    """Start the GUI.

    :param args: Namespace of CLI arguments (from this module or the CLI)
    :param cwd: current working directory
    :param error: function to call for CLI errors

    """
    from doorstop import __project__, __version__

    # Exit if tkinter is not available
    if isinstance(tk, Mock) or isinstance(ttk, Mock):
        return error("tkinter is not available")

    else:

        root = widget.Tk()
        root.title("{} ({})".format(__project__, __version__))

        from sys import platform as _platform

        # Load the icon
        if _platform in ("linux", "linux2"):
            # Linux
            from doorstop.gui import resources

            root.tk.call(
                # pylint: disable=protected-access
                'wm',
                'iconphoto',
                root._w,
                tk.PhotoImage(data=resources.b64_doorstopicon_png),
            )
        elif _platform == "darwin":
            # macOS
            pass  # TODO
        elif _platform in ("win32", "win64"):
            # Windows
            from doorstop.gui import resources
            import base64
            import tempfile

            try:
                with tempfile.TemporaryFile(
                    mode='w+b', suffix=".ico", delete=False
                ) as theTempIconFile:
                    theTempIconFile.write(
                        base64.b64decode(resources.b64_doorstopicon_ico)
                    )
                    theTempIconFile.flush()
                root.iconbitmap(theTempIconFile.name)
            finally:
                try:
                    os.unlink(theTempIconFile.name)
                except Exception:  # pylint: disable=W0703
                    pass

        app = application.Application(root, cwd, args.project)

        root.update()
        root.minsize(root.winfo_width(), root.winfo_height())
        app.mainloop()

        return True


def _log(func):
    """Log name and arguments."""

    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        sargs = "{}, {}".format(
            ', '.join(repr(a) for a in args),
            ', '.join("{}={}".format(k, repr(v)) for k, v in kwargs.items()),
        )
        msg = "log: {}: {}".format(func.__name__, sargs.strip(", "))
        if not isinstance(self, ttk.Frame) or not self.ignore:
            log.debug(msg.strip())
        return func(self, *args, **kwargs)

    return wrapped


if __name__ == '__main__':
    sys.exit(main())
