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

    def __init__(self, master, root=""):
        ttk.Frame.__init__(self, master)

        # Create variables
        self.user = MagicMock()
        self.path_downloads = MagicMock()
        self.outgoing = []
        self.incoming = []

        self.stringvar_root = tk.StringVar()
        self.stringvar_root.set(root)

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
        pad = {'padx': 2, 'pady': 2}
        stickypad = dict(chain(sticky.items(), pad.items()))
        width_outline = 20
        width_text = 40
        width_code = 30
        width_button = 3
        height_text = 10
        height_ext = 5
        height_code = 3

        # Configure grid
        master.rowconfigure(0, weight=0)
        master.rowconfigure(1, weight=1)
        master.columnconfigure(0, weight=2)
        master.columnconfigure(1, weight=1)
        master.columnconfigure(2, weight=1)
        master.columnconfigure(3, weight=2)

        # Create widgets
        def frame_project(master):
            """Frame for the current project."""
            frame = ttk.Frame(master)

            # Configure grid
            frame.rowconfigure(0, weight=1)
            frame.columnconfigure(0, weight=0)
            frame.columnconfigure(1, weight=1)
            frame.columnconfigure(2, weight=0)

            # Place widgets
            ttk.Label(frame, text="Project:").grid(row=0, column=0, **pad)
            ttk.Entry(frame, textvariable=self.stringvar_root).grid(row=0, column=1, **stickypad)
            ttk.Button(frame, text="...", width=width_button, command=self.browse_root).grid(row=0, column=2, **pad)

            return frame

        def frame_document(master):
            """Frame for the current document."""
            frame = ttk.Frame(master)

            # Configure grid
            frame.rowconfigure(0, weight=1)
            frame.columnconfigure(0, weight=0)
            frame.columnconfigure(1, weight=1)
            frame.columnconfigure(2, weight=0)

            # Place widgets
            ttk.Label(frame, text="Document:").grid(row=0, column=0, **pad)
            self.stringvar_document = tk.StringVar()
            self.combobox_documents = ttk.Combobox(frame, textvariable=self.stringvar_document, state='readonly')
            self.combobox_documents.grid(row=0, column=1, **stickypad)
            ttk.Button(frame, text="New...", command=self.new).grid(row=0, column=2, **pad)

            return frame

        def frame_outline(master):
            """Frame for current document's outline and items."""
            frame = ttk.Frame(master)

            # Configure grid
            frame.rowconfigure(0, weight=0)
            frame.rowconfigure(1, weight=5)
            frame.rowconfigure(2, weight=0)
            frame.rowconfigure(3, weight=0)
            frame.rowconfigure(4, weight=1)
            frame.columnconfigure(0, weight=0)
            frame.columnconfigure(1, weight=0)
            frame.columnconfigure(2, weight=0)
            frame.columnconfigure(3, weight=0)
            frame.columnconfigure(4, weight=1)
            frame.columnconfigure(5, weight=1)

            # Place widgets
            ttk.Label(frame, text="Outline:").grid(row=0, column=0, columnspan=4, sticky=tk.W, **pad)
            ttk.Label(frame, text="Items:").grid(row=0, column=4, columnspan=2, sticky=tk.W, **pad)
            self.listbox_outline = tk.Listbox(frame, width=width_outline)
            self.listbox_outline.grid(row=1, column=0, columnspan=4, **stickypad)
            self.listbox_items = tk.Listbox(frame, width=width_text)
            self.listbox_items.grid(row=1, column=4, columnspan=2, **stickypad)
            ttk.Button(frame, text="<", width=width_button, command=self.left).grid(row=2, column=0, **pad)
            ttk.Button(frame, text="v", width=width_button, command=self.down).grid(row=2, column=1, **pad)
            ttk.Button(frame, text="^", width=width_button, command=self.up).grid(row=2, column=2, **pad)
            ttk.Button(frame, text=">", width=width_button, command=self.right).grid(row=2, column=3, **pad)
            ttk.Button(frame, text="Add", command=self.add).grid(row=2, column=4, **pad)
            ttk.Button(frame, text="Remove", command=self.remove).grid(row=2, column=5, **pad)
            ttk.Label(frame, text="Filter:").grid(row=3, column=0, columnspan=6, sticky=tk.W, **pad)
            tk.Text(frame, height=height_code, width=width_code).grid(row=4, column=0, columnspan=5, **stickypad)
            ttk.Button(frame, text="Clear", command=self.clear).grid(row=4, column=5, **pad)

            return frame

        def frame_selected(master):
            """Frame for the currently selected item."""
            frame = ttk.Frame(master)

            # Configure grid
            frame.rowconfigure(0, weight=0)
            frame.rowconfigure(1, weight=1)
            frame.rowconfigure(2, weight=0)
            frame.rowconfigure(3, weight=0)
            frame.rowconfigure(4, weight=0)
            frame.rowconfigure(5, weight=0)
            frame.rowconfigure(6, weight=0)
            frame.rowconfigure(7, weight=0)
            frame.rowconfigure(8, weight=0)
            frame.rowconfigure(9, weight=0)
            frame.rowconfigure(10, weight=0)
            frame.rowconfigure(11, weight=1)
            frame.columnconfigure(0, weight=0)
            frame.columnconfigure(1, weight=1)
            frame.columnconfigure(2, weight=1)

            # Place widgets
            ttk.Label(frame, text="Selected Item:").grid(row=0, column=0, columnspan=3, sticky=tk.W, **pad)
            tk.Text(frame, width=width_text, height=height_text).grid(row=1, column=0, columnspan=3, **stickypad)
            ttk.Label(frame, text="Properties:").grid(row=2, column=0, sticky=tk.W, **pad)
            ttk.Label(frame, text="Links:").grid(row=2, column=1, columnspan=2, sticky=tk.W, **pad)
            ttk.Checkbutton(frame, text="Active").grid(row=3, column=0, sticky=tk.W, **pad)
            self.listbox_links = tk.Listbox(frame, width=10)
            self.listbox_links.grid(row=3, column=1, rowspan=4, **stickypad)
            self.stringvar_link = tk.StringVar()
            ttk.Entry(frame, width=10, textvariable=self.stringvar_link).grid(row=3, column=2, sticky=tk.EW, **pad)
            ttk.Checkbutton(frame, text="Derived").grid(row=4, column=0, sticky=tk.W, **pad)
            ttk.Button(frame, text="<< Link", command=self.link).grid(row=4, column=2, **pad)
            ttk.Checkbutton(frame, text="Heading").grid(row=5, column=0, sticky=tk.W, **pad)
            self.stringvar_unlink = tk.StringVar()
            ttk.Entry(frame, width=10, textvariable=self.stringvar_unlink).grid(row=5, column=2, sticky=tk.EW, **pad)
            ttk.Checkbutton(frame, text="Normative").grid(row=6, column=0, sticky=tk.W, **pad)
            ttk.Button(frame, text=">> Unlink", command=self.link).grid(row=6, column=2, **pad)
            ttk.Label(frame, text="External Reference:").grid(row=7, column=0, columnspan=3, sticky=tk.W, **pad)
            self.stringvar_ref = tk.StringVar()
            ttk.Entry(frame, width=width_text, textvariable=self.stringvar_ref).grid(row=8, column=0, columnspan=3, **stickypad)
            ttk.Label(frame, text="Extended Attributes:").grid(row=9, column=0, columnspan=3, sticky=tk.W, **pad)
            self.stringvar_extended = tk.StringVar()
            self.combobox_extended = ttk.Combobox(frame, textvariable=self.stringvar_extended)
            self.combobox_extended.grid(row=10, column=0, columnspan=3, **stickypad)
            tk.Text(frame, width=width_text, height=height_ext).grid(row=11, column=0, columnspan=3, **stickypad)

            return frame

        def frame_family(master):
            """Frame for the parent and child document items."""
            frame = ttk.Frame(master)

            # Configure grid
            frame.rowconfigure(0, weight=0)
            frame.rowconfigure(1, weight=1)
            frame.rowconfigure(2, weight=0)
            frame.rowconfigure(3, weight=1)
            frame.columnconfigure(0, weight=1)

            # Place widgets
            ttk.Label(frame, text="Linked Parent Items:").grid(row=0, column=0, sticky=tk.W, **pad)
            self.listbox_parents = tk.Listbox(frame, width=width_text)
            self.listbox_parents.grid(row=1, column=0, **stickypad)
            ttk.Label(frame, text="Linked Child Items:").grid(row=2, column=0, sticky=tk.W, **pad)
            self.listbox_children = tk.Listbox(frame, width=width_text)
            self.listbox_children.grid(row=3, column=0, **stickypad)

            return frame

        # Place widgets
        frame_project(master).grid(row=0, column=0, columnspan=2, **stickypad)
        frame_document(master).grid(row=0, column=2, columnspan=2, **stickypad)
        frame_outline(master).grid(row=1, column=0, **stickypad)
        frame_selected(master).grid(row=1, column=1, columnspan=2, **stickypad)
        frame_family(master).grid(row=1, column=3, **stickypad)

    def browse_root(self):
        """Browse the root of the project."""
        path = filedialog.askdirectory()
        logging.debug("path: {}".format(path))
        if path:
            self.user.path_downloads = path
            self.path_downloads.set(self.user.path_downloads)

    def new(self):
        raise NotImplementedError()

    def left(self):
        raise NotImplementedError()

    def down(self):
        raise NotImplementedError()

    def up(self):
        raise NotImplementedError()

    def right(self):
        raise NotImplementedError()

    def add(self):
        raise NotImplementedError()

    def remove(self):
        raise NotImplementedError()

    def clear(self):
        raise NotImplementedError()

    def link(self):
        raise NotImplementedError()

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
#         # Cleanup outgoing songs
#         self.user.cleanup()
#         # Update outgoing songs list
#         logging.info("updating outoing songs...")
#         self.outgoing = list(self.user.outgoing)
#         self.listbox_outgoing.delete(0, tk.END)
#         for song in self.outgoing:
#             self.listbox_outgoing.insert(tk.END, song.out_string)
#         # Update incoming songs list
#         logging.info("updating incoming songs...")
#         self.incoming = list(self.user.incoming)
#         self.listbox_incoming.delete(0, tk.END)
#         for song in self.incoming:
#             self.listbox_incoming.insert(tk.END, song.in_string)


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
        # root.minsize(1000, 600)

        # Map the Mac 'command' key to 'control'
        root.bind_class('Listbox', '<Command-Button-1>',
                        root.bind_class('Listbox', '<Control-Button-1>'))

        # Temporarity hide the window for other dialogs
        root.withdraw()

        # Start the application
        app = Application(master=root, root=args.root)
        app.mainloop()

        return True


if __name__ == '__main__':  # pragma: no cover - manual test
    main()
