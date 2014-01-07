#!/usr/bin/env python

"""
Graphical interface for Doorstop.
"""

import sys
from unittest.mock import Mock, MagicMock
try:  # pragma: no cover - not measurable
    import tkinter as tk
    from tkinter import messagebox, simpledialog, filedialog
except ImportError as err:  # pragma: no cover - not measurable
    sys.stderr.write("WARNING: {}\n".format(err))
    tk = Mock()  # pylint: disable=C0103

import os
import argparse
from itertools import chain
import logging


from doorstop import GUI, __project__, __version__
from doorstop.common import SHARED, WarningFormatter
from doorstop import settings


class Application(tk.Frame):  # pragma: no cover - manual test, pylint: disable=R0904,R0924
    """Tkinter application for DropTheBeat."""

    def __init__(self, master=None, root=None, name=None):
        tk.Frame.__init__(self, master)

        # Load the root sharing directory
        self.root = root or MagicMock()

        # Load the user
        self.user = MagicMock()

        # Create variables
        self.path_downloads = tk.StringVar(value=self.user.path_downloads)
        self.outgoing = []
        self.incoming = []

        # Initialize the GUI
        self.listbox_incoming = None
        self.init(master)

        # Show the GUI
        master.deiconify()
        self.update()

    def init(self, master):  # pylint: disable=R0914
        """Initialize frames and widgets."""  # pylint: disable=C0301

        # Shared settings

        sticky = {'sticky': tk.NSEW}
        pad = {'padx': 5, 'pady': 5}
        stickypad = dict(chain(sticky.items(), pad.items()))

        # Create frames

        frame_documents = tk.Frame(master)
        frame_items = tk.Frame(master)

        frame_div1 = tk.Frame(master, height=2, bd=1, relief=tk.SUNKEN)

        # Create widets for frames

        label_project = tk.Label(frame_documents, text="Project:")
        entry_project = tk.Entry(frame_documents, state='readonly', textvariable=self.path_downloads)
        button_project = tk.Button(frame_documents, text="...", command=self.browse_downloads)

        label_document = tk.Label(frame_documents, text="Document:")
        option_document = tk.OptionMenu(frame_documents, tk.StringVar(), "a")

        self.listbox_incoming = tk.Listbox(frame_items, selectmode=tk.EXTENDED)
        button_refin = tk.Button(frame_items, text="\u21BB", command=self.update)
        button_ignore = tk.Button(frame_items, text="Ignore Selected", command=self.do_ignore)
        button_download = tk.Button(frame_items, text="Download Selected", command=self.do_download)

        # Specify frame resizing

        frame_documents.rowconfigure(0, weight=1)
        frame_documents.columnconfigure(0, weight=0)
        frame_documents.columnconfigure(1, weight=1)
        frame_documents.columnconfigure(2, weight=0)

        frame_items.rowconfigure(0, weight=1)
        frame_items.rowconfigure(1, weight=0)
        frame_items.columnconfigure(0, weight=0)
        frame_items.columnconfigure(1, weight=1)
        frame_items.columnconfigure(2, weight=1)

        # Pack widgets in frames

        label_project.grid(row=0, column=0, **pad)
        entry_project.grid(row=0, column=1, **stickypad)
        button_project.grid(row=0, column=2, ipadx=5, **pad)
        label_document.grid(row=0, column=3)
        option_document.grid(row=0, column=4)

        self.listbox_incoming.grid(row=0, column=0, columnspan=3, **stickypad)
        button_refin.grid(row=1, column=0, sticky=tk.SW, ipadx=5, **pad)
        button_ignore.grid(row=1, column=1, sticky=tk.SW, ipadx=5, **pad)
        button_download.grid(row=1, column=2, sticky=tk.SE, ipadx=5, **pad)

        # Specify master resizing

        master.rowconfigure(0, weight=0)
        master.rowconfigure(2, weight=1)
        master.rowconfigure(4, weight=1)
        master.columnconfigure(0, weight=1)

        # Pack frames in master

        frame_documents.grid(row=0, **stickypad)
        frame_div1.grid(row=3, sticky=tk.EW, padx=10)
        frame_items.grid(row=4, **stickypad)

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
        pass


def main(args=None):
    """Process command-line arguments and run the program.
    """
    # Main parser
    parser = argparse.ArgumentParser(prog=GUI, description=__doc__, **SHARED)

    # Parse arguments
    args = parser.parse_args(args=args)

    # Configure logging
    _configure_logging(args.verbose)

    # Run the program
    try:
        success = run(args, os.getcwd(), parser.error)
    except KeyboardInterrupt:
        logging.debug("program manually closed")
        success = False
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


def run(args, cwd, err):
    """Start the GUI."""

    # Exit if tkinter is not available
    if isinstance(tk, Mock):
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
        app = Application(master=root)
        app.mainloop()

        return True


if __name__ == '__main__':  # pragma: no cover - manual test
    main()
