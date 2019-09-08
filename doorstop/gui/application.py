#!/usr/bin/env python
# SPDX-License-Identifier: LGPL-3.0-only
# type: ignore

"""Graphical interface for Doorstop."""

import functools
import logging
import sys
from itertools import chain
from unittest.mock import Mock

from doorstop import common
from doorstop.common import DoorstopError
from doorstop.core import builder, vcs
from doorstop.gui import utilTkinter, widget

try:
    import tkinter as tk
    from tkinter import ttk
    from tkinter import filedialog
except ImportError as _exc:
    sys.stderr.write("WARNING: {}\n".format(_exc))
    tk = Mock()
    ttk = Mock()


log = common.logger(__name__)


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


class Application(ttk.Frame):
    """Graphical application for Doorstop."""

    def __init__(self, root, cwd, project):
        ttk.Frame.__init__(self, root)

        # Create Doorstop variables
        self.cwd = cwd
        self.tree = None
        self.document = None
        self.item = None

        # Create string variables
        self.stringvar_project = tk.StringVar(value=project or '')
        self.stringvar_project.trace('w', self.display_tree)
        self.stringvar_document = tk.StringVar()
        self.stringvar_document.trace('w', self.display_document)

        # The stringvar_item holds the uid of the main selected item (or empty string if nothing is selected).
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

    def init(self, root):
        """Initialize and return the main frame."""
        # pylint: disable=attribute-defined-outside-init

        # Shared arguments
        width_text = 30
        height_text = 10
        height_ext = 5

        # Shared keyword arguments
        kw_f = {'padding': 5}  # constructor arguments for frames
        kw_gp = {'padx': 2, 'pady': 2}  # grid arguments for padded widgets
        kw_gs = {'sticky': tk.NSEW}  # grid arguments for sticky widgets
        kw_gsp = dict(
            chain(kw_gs.items(), kw_gp.items())
        )  # grid arguments for sticky padded widgets

        root.bind_all("<Control-minus>", lambda arg: widget.adjustFontSize(-1))
        root.bind_all("<Control-equal>", lambda arg: widget.adjustFontSize(1))
        root.bind_all("<Control-0>", lambda arg: widget.resetFontSize())

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
            widget.Label(frame, text="Project:").grid(row=0, column=0, **kw_gp)
            widget.Entry(frame, textvariable=self.stringvar_project).grid(
                row=0, column=1, **kw_gsp
            )

            return frame

        def frame_tree(root):
            """Frame for the current document."""
            # Configure grid
            frame = ttk.Frame(root, **kw_f)
            frame.rowconfigure(0, weight=1)
            frame.columnconfigure(0, weight=0)
            frame.columnconfigure(1, weight=1)

            # Place widgets
            widget.Label(frame, text="Document:").grid(row=0, column=0, **kw_gp)
            self.combobox_documents = widget.Combobox(
                frame, textvariable=self.stringvar_document, state="readonly"
            )
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
            def treeview_outline_treeviewselect(event):
                """Handle selecting an item in the tree view."""
                if self.ignore:
                    return
                thewidget = event.widget
                curselection = thewidget.selection()
                if curselection:
                    uid = curselection[0]
                    self.stringvar_item.set(uid)

            @_log
            def treeview_outline_delete(event):  # pylint: disable=W0613
                """Handle deleting an item in the tree view."""
                if self.ignore:
                    return
                self.remove()

            # Place widgets
            widget.Label(frame, text="Outline:").grid(
                row=0, column=0, columnspan=4, sticky=tk.W, **kw_gp
            )
            widget.Label(frame, text="Items:").grid(
                row=0, column=4, columnspan=2, sticky=tk.W, **kw_gp
            )
            c_columnId = ("Id",)
            self.treeview_outline = widget.TreeView(frame, columns=c_columnId)
            for col in c_columnId:
                self.treeview_outline.heading(col, text=col)

            # Add a Vertical scrollbar to the Treeview Outline
            treeview_outline_verticalScrollBar = widget.ScrollbarV(
                frame, command=self.treeview_outline.yview
            )
            treeview_outline_verticalScrollBar.grid(
                row=1, column=0, columnspan=1, **kw_gs
            )
            self.treeview_outline.configure(
                yscrollcommand=treeview_outline_verticalScrollBar.set
            )

            self.treeview_outline.bind(
                "<<TreeviewSelect>>", treeview_outline_treeviewselect
            )
            self.treeview_outline.bind("<Delete>", treeview_outline_delete)
            self.treeview_outline.grid(row=1, column=1, columnspan=3, **kw_gsp)
            self.text_items = widget.noUserInput_init(
                widget.Text(frame, width=width_text, wrap=tk.WORD)
            )
            self.text_items.grid(row=1, column=4, columnspan=2, **kw_gsp)
            self.text_items_hyperlink = utilTkinter.HyperlinkManager(self.text_items)
            widget.Button(frame, text="<", width=0, command=self.left).grid(
                row=2, column=0, sticky=tk.EW, padx=(2, 0)
            )
            widget.Button(frame, text="v", width=0, command=self.down).grid(
                row=2, column=1, sticky=tk.EW
            )
            widget.Button(frame, text="^", width=0, command=self.up).grid(
                row=2, column=2, sticky=tk.EW
            )
            widget.Button(frame, text=">", width=0, command=self.right).grid(
                row=2, column=3, sticky=tk.EW, padx=(0, 2)
            )
            widget.Button(frame, text="Add Item", command=self.add).grid(
                row=2, column=4, sticky=tk.W, **kw_gp
            )
            widget.Button(frame, text="Remove Selected Item", command=self.remove).grid(
                row=2, column=5, sticky=tk.E, **kw_gp
            )

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
            frame.columnconfigure(0, weight=1, pad=kw_f['padding'] * 2)
            frame.columnconfigure(1, weight=1)

            @_log
            def text_focusin(_):
                """Handle entering a text field."""
                self.ignore = True

            @_log
            def text_item_focusout(event):
                """Handle updated text text."""
                self.ignore = False
                thewidget = event.widget
                value = thewidget.get('1.0', tk.END)
                self.stringvar_text.set(value)

            @_log
            def text_extendedvalue_focusout(event):
                """Handle updated extended attributes."""
                self.ignore = False
                thewidget = event.widget
                value = thewidget.get('1.0', tk.END)
                self.stringvar_extendedvalue.set(value)

            # Selected Item
            widget.Label(frame, text="Selected Item:").grid(
                row=0, column=0, columnspan=3, sticky=tk.W, **kw_gp
            )
            self.text_item = widget.Text(
                frame, width=width_text, height=height_text, wrap=tk.WORD
            )
            self.text_item.bind('<FocusIn>', text_focusin)
            self.text_item.bind('<FocusOut>', text_item_focusout)
            self.text_item.grid(row=1, column=0, columnspan=3, **kw_gsp)

            # Column: Properties
            self.create_properties_widget(frame).grid(
                row=2, rowspan=2, column=0, columnspan=2, sticky=tk.NSEW, **kw_gp
            )

            # Column: Links
            self.create_links_widget(frame).grid(
                row=4, rowspan=3, column=0, columnspan=2, sticky=tk.NSEW, **kw_gp
            )

            # External Reference
            self.create_reference_widget(frame).grid(
                row=7, rowspan=2, column=0, columnspan=2, sticky=tk.NSEW, **kw_gp
            )

            widget.Label(frame, text="Extended Attributes:").grid(
                row=9, column=0, columnspan=3, sticky=tk.W, **kw_gp
            )
            self.combobox_extended = widget.Combobox(
                frame, textvariable=self.stringvar_extendedkey
            )
            self.combobox_extended.grid(row=10, column=0, columnspan=3, **kw_gsp)
            self.text_extendedvalue = widget.Text(
                frame, width=width_text, height=height_ext, wrap=tk.WORD
            )
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
            widget.Label(frame, text="Linked To:").grid(
                row=0, column=0, sticky=tk.W, **kw_gp
            )
            self.text_parents = widget.noUserInput_init(
                widget.Text(frame, width=width_text, wrap=tk.WORD)
            )
            self.text_parents_hyperlink = utilTkinter.HyperlinkManager(
                self.text_parents
            )
            self.text_parents.grid(row=1, column=0, **kw_gsp)
            widget.Label(frame, text="Linked From:").grid(
                row=2, column=0, sticky=tk.W, **kw_gp
            )
            self.text_children = widget.noUserInput_init(
                widget.Text(frame, width=width_text, wrap=tk.WORD)
            )
            self.text_children_hyperlink = utilTkinter.HyperlinkManager(
                self.text_children
            )
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
        values = [
            "{} ({})".format(document.prefix, document.relpath)
            for document in self.tree
        ]
        self.combobox_documents['values'] = values

        # Select the first document
        if len(self.tree):  # pylint: disable=len-as-condition
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

        # Record the currently opened items.
        c_openItem = []
        for c_currUID in utilTkinter.getAllChildren(self.treeview_outline):
            if self.treeview_outline.item(c_currUID)["open"]:
                c_openItem.append(c_currUID)

        # Record the currently selected items.
        c_selectedItem = self.treeview_outline.selection()

        # Clear the widgets
        self.treeview_outline.delete(*self.treeview_outline.get_children())
        widget.noUserInput_delete(self.text_items, '1.0', tk.END)
        self.text_items_hyperlink.reset()

        # Display the items in the document
        c_levelsItem = [""]
        for item in self.document.items:
            theParent = next(
                iter(reversed([x for x in c_levelsItem[: item.depth]])), ""
            )

            while len(c_levelsItem) < item.depth:
                c_levelsItem.append(item.uid)
            c_levelsItem = c_levelsItem[: item.depth]
            for x in range(item.depth):
                c_levelsItem.append(item.uid)

            # Add the item to the document outline
            self.treeview_outline.insert(
                theParent,
                tk.END,
                item.uid,
                text=item.level,
                values=(item.uid,),
                open=item.uid in c_openItem,
            )

            # Add the item to the document text
            widget.noUserInput_insert(
                self.text_items, tk.END, "{t}".format(t=item.text or item.ref or '???')
            )
            widget.noUserInput_insert(self.text_items, tk.END, " [")
            widget.noUserInput_insert(
                self.text_items,
                tk.END,
                item.uid,
                self.text_items_hyperlink.add(
                    # pylint: disable=unnecessary-lambda
                    lambda c_theURL: self.followlink(c_theURL),
                    item.uid,
                    ["refLink"],
                ),
            )
            widget.noUserInput_insert(self.text_items, tk.END, "]\n\n")

        # Set tree view selection
        c_selectedItem = [
            x
            for x in c_selectedItem
            if x in utilTkinter.getAllChildren(self.treeview_outline)
        ]
        if c_selectedItem:
            # Restore selection
            self.treeview_outline.selection_set(c_selectedItem)
        else:
            # Select the first item
            for uid in utilTkinter.getAllChildren(self.treeview_outline):
                self.stringvar_item.set(uid)
                break
            else:
                logging.warning("no items to display")
                self.stringvar_item.set("")

    @_log
    def display_item(self, *_):
        """Display the currently selected item."""
        try:
            self.ignore = True

            # Fetch the current item
            uid = self.stringvar_item.get()
            if uid == "":
                self.item = None
            else:
                try:
                    self.item = self.tree.find_item(uid)
                except DoorstopError:
                    pass
            log.info("displaying item {}...".format(self.item))

            if uid != "":
                if uid not in self.treeview_outline.selection():
                    self.treeview_outline.selection_set((uid,))
                self.treeview_outline.see(uid)

            # Display the item's text
            self.text_item.replace(
                '1.0', tk.END, "" if self.item is None else self.item.text
            )

            # Display the item's properties
            self.stringvar_text.set("" if self.item is None else self.item.text)
            self.intvar_active.set(False if self.item is None else self.item.active)
            self.intvar_derived.set(False if self.item is None else self.item.derived)
            self.intvar_normative.set(
                False if self.item is None else self.item.normative
            )
            self.intvar_heading.set(False if self.item is None else self.item.heading)

            # Display the item's links
            self.listbox_links.delete(0, tk.END)
            if self.item is not None:
                for uid in self.item.links:
                    self.listbox_links.insert(tk.END, uid)
            self.stringvar_link.set('')

            # Display the item's external reference
            self.stringvar_ref.set("" if self.item is None else self.item.ref)

            # Display the item's extended attributes
            values = None if self.item is None else self.item.extended
            self.combobox_extended['values'] = values or ['']
            if self.item is not None:
                self.combobox_extended.current(0)

            # Display the items this item links to
            widget.noUserInput_delete(self.text_parents, '1.0', tk.END)
            self.text_parents_hyperlink.reset()
            if self.item is not None:
                for uid in self.item.links:
                    try:
                        item = self.tree.find_item(uid)
                    except DoorstopError:
                        text = "???"
                    else:
                        text = item.text or item.ref or '???'
                        uid = item.uid

                    widget.noUserInput_insert(
                        self.text_parents, tk.END, "{t}".format(t=text)
                    )
                    widget.noUserInput_insert(self.text_parents, tk.END, " [")
                    widget.noUserInput_insert(
                        self.text_parents,
                        tk.END,
                        uid,
                        self.text_parents_hyperlink.add(
                            # pylint: disable=unnecessary-lambda
                            lambda c_theURL: self.followlink(c_theURL),
                            uid,
                            ["refLink"],
                        ),
                    )
                    widget.noUserInput_insert(self.text_parents, tk.END, "]\n\n")

            # Display the items this item has links from
            widget.noUserInput_delete(self.text_children, '1.0', 'end')
            self.text_children_hyperlink.reset()
            if self.item is not None:
                for uid in self.item.find_child_links():
                    item = self.tree.find_item(uid)
                    text = item.text or item.ref or '???'
                    uid = item.uid

                    widget.noUserInput_insert(
                        self.text_children, tk.END, "{t}".format(t=text)
                    )
                    widget.noUserInput_insert(self.text_children, tk.END, " [")
                    widget.noUserInput_insert(
                        self.text_children,
                        tk.END,
                        uid,
                        self.text_children_hyperlink.add(
                            # pylint: disable=unnecessary-lambda
                            lambda c_theURL: self.followlink(c_theURL),
                            uid,
                            ["refLink"],
                        ),
                    )
                    widget.noUserInput_insert(self.text_children, tk.END, "]\n\n")
        finally:
            self.ignore = False

    @_log
    def display_extended(self, *_):
        """Display the currently selected extended attribute."""
        try:
            self.ignore = True

            name = self.stringvar_extendedkey.get()
            log.debug("displaying extended attribute '{}'...".format(name))
            self.text_extendedvalue.replace('1.0', tk.END, self.item.get(name, ""))
        finally:
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
        # Refresh the document view
        self.display_document()
        # Set the new selection
        self.stringvar_item.set(item.uid)

    @_log
    def remove(self):
        """Remove the selected item from the document."""
        newSelection = ""
        for c_currUID in self.treeview_outline.selection():
            # Find the item which should be selected once the current selection is removed.
            for currNeighbourStrategy in (
                self.treeview_outline.next,
                self.treeview_outline.prev,
                self.treeview_outline.parent,
            ):
                newSelection = currNeighbourStrategy(c_currUID)
                if newSelection != "":
                    break
            # Remove the item
            item = self.tree.find_item(c_currUID)
            logging.info("removing item {}...".format(item))
            item = self.tree.remove_item(item)
            logging.info("removed item: {}".format(item))
            # Set the new selection
            self.stringvar_item.set(newSelection)
            # Refresh the document view
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
        # Remove the selected link from the list (if selected)
        index = self.listbox_links.curselection()
        if not index:
            return
        self.listbox_links.delete(index)

        # Update the current item
        self.update_item()

    @_log
    def followlink(self, uid):
        """Display a given uid."""
        # Update the current item
        self.ignore = False
        self.update_item()

        # Load the good document.
        document = self.tree.find_document(uid.prefix)
        index = list(self.tree).index(document)
        self.combobox_documents.current(index)
        self.display_document()

        # load the good Item
        self.stringvar_item.set(uid)

    def create_properties_widget(self, parent):
        frame = ttk.Frame(parent)

        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        frame.rowconfigure(2, weight=1)
        frame.rowconfigure(3, weight=1)
        frame.rowconfigure(4, weight=1)

        widget.Label(frame, text="Properties:").grid(row=0, column=0, sticky=tk.NW)
        widget.Checkbutton(frame, text="Active", variable=self.intvar_active).grid(
            row=1, column=0, sticky=tk.NW
        )
        widget.Checkbutton(frame, text="Derived", variable=self.intvar_derived).grid(
            row=2, column=0, sticky=tk.NW
        )
        widget.Checkbutton(
            frame, text="Normative", variable=self.intvar_normative
        ).grid(row=3, column=0, sticky=tk.NW)
        widget.Checkbutton(frame, text="Heading", variable=self.intvar_heading).grid(
            row=4, column=0, sticky=tk.NW
        )

        return frame

    def create_links_widget(self, parent):
        frame = ttk.Frame(parent)

        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=0)
        frame.columnconfigure(3, weight=0)
        frame.rowconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        frame.rowconfigure(2, weight=1)

        width_uid = 10
        widget.Label(frame, text="Links:").grid(
            row=0, column=0, columnspan=1, sticky=tk.NW
        )
        widget.Entry(frame, textvariable=self.stringvar_link).grid(
            row=1, column=0, columnspan=2, sticky=tk.EW + tk.N
        )
        widget.Button(frame, text="+", command=self.link).grid(
            row=1, column=2, columnspan=1, sticky=tk.EW + tk.N
        )
        widget.Button(frame, text="-", command=self.unlink).grid(
            row=1, column=3, columnspan=1, sticky=tk.EW + tk.N
        )
        self.listbox_links = widget.Listbox(frame, width=width_uid)
        self.listbox_links.grid(
            row=2,
            column=0,
            rowspan=2,
            columnspan=4,
            padx=(3, 0),
            pady=(3, 0),
            sticky=tk.NSEW,
        )

        return frame

    def create_reference_widget(self, parent):
        frame = ttk.Frame(parent)

        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        widget.Label(frame, text="External Reference:").grid(
            row=0, column=0, sticky=tk.W
        )
        widget.Entry(frame, textvariable=self.stringvar_ref).grid(
            row=1, column=0, sticky=tk.NSEW
        )

        return frame
