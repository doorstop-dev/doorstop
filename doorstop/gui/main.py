#!/usr/bin/env python

"""
Graphical interface for Doorstop.
"""

import sys
from unittest.mock import Mock
try:  # pragma: no cover - not measurable
    import tkinter as tk
    from tkinter import ttk
    from tkinter import font, messagebox, simpledialog, filedialog
except ImportError as err:  # pragma: no cover - not measurable
    sys.stderr.write("WARNING: {}\n".format(err))
    tk = Mock()  # pylint: disable=C0103
    ttk = Mock()  # pylint: disable=C0103
import os
import argparse
from itertools import chain
import logging


from doorstop import GUI, __project__, __version__
from doorstop.common import SHARED, WarningFormatter, DoorstopError
from doorstop.core import vcs
from doorstop.core import tree
from doorstop import settings


def main(args=None):
    """Process command-line arguments and run the program.
    """
    # Main parser
    parser = argparse.ArgumentParser(prog=GUI, description=__doc__, **SHARED)
    # Hidden argument to override the root sharing directory path
    parser.add_argument('-j', '--project', metavar="PATH",
                        help="path to the root of the project")

    # Parse arguments
    args = parser.parse_args(args=args)

    # Configure logging
    _configure_logging(args.verbose)

    # Run the program
    try:
        success = _run(args, os.getcwd(), parser.error)
    except KeyboardInterrupt:
        logging.debug("program interrupted")
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
        default_format = settings.VERBOSE_LOGGING_FORMAT
        verbose_format = settings.VERBOSE_LOGGING_FORMAT
    else:
        level = settings.VERBOSE2_LOGGING_LEVEL
        default_format = settings.VERBOSE_LOGGING_FORMAT
        verbose_format = settings.VERBOSE_LOGGING_FORMAT

    # Set a custom formatter
    logging.basicConfig(level=level)
    formatter = WarningFormatter(default_format, verbose_format)
    logging.root.handlers[0].setFormatter(formatter)


def _run(args, cwd, err):
    """Start the GUI.

    @param args: Namespace of CLI arguments (from this module or the CLI)
    @param cwd: current working directory
    @param err: function to call for CLI errors
    """

    # Exit if tkinter is not available
    if isinstance(tk, Mock) or isinstance(ttk, Mock):
        logging.error("tkinter is not available")
        return False

    else:  # pragma: no cover, manual test

        root = tk.Tk()
        root.title("{} ({})".format(__project__, __version__))
        # TODO: set a minimum window size
        # root.minsize(1000, 600)

        # Start the application
        app = Application(root, cwd, args.project)
        app.mainloop()

        return True


class Application(ttk.Frame):  # pragma: no cover, manual test
    """Graphical application for Doorstop."""

    def __init__(self, root, cwd, project):
        self.root = root
        self.cwd = cwd
        ttk.Frame.__init__(self, self.root)

        self.ignore = False  # indicates an event is internal an can be ignored

        # Create string variables
        self.stringvar_project = tk.StringVar(value=project or '')
        self.stringvar_project.trace('w', self.update_project)
        self.stringvar_document = tk.StringVar()
        self.stringvar_document.trace('w', self.update_tree)
        self.stringvar_item = tk.StringVar()
        self.stringvar_item.trace('w', self.update_document)
        self.stringvar_text = tk.StringVar()
        self.stringvar_text.trace('w', self.update_item)
        self.intvar_active = tk.IntVar()
        self.intvar_active.trace('w', self.update_item)
        self.intvar_derived = tk.IntVar()
        self.intvar_derived.trace('w', self.update_item)
        self.intvar_normative = tk.IntVar()
        self.intvar_normative.trace('w', self.update_item)
        self.intvar_heading = tk.IntVar()
        self.intvar_heading.trace('w', self.update_item)

        # Create widget variables
        self.combobox_documents = None
        self.listbox_outline = None
        self.text_items = None
        self.text_item = None
        self.text_parents = None
        self.text_children = None

        # Initialize the GUI
        frame = self.init(root)
        frame.pack(fill=tk.BOTH, expand=1)

        # Start the application
        self.root.after(0, self.find)

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

        # Shared style
        fixed = font.Font(family="Courier", size=10)

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
            ttk.Button(frame, text="...", command=self.browse).grid(row=0, column=2, **kw_gp)

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
            self.combobox_documents = ttk.Combobox(frame, textvariable=self.stringvar_document, state='readonly')
            # self.combobox_documents.bind("<<ComboboxSelected>>", self.update_items)
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

            def listbox_outline_listboxselect(event):
                """Callback for selecting an item."""
                widget = event.widget
                index = int(widget.curselection()[0])
                value = widget.get(index)
                self.stringvar_item.set(value)

            # Place widgets
            ttk.Label(frame, text="Outline:").grid(row=0, column=0, columnspan=4, sticky=tk.W, **kw_gp)
            ttk.Label(frame, text="Items:").grid(row=0, column=4, columnspan=2, sticky=tk.W, **kw_gp)
            self.listbox_outline = tk.Listbox(frame, width=width_outline, font=fixed)
            self.listbox_outline.bind('<<ListboxSelect>>', listbox_outline_listboxselect)
            self.listbox_outline.grid(row=1, column=0, columnspan=4, **kw_gsp)
            self.text_items = tk.Text(frame, width=width_text, wrap=tk.WORD, font=fixed)
            self.text_items.grid(row=1, column=4, columnspan=2, **kw_gsp)
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

            def text_item_focusout(event):
                """Callback for updating text."""
                logging.critical(text_item_focusout.__name__)
                widget = event.widget
                value = widget.get('1.0', 'end')
                self.stringvar_text.set(value)

            # Place widgets
            ttk.Label(frame, text="Selected Item:").grid(row=0, column=0, columnspan=3, sticky=tk.W, **kw_gp)
            self.text_item = tk.Text(frame, width=width_text, height=height_text, wrap=tk.WORD, font=fixed)
            self.text_item.bind('<FocusOut>', text_item_focusout)
            self.text_item.grid(row=1, column=0, columnspan=3, **kw_gsp)
            ttk.Label(frame, text="Properties:").grid(row=2, column=0, sticky=tk.W, **kw_gp)
            ttk.Label(frame, text="Links:").grid(row=2, column=1, columnspan=2, sticky=tk.W, **kw_gp)
            ttk.Checkbutton(frame, text="Active", variable=self.intvar_active).grid(row=3, column=0, sticky=tk.W, **kw_gp)
            self.listbox_links = tk.Listbox(frame, width=width_id, height=6)
            self.listbox_links.grid(row=3, column=1, rowspan=4, **kw_gsp)
            self.stringvar_link = tk.StringVar()
            ttk.Entry(frame, width=width_id, textvariable=self.stringvar_link).grid(row=3, column=2, sticky=tk.EW + tk.N, **kw_gp)
            ttk.Checkbutton(frame, text="Derived", variable=self.intvar_derived).grid(row=4, column=0, sticky=tk.W, **kw_gp)
            ttk.Button(frame, text="<< Link Item", command=self.link).grid(row=4, column=2, **kw_gp)
            ttk.Checkbutton(frame, text="Normative", variable=self.intvar_normative).grid(row=5, column=0, sticky=tk.W, **kw_gp)
            self.stringvar_unlink = tk.StringVar()
            ttk.Entry(frame, width=width_id, textvariable=self.stringvar_unlink).grid(row=5, column=2, sticky=tk.EW, **kw_gp)
            ttk.Checkbutton(frame, text="Heading", variable=self.intvar_heading).grid(row=6, column=0, sticky=tk.W, **kw_gp)
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
            ttk.Label(frame, text="Linked To:").grid(row=0, column=0, sticky=tk.W, **kw_gp)
            self.text_parents = tk.Text(frame, width=width_text, wrap=tk.WORD, font=fixed)
            self.text_parents.grid(row=1, column=0, **kw_gsp)
            ttk.Label(frame, text="Linked From:").grid(row=2, column=0, sticky=tk.W, **kw_gp)
            self.text_children = tk.Text(frame, width=width_text, wrap=tk.WORD, font=fixed)
            self.text_children.grid(row=3, column=0, **kw_gsp)

            return frame

        # Place widgets
        frame_project(frame).grid(row=0, column=0, columnspan=2, **kw_gs)
        frame_document(frame).grid(row=0, column=2, columnspan=2, **kw_gs)
        frame_outline(frame).grid(row=1, column=0, **kw_gs)
        frame_selected(frame).grid(row=1, column=1, columnspan=2, **kw_gs)
        frame_family(frame).grid(row=1, column=3, **kw_gs)

        return frame

    def find(self):
        """Find the root of the project."""
        if not self.stringvar_project.get():
            try:
                path = vcs.find_root(self.cwd)
            except DoorstopError as exc:
                logging.error(exc)
            else:
                self.stringvar_project.set(path)

    def update_project(self, *args):
        logging.critical(self.update_project.__name__)

        self.tree = tree.build(root=self.stringvar_project.get())

        values = [document.prefix_relpath for document in self.tree]
        self.combobox_documents['values'] = values
        self.combobox_documents.current(0)

    def update_tree(self, *args, item_index=0):
        logging.critical(self.update_tree.__name__)

        index = self.combobox_documents.current()
        self.document = list(self.tree)[index]
        print(self.document)


        self.listbox_outline.delete(0, tk.END)
        self.text_items.delete('1.0', 'end')
        for item in self.document.items:

            # TODO: make this part of the Item class and use in report.py
            level = '.'.join(str(l) for l in item.level)
            if level.endswith('.0') and len(level) > 3:
                level = level[:-2]

            indent = '  ' * (item.depth - 1)

            # TODO: determine a way to do this dynamically
            # width = self.listbox_outline.cget('width')
            width = self.listbox_outline.cget('width')
            value = indent + level + ' '
            while (len(value) + len(item.id)) < width:
                value += ' '
            value += item.id



            self.listbox_outline.insert(tk.END, value)



            chars = (item.text or item.ref or '???') + '\n\n'
            self.text_items.insert('end', chars)


        self.listbox_outline.selection_set(item_index)
        identifier = self.listbox_outline.selection_get()
        self.stringvar_item.set(identifier)  # manual call





    def update_document(self, *args):
        logging.critical(self.update_document.__name__)
        print(self.stringvar_item.get())

        self.ignore = True

        value = self.stringvar_item.get()
        identifier = value.rsplit(' ', 1)[-1]
        self.item = self.tree.find_item(identifier)

        self.text_item.replace('1.0', 'end', self.item.text)

        self.intvar_active.set(self.item.active)
        self.intvar_derived.set(self.item.derived)
        self.intvar_normative.set(self.item.normative)
        self.intvar_heading.set(self.item.heading)


        self.text_parents.delete('1.0', 'end')
        for identifier in self.item.links:
            item = self.tree.find_item(identifier)
            chars = (item.text or item.ref or '???') + '\n\n'
            self.text_parents.insert('end', chars)

        self.text_children.delete('1.0', 'end')
        identifiers = self.item.find_rlinks(self.document, self.tree)[0]
        for identifier in identifiers:
            item = self.tree.find_item(identifier)
            chars = (item.text or item.ref or '???') + '\n\n'
            self.text_children.insert('end', chars)

        self.ignore = False


    def update_item(self, *args):
        logging.critical(self.update_item.__name__)

        if self.ignore:
            return

        self.item.auto = False
        self.item.text = self.stringvar_text.get()
        self.item.active = self.intvar_active.get()
        self.item.derived = self.intvar_derived.get()
        self.item.normative = self.intvar_normative.get()
        self.item.heading = self.intvar_heading.get()
        self.item.save()

        index = self.listbox_outline.curselection()[0]
        self.update_tree(item_index=index)

    def browse(self):
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


if __name__ == '__main__':  # pragma: no cover - manual test
    main()
