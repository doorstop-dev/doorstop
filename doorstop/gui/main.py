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

    def __init__(self, root, project=""):
        ttk.Frame.__init__(self, root)

        # Create variables
        self.stringvar_project = tk.StringVar()
        self.stringvar_project.set(project)

        # Initialize the GUI
        frame = self.init(root)
        frame.pack(fill=tk.BOTH, expand=1)

    def init(self, root):  # pylint: disable=R0914
        """Initialize and return the main frame."""  # pylint: disable=C0301

        # Shared arguments
        width_outline = 20
        width_text = 40
        width_code = 30
        width_id = 10
        height_text = 10
        height_ext = 5
        height_code = 3

        # Shared keyword arguments
        kw_f = {'padding': 5}  # constructor arguments for frames
        kw_gp = {'padx': 2, 'pady': 2}  # grid arguments for padded widgets
        kw_gs = {'sticky': tk.NSEW}  # grid arguments for sticky widgets
        kw_gsp = dict(chain(kw_gs.items(), kw_gp.items()))  # grid arguments for sticky padded widgets

        # Configure grid
        frame = ttk.Frame(root, **kw_f)
        frame.rowconfigure(0, weight=0)
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=2)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)
        frame.columnconfigure(3, weight=2)

        # Create widgets
        def frame_project(root):
            """Frame for the current project."""

            # Configure grid
            frame = ttk.Frame(root, **kw_f)
            frame.rowconfigure(0, weight=1)
            frame.columnconfigure(0, weight=0)
            frame.columnconfigure(1, weight=1)
            frame.columnconfigure(2, weight=0)

            # Place widgets
            ttk.Label(frame, text="Project:").grid(row=0, column=0, **kw_gp)
            ttk.Entry(frame, textvariable=self.stringvar_project).grid(row=0, column=1, **kw_gsp)
            ttk.Button(frame, text="...", command=self.browse_root).grid(row=0, column=2, **kw_gp)

            return frame

        def frame_document(root):
            """Frame for the current document."""

            # Configure grid
            frame = ttk.Frame(root, **kw_f)
            frame.rowconfigure(0, weight=1)
            frame.columnconfigure(0, weight=0)
            frame.columnconfigure(1, weight=1)
            frame.columnconfigure(2, weight=0)

            # Place widgets
            ttk.Label(frame, text="Document:").grid(row=0, column=0, **kw_gp)
            self.stringvar_document = tk.StringVar()
            self.combobox_documents = ttk.Combobox(frame, textvariable=self.stringvar_document, state='readonly')
            self.combobox_documents.grid(row=0, column=1, **kw_gsp)
            ttk.Button(frame, text="New...", command=self.new).grid(row=0, column=2, **kw_gp)

            return frame

        def frame_outline(root):
            """Frame for current document's outline and items."""

            # Configure grid
            frame = ttk.Frame(root, **kw_f)
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
            ttk.Label(frame, text="Outline:").grid(row=0, column=0, columnspan=4, sticky=tk.W, **kw_gp)
            ttk.Label(frame, text="Items:").grid(row=0, column=4, columnspan=2, sticky=tk.W, **kw_gp)
            self.listbox_outline = tk.Listbox(frame, width=width_outline)
            self.listbox_outline.grid(row=1, column=0, columnspan=4, **kw_gsp)
            self.listbox_items = tk.Listbox(frame, width=width_text)
            self.listbox_items.grid(row=1, column=4, columnspan=2, **kw_gsp)
            ttk.Button(frame, text="<", width=0, command=self.left).grid(row=2, column=0, sticky=tk.EW, padx=(2, 0))
            ttk.Button(frame, text="v", width=0, command=self.down).grid(row=2, column=1, sticky=tk.EW)
            ttk.Button(frame, text="^", width=0, command=self.up).grid(row=2, column=2, sticky=tk.EW)
            ttk.Button(frame, text=">", width=0, command=self.right).grid(row=2, column=3, sticky=tk.EW, padx=(0, 2))
            ttk.Button(frame, text="Add Item", command=self.add).grid(row=2, column=4, sticky=tk.W, **kw_gp)
            ttk.Button(frame, text="Remove Selected Item", command=self.remove).grid(row=2, column=5, sticky=tk.E, **kw_gp)
            ttk.Label(frame, text="Items Filter:").grid(row=3, column=0, columnspan=6, sticky=tk.W, **kw_gp)
            tk.Text(frame, height=height_code, width=width_code).grid(row=4, column=0, columnspan=6, **kw_gsp)

            return frame

        def frame_selected(root):
            """Frame for the currently selected item."""

            # Configure grid
            frame = ttk.Frame(root, **kw_f)
            frame.rowconfigure(0, weight=0)
            frame.rowconfigure(1, weight=4)
            frame.rowconfigure(2, weight=0)
            frame.rowconfigure(3, weight=1)
            frame.rowconfigure(4, weight=1)
            frame.rowconfigure(5, weight=1)
            frame.rowconfigure(6, weight=1)
            frame.rowconfigure(7, weight=0)
            frame.rowconfigure(8, weight=0)
            frame.rowconfigure(9, weight=0)
            frame.rowconfigure(10, weight=0)
            frame.rowconfigure(11, weight=4)
            frame.columnconfigure(0, weight=0, pad=kw_f['padding'] * 2)
            frame.columnconfigure(1, weight=1)
            frame.columnconfigure(2, weight=1)

            # Place widgets
            ttk.Label(frame, text="Selected Item:").grid(row=0, column=0, columnspan=3, sticky=tk.W, **kw_gp)
            tk.Text(frame, width=width_text, height=height_text).grid(row=1, column=0, columnspan=3, **kw_gsp)
            ttk.Label(frame, text="Properties:").grid(row=2, column=0, sticky=tk.W, **kw_gp)
            ttk.Label(frame, text="Links:").grid(row=2, column=1, columnspan=2, sticky=tk.W, **kw_gp)
            ttk.Checkbutton(frame, text="Active", command=self.update).grid(row=3, column=0, sticky=tk.W, **kw_gp)
            self.listbox_links = tk.Listbox(frame, width=width_id, height=6)
            self.listbox_links.grid(row=3, column=1, rowspan=4, **kw_gsp)
            self.stringvar_link = tk.StringVar()
            ttk.Entry(frame, width=width_id, textvariable=self.stringvar_link).grid(row=3, column=2, sticky=tk.EW + tk.N, **kw_gp)
            ttk.Checkbutton(frame, text="Derived", command=self.update).grid(row=4, column=0, sticky=tk.W, **kw_gp)
            ttk.Button(frame, text="<< Link Item", command=self.link).grid(row=4, column=2, **kw_gp)
            ttk.Checkbutton(frame, text="Heading", command=self.update).grid(row=5, column=0, sticky=tk.W, **kw_gp)
            self.stringvar_unlink = tk.StringVar()
            ttk.Entry(frame, width=width_id, textvariable=self.stringvar_unlink).grid(row=5, column=2, sticky=tk.EW, **kw_gp)
            ttk.Checkbutton(frame, text="Normative", command=self.update).grid(row=6, column=0, sticky=tk.W, **kw_gp)
            ttk.Button(frame, text=">> Unlink Item", command=self.unlink).grid(row=6, column=2, **kw_gp)
            ttk.Label(frame, text="External Reference:").grid(row=7, column=0, columnspan=3, sticky=tk.W, **kw_gp)
            self.stringvar_ref = tk.StringVar()
            ttk.Entry(frame, width=width_text, textvariable=self.stringvar_ref).grid(row=8, column=0, columnspan=3, **kw_gsp)
            ttk.Label(frame, text="Extended Attributes:").grid(row=9, column=0, columnspan=3, sticky=tk.W, **kw_gp)
            self.stringvar_extended = tk.StringVar()
            self.combobox_extended = ttk.Combobox(frame, textvariable=self.stringvar_extended)
            self.combobox_extended.grid(row=10, column=0, columnspan=3, **kw_gsp)
            tk.Text(frame, width=width_text, height=height_ext).grid(row=11, column=0, columnspan=3, **kw_gsp)

            return frame

        def frame_family(root):
            """Frame for the parent and child document items."""

            # Configure grid
            frame = ttk.Frame(root, **kw_f)
            frame.rowconfigure(0, weight=0)
            frame.rowconfigure(1, weight=1)
            frame.rowconfigure(2, weight=0)
            frame.rowconfigure(3, weight=1)
            frame.columnconfigure(0, weight=1)

            # Place widgets
            ttk.Label(frame, text="Linked Parent Items:").grid(row=0, column=0, sticky=tk.W, **kw_gp)
            self.listbox_parents = tk.Listbox(frame, width=width_text)
            self.listbox_parents.grid(row=1, column=0, **kw_gsp)
            ttk.Label(frame, text="Linked Child Items:").grid(row=2, column=0, sticky=tk.W, **kw_gp)
            self.listbox_children = tk.Listbox(frame, width=width_text)
            self.listbox_children.grid(row=3, column=0, **kw_gsp)

            return frame

        # Place widgets
        frame_project(frame).grid(row=0, column=0, columnspan=2, **kw_gs)
        frame_document(frame).grid(row=0, column=2, columnspan=2, **kw_gs)
        frame_outline(frame).grid(row=1, column=0, **kw_gs)
        frame_selected(frame).grid(row=1, column=1, columnspan=2, **kw_gs)
        frame_family(frame).grid(row=1, column=3, **kw_gs)

        return frame

    def browse_root(self):
        """Browse for the root of a project."""
        path = filedialog.askdirectory()
        logging.debug("path: {}".format(path))
        if path:
            self.stringvar_project.set(path)

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

    def unlink(self):
        raise NotImplementedError()

    def update(self):
        raise NotImplementedError()


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

        # Start the application
        app = Application(root=root, project=args.root)
        app.mainloop()

        return True


if __name__ == '__main__':  # pragma: no cover - manual test
    main()
