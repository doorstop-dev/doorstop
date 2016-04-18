#!/usr/bin/env python

"""Graphical interface for Doorstop."""

import sys
from unittest.mock import Mock
try:  # pragma: no cover (manual test)
    import tkinter as tk
    from tkinter import ttk
    from tkinter import font, filedialog
except ImportError as _exc:  # pragma: no cover (manual test)
    sys.stderr.write("WARNING: {}\n".format(_exc))
    tk = Mock()
    ttk = Mock()
import os
import argparse
import functools
from itertools import chain
import logging

from doorstop import common
from doorstop.common import HelpFormatter, WarningFormatter, DoorstopError
from doorstop.core import vcs
from doorstop.core import builder
from doorstop import settings

log = common.logger(__name__)


def main(args=None):
    """Process command-line arguments and run the program."""
    from doorstop import GUI, VERSION

    # Shared options
    debug = argparse.ArgumentParser(add_help=False)
    debug.add_argument('-V', '--version', action='version', version=VERSION)
    debug.add_argument('-v', '--verbose', action='count', default=0,
                       help="enable verbose logging")
    shared = {'formatter_class': HelpFormatter, 'parents': [debug]}
    parser = argparse.ArgumentParser(prog=GUI, description=__doc__, **shared)

    # Build main parser
    parser.add_argument('-j', '--project', metavar="PATH",
                        help="path to the root of the project")

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
    else:
        log.debug("program exited with error")
        sys.exit(1)


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

    else:  # pragma: no cover (manual test)

        root = tk.Tk()
        root.title("{} ({})".format(__project__, __version__))
        app = Application(root, cwd, args.project)
        root.update()
        root.minsize(root.winfo_width(), root.winfo_height())
        app.mainloop()

        return True


def _log(func):  # pragma: no cover (manual test)
    """Decorator for methods that should log calls."""
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        """Wrapped method to log name and arguments."""
        sargs = "{}, {}".format(', '.join(repr(a) for a in args),
                                ', '.join("{}={}".format(k, repr(v))
                                          for k, v in kwargs.items()))
        msg = "log: {}: {}".format(func.__name__, sargs.strip(", "))
        if not isinstance(self, ttk.Frame) or not self.ignore:
            log.debug(msg.strip())
        return func(self, *args, **kwargs)
    return wrapped


class Listbox2(tk.Listbox):  # pragma: no cover (manual test), pylint: disable=R0901
    """Listbox class with automatic width adjustment."""

    def autowidth(self, maxwidth=250):
        """Resize the widget width to fit contents."""
        fnt = font.Font(font=self.cget("font"))
        pixels = 0
        for item in self.get(0, "end"):
            pixels = max(pixels, fnt.measure(item))
        # bump listbox size until all entries fit
        pixels = pixels + 10
        width = int(self.cget("width"))
        for shift in range(0, maxwidth + 1, 5):
            if self.winfo_reqwidth() >= pixels:
                break
            self.config(width=width + shift)


class Application(ttk.Frame):  # pragma: no cover (manual test), pylint: disable=R0901,R0902
    """Graphical application for Doorstop."""

    def __init__(self, root, cwd, project):
        ttk.Frame.__init__(self, root)

        # Create Doorstop variables
        self.cwd = cwd
        self.tree = None
        self.document = None
        self.item = None
        self.index = None

        # Create string variables
        self.stringvar_project = tk.StringVar(value=project or '')
        self.stringvar_project.trace('w', self.display_tree)
        self.stringvar_document = tk.StringVar()
        self.stringvar_document.trace('w', self.display_document)
        self.stringvar_item = tk.StringVar()
        self.stringvar_item.trace('w', self.display_item)
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
        self.stringvar_link = tk.StringVar()  # no trace event
        self.stringvar_ref = tk.StringVar()
        self.stringvar_ref.trace('w', self.update_item)
        self.stringvar_extendedkey = tk.StringVar()
        self.stringvar_extendedkey.trace('w', self.display_extended)
        self.stringvar_extendedvalue = tk.StringVar()
        self.stringvar_extendedvalue.trace('w', self.update_item)

        # Create widget variables
        self.combobox_documents = None
        self.listbox_outline = None
        self.text_items = None
        self.text_item = None
        self.listbox_links = None
        self.combobox_extended = None
        self.text_extendedvalue = None
        self.text_parents = None
        self.text_children = None

        # Initialize the GUI
        self.ignore = False  # flag to ignore internal events
        frame = self.init(root)
        frame.pack(fill=tk.BOTH, expand=1)

        # Start the application
        root.after(500, self.find)

    def init(self, root):  # pylint: disable=R0912,R0914
        """Initialize and return the main frame."""  # pylint: disable=C0301
        # Shared arguments
        width_outline = 20
        width_text = 30
        width_code = 30
        width_uid = 10
        height_text = 10
        height_ext = 5
        height_code = 3

        # Shared keyword arguments
        kw_f = {'padding': 5}  # constructor arguments for frames
        kw_gp = {'padx': 2, 'pady': 2}  # grid arguments for padded widgets
        kw_gs = {'sticky': tk.NSEW}  # grid arguments for sticky widgets
        kw_gsp = dict(chain(kw_gs.items(), kw_gp.items()))  # grid arguments for sticky padded widgets

        # Shared style
        if sys.platform == 'darwin':
            size = 14
        else:
            size = 10
        normal = font.Font(family='TkDefaultFont', size=size)
        fixed = font.Font(family='Courier New', size=size)

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

            # Place widgets
            ttk.Label(frame, text="Project:").grid(row=0, column=0, **kw_gp)
            ttk.Entry(frame, textvariable=self.stringvar_project).grid(row=0, column=1, **kw_gsp)

            return frame

        def frame_tree(root):
            """Frame for the current document."""
            # Configure grid
            frame = ttk.Frame(root, **kw_f)
            frame.rowconfigure(0, weight=1)
            frame.columnconfigure(0, weight=0)
            frame.columnconfigure(1, weight=1)

            # Place widgets
            ttk.Label(frame, text="Document:").grid(row=0, column=0, **kw_gp)
            self.combobox_documents = ttk.Combobox(frame, textvariable=self.stringvar_document, state='readonly')
            self.combobox_documents.grid(row=0, column=1, **kw_gsp)

            return frame

        def frame_document(root):
            """Frame for current document's outline and items."""
            # Configure grid
            frame = ttk.Frame(root, **kw_f)
            frame.rowconfigure(0, weight=0)
            frame.rowconfigure(1, weight=5)
            frame.rowconfigure(2, weight=0)
            frame.rowconfigure(3, weight=0)
            frame.columnconfigure(0, weight=0)
            frame.columnconfigure(1, weight=0)
            frame.columnconfigure(2, weight=0)
            frame.columnconfigure(3, weight=0)
            frame.columnconfigure(4, weight=1)
            frame.columnconfigure(5, weight=1)

            @_log
            def listbox_outline_listboxselect(event):
                """Callback for selecting an item."""
                if self.ignore:
                    return
                widget = event.widget
                curselection = widget.curselection()
                if curselection:
                    index = int(curselection[0])
                    value = widget.get(index)
                    self.stringvar_item.set(value)

            # Place widgets
            ttk.Label(frame, text="Outline:").grid(row=0, column=0, columnspan=4, sticky=tk.W, **kw_gp)
            ttk.Label(frame, text="Items:").grid(row=0, column=4, columnspan=2, sticky=tk.W, **kw_gp)
            self.listbox_outline = Listbox2(frame, width=width_outline, font=normal)
            self.listbox_outline.bind('<<ListboxSelect>>', listbox_outline_listboxselect)
            self.listbox_outline.grid(row=1, column=0, columnspan=4, **kw_gsp)
            self.text_items = tk.Text(frame, width=width_text, wrap=tk.WORD, font=normal)
            self.text_items.grid(row=1, column=4, columnspan=2, **kw_gsp)
            ttk.Button(frame, text="<", width=0, command=self.left).grid(row=2, column=0, sticky=tk.EW, padx=(2, 0))
            ttk.Button(frame, text="v", width=0, command=self.down).grid(row=2, column=1, sticky=tk.EW)
            ttk.Button(frame, text="^", width=0, command=self.up).grid(row=2, column=2, sticky=tk.EW)
            ttk.Button(frame, text=">", width=0, command=self.right).grid(row=2, column=3, sticky=tk.EW, padx=(0, 2))
            ttk.Button(frame, text="Add Item", command=self.add).grid(row=2, column=4, sticky=tk.W, **kw_gp)
            ttk.Button(frame, text="Remove Selected Item", command=self.remove).grid(row=2, column=5, sticky=tk.E, **kw_gp)

            return frame

        def frame_item(root):
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

            @_log
            def text_focusin(_):
                """Callback for entering a text field."""
                self.ignore = True

            @_log
            def text_item_focusout(event):
                """Callback for updating text."""
                self.ignore = False
                widget = event.widget
                value = widget.get('1.0', 'end')
                self.stringvar_text.set(value)

            @_log
            def text_extendedvalue_focusout(event):
                """Callback for updating extended attributes."""
                self.ignore = False
                widget = event.widget
                value = widget.get('1.0', 'end')
                self.stringvar_extendedvalue.set(value)

            # Place widgets
            ttk.Label(frame, text="Selected Item:").grid(row=0, column=0, columnspan=3, sticky=tk.W, **kw_gp)
            self.text_item = tk.Text(frame, width=width_text, height=height_text, wrap=tk.WORD, font=fixed)
            self.text_item.bind('<FocusIn>', text_focusin)
            self.text_item.bind('<FocusOut>', text_item_focusout)
            self.text_item.grid(row=1, column=0, columnspan=3, **kw_gsp)
            ttk.Label(frame, text="Properties:").grid(row=2, column=0, sticky=tk.W, **kw_gp)
            ttk.Label(frame, text="Links:").grid(row=2, column=1, columnspan=2, sticky=tk.W, **kw_gp)
            ttk.Checkbutton(frame, text="Active", variable=self.intvar_active).grid(row=3, column=0, sticky=tk.W, **kw_gp)
            self.listbox_links = tk.Listbox(frame, width=width_uid, height=6)
            self.listbox_links.grid(row=3, column=1, rowspan=4, **kw_gsp)
            ttk.Entry(frame, width=width_uid, textvariable=self.stringvar_link).grid(row=3, column=2, sticky=tk.EW + tk.N, **kw_gp)
            ttk.Checkbutton(frame, text="Derived", variable=self.intvar_derived).grid(row=4, column=0, sticky=tk.W, **kw_gp)
            ttk.Button(frame, text="<< Link Item", command=self.link).grid(row=4, column=2, **kw_gp)
            ttk.Checkbutton(frame, text="Normative", variable=self.intvar_normative).grid(row=5, column=0, sticky=tk.W, **kw_gp)
            ttk.Checkbutton(frame, text="Heading", variable=self.intvar_heading).grid(row=6, column=0, sticky=tk.W, **kw_gp)
            ttk.Button(frame, text=">> Unlink Item", command=self.unlink).grid(row=6, column=2, **kw_gp)
            ttk.Label(frame, text="External Reference:").grid(row=7, column=0, columnspan=3, sticky=tk.W, **kw_gp)
            ttk.Entry(frame, width=width_text, textvariable=self.stringvar_ref, font=fixed).grid(row=8, column=0, columnspan=3, **kw_gsp)
            ttk.Label(frame, text="Extended Attributes:").grid(row=9, column=0, columnspan=3, sticky=tk.W, **kw_gp)
            self.combobox_extended = ttk.Combobox(frame, textvariable=self.stringvar_extendedkey, font=fixed)
            self.combobox_extended.grid(row=10, column=0, columnspan=3, **kw_gsp)
            self.text_extendedvalue = tk.Text(frame, width=width_text, height=height_ext, wrap=tk.WORD, font=fixed)
            self.text_extendedvalue.bind('<FocusIn>', text_focusin)
            self.text_extendedvalue.bind('<FocusOut>', text_extendedvalue_focusout)
            self.text_extendedvalue.grid(row=11, column=0, columnspan=3, **kw_gsp)

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
            self.text_parents = tk.Text(frame, width=width_text, wrap=tk.WORD, font=normal)
            self.text_parents.grid(row=1, column=0, **kw_gsp)
            ttk.Label(frame, text="Linked From:").grid(row=2, column=0, sticky=tk.W, **kw_gp)
            self.text_children = tk.Text(frame, width=width_text, wrap=tk.WORD, font=normal)
            self.text_children.grid(row=3, column=0, **kw_gsp)

            return frame

        # Place widgets
        frame_project(frame).grid(row=0, column=0, columnspan=2, **kw_gs)
        frame_tree(frame).grid(row=0, column=2, columnspan=2, **kw_gs)
        frame_document(frame).grid(row=1, column=0, **kw_gs)
        frame_item(frame).grid(row=1, column=1, columnspan=2, **kw_gs)
        frame_family(frame).grid(row=1, column=3, **kw_gs)

        return frame

    @_log
    def find(self):
        """Find the root of the project."""
        if not self.stringvar_project.get():
            try:
                path = vcs.find_root(self.cwd)
            except DoorstopError as exc:
                log.error(exc)
            else:
                self.stringvar_project.set(path)

    @_log
    def browse(self):
        """Browse for the root of a project."""
        path = filedialog.askdirectory()
        log.debug("path: {}".format(path))
        if path:
            self.stringvar_project.set(path)

    @_log
    def display_tree(self, *_):
        """Display the currently selected tree."""
        # Set the current tree
        self.tree = builder.build(root=self.stringvar_project.get())
        log.info("displaying tree...")

        # Display the documents in the tree
        values = ["{} ({})".format(document.prefix, document.relpath)
                  for document in self.tree]
        self.combobox_documents['values'] = values

        # Select the first document
        if len(self.tree):
            self.combobox_documents.current(0)
        else:
            logging.warning("no documents to display")

    @_log
    def display_document(self, *_):
        """Display the currently selected document."""
        # Set the current document
        index = self.combobox_documents.current()
        self.document = list(self.tree)[index]
        log.info("displaying document {}...".format(self.document))

        # Display the items in the document
        self.listbox_outline.delete(0, tk.END)
        self.text_items.delete('1.0', 'end')
        for item in self.document.items:

            # Add the item to the document outline
            indent = '  ' * (item.depth - 1)
            level = '.'.join(str(l) for l in item.level)
            value = "{s}{l} {i}".format(s=indent, l=level, i=item.uid)
            level = '.'.join(str(l) for l in item.level)
            value = "{s}{l} {u}".format(s=indent, l=level, u=item.uid)
            value = "{s}{l} {i}".format(s=indent, l=item.level, i=item.uid)
            self.listbox_outline.insert(tk.END, value)

            # Add the item to the document text
            value = "{t} [{u}]\n\n".format(t=item.text or item.ref or '???',
                                           u=item.uid)
            self.text_items.insert('end', value)
        self.listbox_outline.autowidth()

        # Select the first item
        self.listbox_outline.selection_set(self.index or 0)
        identifier = self.listbox_outline.selection_get()
        self.stringvar_item.set(identifier)  # manual call
        self.listbox_outline.selection_set(self.index or 0)
        uid = self.listbox_outline.selection_get()
        self.stringvar_item.set(uid)  # manual call
        if len(self.document):
            self.listbox_outline.selection_set(self.index or 0)
            identifier = self.listbox_outline.selection_get()
            self.stringvar_item.set(identifier)  # manual call
        else:
            logging.warning("no items to display")

    @_log
    def display_item(self, *_):
        """Display the currently selected item."""
        self.ignore = True

        # Set the current item
        uid = self.stringvar_item.get().rsplit(' ', 1)[-1]
        self.item = self.tree.find_item(uid)
        self.index = int(self.listbox_outline.curselection()[0])
        log.info("displaying item {}...".format(self.item))

        # Display the item's text
        self.text_item.replace('1.0', 'end', self.item.text)

        # Display the item's properties
        self.stringvar_text.set(self.item.text)  # manual call
        self.intvar_active.set(self.item.active)
        self.intvar_derived.set(self.item.derived)
        self.intvar_normative.set(self.item.normative)
        self.intvar_heading.set(self.item.heading)

        # Display the item's links
        self.listbox_links.delete(0, tk.END)
        for uid in self.item.links:
            self.listbox_links.insert(tk.END, uid)
        self.stringvar_link.set('')

        # Display the item's external reference
        self.stringvar_ref.set(self.item.ref)

        # Display the item's extended attributes
        values = self.item.extended
        self.combobox_extended['values'] = values or ['']
        self.combobox_extended.current(0)

        # Display the items this item links to
        self.text_parents.delete('1.0', 'end')
        for uid in self.item.links:
            try:
                item = self.tree.find_item(uid)
            except DoorstopError:
                text = "???"
            else:
                text = item.text or item.ref or '???'
                uid = item.uid
            chars = "{t} [{u}]\n\n".format(t=text, u=uid)
            self.text_parents.insert('end', chars)

        # Display the items this item has links from
        self.text_children.delete('1.0', 'end')
        identifiers = self.item.find_child_links()
        for uid in identifiers:
            item = self.tree.find_item(uid)
            text = item.text or item.ref or '???'
            uid = item.uid
            chars = "{t} [{u}]\n\n".format(t=text, u=uid)
            self.text_children.insert('end', chars)

        self.ignore = False

    @_log
    def display_extended(self, *_):
        """Display the currently selected extended attribute."""
        self.ignore = True

        name = self.stringvar_extendedkey.get()
        log.debug("displaying extended attribute '{}'...".format(name))
        self.text_extendedvalue.replace('1.0', 'end', self.item.get(name, ''))

        self.ignore = False

    @_log
    def update_item(self, *_):
        """Update the current item from the fields."""
        if self.ignore:
            return
        if not self.item:
            logging.warning("no item selected")
            return

        # Update the current item
        log.info("updating {}...".format(self.item))
        self.item.auto = False
        self.item.text = self.stringvar_text.get()
        self.item.active = self.intvar_active.get()
        self.item.derived = self.intvar_derived.get()
        self.item.normative = self.intvar_normative.get()
        self.item.heading = self.intvar_heading.get()
        self.item.links = self.listbox_links.get(0, tk.END)
        self.item.ref = self.stringvar_ref.get()
        name = self.stringvar_extendedkey.get()
        if name:
            self.item.set(name, self.stringvar_extendedvalue.get())
        self.item.save()

        # Re-select this item
        self.display_document()

    @_log
    def left(self):
        """Dedent the current item's level."""
        self.item.level <<= 1
        self.document.reorder(keep=self.item)
        self.display_document()

    @_log
    def down(self):
        """Increment the current item's level."""
        self.item.level += 1
        self.document.reorder(keep=self.item)
        self.display_document()

    @_log
    def up(self):
        """Decrement the current item's level."""
        self.item.level -= 1
        self.document.reorder(keep=self.item)
        self.display_document()

    @_log
    def right(self):
        """Indent the current item's level."""
        self.item.level >>= 1
        self.document.reorder(keep=self.item)
        self.display_document()

    @_log
    def add(self):
        """Add a new item to the document."""
        logging.info("adding item to {}...".format(self.document))
        if self.item:
            level = self.item.level + 1
        else:
            level = None
        item = self.document.add_item(level=level)
        logging.info("added item: {}".format(item))
        self.index = self.document.items.index(item)
        self.display_document()

    @_log
    def remove(self):
        """Remove the selected item from the document."""
        logging.info("removing item {}...".format(self.item))
        item = self.tree.remove_item(self.item)
        logging.info("removed item: {}".format(item))
        self.item = None
        self.index = max(0, self.index - 1)
        self.display_document()

    @_log
    def link(self):
        """Add the specified link to the current item."""
        # Add the specified link to the list
        uid = self.stringvar_link.get()
        if uid:
            self.listbox_links.insert(tk.END, uid)
            self.stringvar_link.set('')

            # Update the current item
            self.update_item()

    @_log
    def unlink(self):
        """Remove the currently selected link from the current item."""
        # Remove the selected link from the list
        index = self.listbox_links.curselection()
        self.listbox_links.delete(index)

        # Update the current item
        self.update_item()


if __name__ == '__main__':  # pragma: no cover (manual test)
    main()
