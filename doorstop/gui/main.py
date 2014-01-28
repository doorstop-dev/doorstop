#!/usr/bin/env python

"""
Graphical interface for Doorstop.
"""

import sys
from unittest.mock import Mock, MagicMock
try:  # pragma: no cover - not measurable
    import tkinter as tk
    from tkinter import ttk
    from tkinter import messagebox, simpledialog, filedialog
except ImportError as err:  # pragma: no cover - not measurable
    sys.stderr.write("WARNING: {}\n".format(err))
    tk = Mock()  # pylint: disable=C0103
    ttk = Mock()  # pylint: disable=C0103
import os
import argparse
from itertools import chain
import logging


from doorstop import GUI, __project__, __version__
from doorstop.common import SHARED, WarningFormatter
from doorstop import settings


class Application(ttk.Frame):  # pragma: no cover - manual test
    """Tkinter application for Doorstop."""

    def __init__(self, master=None, root=None, name=None):
        ttk.Frame.__init__(self, master)

        # Load the root sharing directory
        self.root = root or MagicMock()

        # Load the user
        self.user = MagicMock()
        try:
            self.user = self.user or MagicMock()
        except EnvironmentError:

            while True:

                msg = "Enter your name in the form 'FirstLast':"
                text = simpledialog.askstring("Create a User", msg)
                logging.debug("text: {}".format(repr(text)))
                name = text.strip(" '") if text else None
                if not name:
                    raise KeyboardInterrupt("no user specified")
                try:
                    self.user = MagicMock()
                except EnvironmentError:
                    existing = MagicMock()
                    msg = "Is this you:"
                    for info in existing.info:
                        msg += "\n\n'{}' on '{}'".format(info[1], info[0])
                    if not existing.info or \
                            messagebox.askyesno("Add to Existing User", msg):
                        self.user = MagicMock()
                        break
                else:
                    break

        # Create variables
        self.path_downloads = tk.StringVar(value=self.user.path_downloads)
        self.outgoing = []
        self.incoming = []

        # Initialize the GUI
        self.listbox_outgoing = None
        self.listbox_incoming = None
        self.init(master)

        # Show the GUI
        master.deiconify()
        self.update()

    def init(self, master):  # pylint: disable=R0914
        """Initialize frames and widgets."""  # pylint: disable=C0301

        sticky = {'sticky': tk.NSEW}
        pad = {'padx': 5, 'pady': 5}
        stickypad = dict(chain(sticky.items(), pad.items()))

        # Configure grid
        master.rowconfigure(0, weight=0)
        master.rowconfigure(2, weight=1)
        master.rowconfigure(4, weight=1)
        master.columnconfigure(0, weight=1)

        # Create widgets
        def frame_settings(master):
            """Frame for the settings."""
            frame = ttk.Frame(master)

            # Configure grid
            frame.rowconfigure(0, weight=1)
            frame.columnconfigure(0, weight=0)
            frame.columnconfigure(1, weight=1)
            frame.columnconfigure(2, weight=0)

            # Place widgets
            ttk.Label(frame, text="Downloads:").grid(row=0, column=0, **pad)
            ttk.Entry(frame, state='readonly', textvariable=self.path_downloads).grid(row=0, column=1, **stickypad)
            ttk.Button(frame, text="...", width=0, command=self.browse_downloads).grid(row=0, column=2, ipadx=5, **pad)

            return frame

        def frame_incoming(master):
            """Frame for incoming songs."""
            frame = ttk.Frame(master)

            # Configure grid
            frame.rowconfigure(0, weight=1)
            frame.rowconfigure(1, weight=0)
            frame.columnconfigure(0, weight=0)
            frame.columnconfigure(1, weight=1)
            frame.columnconfigure(2, weight=1)

            # Place widgets
            self.listbox_incoming = tk.Listbox(frame, selectmode=tk.EXTENDED)
            self.listbox_incoming.grid(row=0, column=0, columnspan=3, **stickypad)
            ttk.Button(frame, text="\u21BB", width=0, command=self.update).grid(row=1, column=0, sticky=tk.SW, ipadx=5, **pad)
            ttk.Button(frame, text="Ignore Selected", command=self.do_ignore).grid(row=1, column=1, sticky=tk.SW, ipadx=5, **pad)
            ttk.Button(frame, text="Download Selected", command=self.do_download).grid(row=1, column=2, sticky=tk.SE, ipadx=5, **pad)
            return frame

        def frame_outgoing(master):
            """Frame for outgoing songs."""
            frame = ttk.Frame(master)

            # Configure grid
            frame.rowconfigure(0, weight=1)
            frame.rowconfigure(1, weight=0)
            frame.columnconfigure(0, weight=0)
            frame.columnconfigure(1, weight=1)
            frame.columnconfigure(2, weight=1)

            # Place widgets
            self.listbox_outgoing = tk.Listbox(frame, selectmode=tk.EXTENDED)
            self.listbox_outgoing.grid(row=0, column=0, columnspan=3, **stickypad)
            ttk.Button(frame, text="\u21BB", width=0, command=self.update).grid(row=1, column=0, sticky=tk.SW, ipadx=5, **pad)
            ttk.Button(frame, text="Remove Selected", command=self.do_remove).grid(row=1, column=1, sticky=tk.SW, ipadx=5, **pad)
            ttk.Button(frame, text="Share Songs...", command=self.do_share).grid(row=1, column=2, sticky=tk.SE, ipadx=5, **pad)

            return frame

        def separator(master):
            """Widget to separate frames."""
            return ttk.Separator(master)

        # Place widgets
        frame_settings(master).grid(row=0, **stickypad)
        separator(master).grid(row=1, sticky=tk.EW, padx=10)
        frame_outgoing(master).grid(row=2, **stickypad)
        separator(master).grid(row=3, sticky=tk.EW, padx=10)
        frame_incoming(master).grid(row=4, **stickypad)

    def browse_downloads(self):
        """Browser for a new downloads directory."""
        path = filedialog.askdirectory()
        logging.debug("path: {}".format(path))
        if path:
            self.user.path_downloads = path
            self.path_downloads.set(self.user.path_downloads)

    def do_remove(self):
        """Remove selected songs."""
        for index in (int(s) for s in self.listbox_outgoing.curselection()):
            self.outgoing[index].ignore()
        self.update()

    def do_share(self):
        """Share songs."""
        paths = filedialog.askopenfilenames()
        if isinstance(paths, str):  # http://bugs.python.org/issue5712
            paths = self.master.tk.splitlist(paths)
        logging.debug("paths: {}".format(paths))
        for path in paths:
            self.user.recommend(path)
        self.update()

    def do_ignore(self):
        """Ignore selected songs."""
        for index in (int(s) for s in self.listbox_incoming.curselection()):
            self.incoming[index].ignore()
        self.update()

    def do_download(self):
        """Download all songs."""
        for index in (int(s) for s in self.listbox_incoming.curselection()):
            self.incoming[index].download()
        self.update()

    def update(self):
        """Update the list of outgoing and incoming songs."""
        # Cleanup outgoing songs
        self.user.cleanup()
        # Update outgoing songs list
        logging.info("updating outoing songs...")
        self.outgoing = list(self.user.outgoing)
        self.listbox_outgoing.delete(0, tk.END)
        for song in self.outgoing:
            self.listbox_outgoing.insert(tk.END, song.out_string)
        # Update incoming songs list
        logging.info("updating incoming songs...")
        self.incoming = list(self.user.incoming)
        self.listbox_incoming.delete(0, tk.END)
        for song in self.incoming:
            self.listbox_incoming.insert(tk.END, song.in_string)


def main(args=None):
    """Process command-line arguments and run the program.
    """
    # Main parser
    parser = argparse.ArgumentParser(prog=GUI, description=__doc__, **SHARED)
    # Hidden argument to override the root sharing directory path
    parser.add_argument('--root', metavar="PATH", help=argparse.SUPPRESS)
    # Hidden argument to run the program as a different user
    parser.add_argument('--test', metavar='FirstLast', help=argparse.SUPPRESS)

    # Parse arguments
    args = parser.parse_args(args=args)

    # Configure logging
    _configure_logging(args.verbose)

    # Run the program
    try:
        success = run(args)
    except KeyboardInterrupt:
        logging.debug("program manually closed")
    else:
        if success:
            logging.debug("program exited")
        else:
            logging.debug("program exited with error")
            sys.exit(1)


def _configure_logging(verbosity=0):
    """Configure logging using the provided verbosity level (0+)."""

    # Configure the logging level and format
    if verbosity == 0:
        level = settings.VERBOSE_LOGGING_LEVEL
        default_format = settings.DEFAULT_LOGGING_FORMAT
        verbose_format = settings.VERBOSE_LOGGING_FORMAT
    else:
        level = settings.VERBOSE2_LOGGING_LEVEL
        default_format = verbose_format = settings.VERBOSE_LOGGING_FORMAT

    # Set a custom formatter
    logging.basicConfig(level=level)
    formatter = WarningFormatter(default_format, verbose_format)
    logging.root.handlers[0].setFormatter(formatter)


def run(args):
    """Start the GUI."""

    # Exit if tkinter is not available
    if isinstance(tk, Mock) or isinstance(ttk, Mock):
        logging.error("tkinter is not available")
        return False

    else:  # pragma: no cover - manual test

        root = tk.Tk()
        root.title("{} ({})".format(__project__, __version__))
        root.minsize(500, 500)

        # Map the Mac 'command' key to 'control'
        root.bind_class('Listbox', '<Command-Button-1>',
                        root.bind_class('Listbox', '<Control-Button-1>'))

        # Temporarity hide the window for other dialogs
        root.withdraw()

        # Start the application
        app = Application(master=root, root=args.root, name=args.test)
        app.mainloop()

        return True


if __name__ == '__main__':  # pragma: no cover - manual test
    main()
