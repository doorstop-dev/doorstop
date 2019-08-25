#!/usr/bin/env python
# SPDX-License-Identifier: LGPL-3.0-only
# type: ignore

"""Graphical Widget creator and controller for doorstop."""

import sys
from unittest.mock import Mock

try:
    import tkinter as tk
    from tkinter import ttk
    from tkinter import font
except ImportError as _exc:
    sys.stderr.write("WARNING: {}\n".format(_exc))
    tk = Mock()
    ttk = Mock()

# # Styling
fontNormal = None
fontFixed = None
styleDsTButton = None
styleDsTCheckbutton = None
styleDsTCombobox = None
styleDsTEntry = None
styleDsTFrame = None
styleDsTLabel = None
styleDsTLabelFrame = None
styleDsTMenubutton = None
styleDsTNotebook = None
styleDsTPanedwindow = None
styleDsHorizontalTProgressbar = None
styleDsVerticalTProgressbar = None
styleDsTRadiobutton = None
styleDsHorizontalTScale = None
styleDsVerticalTScale = None
styleDsHorizontalTScrollbar = None
styleDsVerticalTScrollbar = None
styleDsTSeparator = None
styleDsTSizegrip = None
styleDsTreeview = None
styleDsTreeviewHeading = None

# # Widget


class _Listbox2(tk.Listbox):
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


def Button(parent, *args, **kwargs):
    result = ttk.Button(parent, *args, style="ds.TButton", **kwargs)
    return result


def Checkbutton(parent, *args, **kwargs):
    result = ttk.Checkbutton(parent, *args, style="ds.TCheckbutton", **kwargs)
    return result


def Combobox(parent, *args, **kwargs):
    result = ttk.Combobox(parent, *args, font=fontNormal, **kwargs)
    return result


def Label(parent, *args, **kwargs):
    result = ttk.Label(parent, *args, **kwargs)
    result.configure(font=fontNormal)
    return result


def Listbox(parent, *args, **kwargs):
    result = tk.Listbox(parent, *args, **kwargs)
    result.configure(font=fontNormal)
    return result


def Listbox2(parent, *args, **kwargs):
    result = _Listbox2(parent, *args, **kwargs)
    result.configure(font=fontNormal)
    return result


def Entry(parent, *args, **kwargs):
    result = ttk.Entry(parent, *args, font=fontFixed, **kwargs)
    return result


def Text(parent, *args, **kwargs):
    result = tk.Text(parent, *args, font=fontFixed, **kwargs)
    return result


def TreeView(parent, *args, **kwargs):
    result = ttk.Treeview(parent, *args, **kwargs)
    return result


def ScrollbarH(parent, *args, **kwargs):
    result = ttk.Scrollbar(
        parent, *args, orient="horizontal", style="ds.Horizontal.TScrollbar", **kwargs
    )
    return result


def ScrollbarV(parent, *args, **kwargs):
    result = ttk.Scrollbar(
        parent, *args, orient="vertical", style="ds.Vertical.TScrollbar", **kwargs
    )
    return result


def Tk():
    result = tk.Tk()

    # # Fonts
    global fontNormal
    fontNormal = font.Font(family='TkDefaultFont', size=1)
    global fontFixed
    fontFixed = font.Font(family='Courier New', size=1)

    # # Styles (http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/ttk-style-layer.html)

    # Style for Button
    global styleDsTButton
    styleDsTButton = ttk.Style()
    styleDsTButton.configure('ds.TButton', font=fontNormal)

    # Style for Checkbutton
    global styleDsTCheckbutton
    styleDsTCheckbutton = ttk.Style()
    styleDsTCheckbutton.configure('ds.TCheckbutton', font=fontNormal)

    # Style for Combobox
    global styleDsTCombobox
    styleDsTCombobox = ttk.Style()
    styleDsTCombobox.configure('ds.TCombobox', font=fontNormal)

    # Style for Entry
    global styleDsTEntry
    styleDsTEntry = ttk.Style()
    styleDsTEntry.configure('ds.TEntry', font=fontNormal)

    # Style for Frame
    global styleDsTFrame
    styleDsTFrame = ttk.Style()
    styleDsTFrame.configure('ds.TFrame', font=fontNormal)

    # Style for Label
    global styleDsTLabel
    styleDsTLabel = ttk.Style()
    styleDsTLabel.configure('ds.TLabel', font=fontNormal)

    # Style for LabelFrame
    global styleDsTLabelFrame
    styleDsTLabelFrame = ttk.Style()
    styleDsTLabelFrame.configure('ds.TLabelFrame', font=fontNormal)

    # Style for Menubutton
    global styleDsTMenubutton
    styleDsTMenubutton = ttk.Style()
    styleDsTMenubutton.configure('ds.TMenubutton', font=fontNormal)

    # Style for Notebook
    global styleDsTNotebook
    styleDsTNotebook = ttk.Style()
    styleDsTNotebook.configure('ds.TNotebook', font=fontNormal)

    # Style for PanedWindow
    global styleDsTPanedwindow
    styleDsTPanedwindow = ttk.Style()
    styleDsTPanedwindow.configure('ds.TPanedwindow', font=fontNormal)

    # Style for Progressbar
    global styleDsHorizontalTProgressbar
    styleDsHorizontalTProgressbar = ttk.Style()
    styleDsHorizontalTProgressbar.configure(
        'ds.Horizontal.TProgressbar', font=fontNormal
    )
    global styleDsVerticalTProgressbar
    styleDsVerticalTProgressbar = ttk.Style()
    styleDsVerticalTProgressbar.configure('ds.Vertical.TProgressbar', font=fontNormal)

    # Style for Radiobutton
    global styleDsTRadiobutton
    styleDsTRadiobutton = ttk.Style()
    styleDsTRadiobutton.configure('ds.TRadiobutton', font=fontNormal)

    # Style for Scale
    global styleDsHorizontalTScale
    styleDsHorizontalTScale = ttk.Style()
    styleDsHorizontalTScale.configure('ds.Horizontal.TScale', font=fontNormal)
    global styleDsVerticalTScale
    styleDsVerticalTScale = ttk.Style()
    styleDsVerticalTScale.configure('ds.Vertical.TScale', font=fontNormal)

    # Style for Scrollbar
    global styleDsHorizontalTScrollbar
    styleDsHorizontalTScrollbar = ttk.Style()
    styleDsHorizontalTScrollbar.configure('ds.Horizontal.TScrollbar', font=fontNormal)
    global styleDsVerticalTScrollbar
    styleDsVerticalTScrollbar = ttk.Style()
    styleDsVerticalTScrollbar.configure('ds.Vertical.TScrollbar', font=fontNormal)

    # Style for Separator
    global styleDsTSeparator
    styleDsTSeparator = ttk.Style()
    styleDsTSeparator.configure('ds.TSeparator', font=fontNormal)

    # Style for Sizegrip
    global styleDsTSizegrip
    styleDsTSizegrip = ttk.Style()
    styleDsTSizegrip.configure('ds.TSizegrip', font=fontNormal)

    # Style for Treeview
    global styleDsTreeview
    styleDsTreeview = ttk.Style()
    styleDsTreeview.configure("Treeview", font=fontNormal)

    global styleDsTreeviewHeading
    styleDsTreeviewHeading = ttk.Style()
    styleDsTreeviewHeading.configure("Treeview.Heading", font=fontNormal)

    resetFontSize()
    result.option_add('*TCombobox*Listbox.font', fontNormal)
    return result


# Manage font size.


def adjustFontSize(fontSizeDelta: int) -> None:
    for currFont in [fontNormal, fontFixed]:
        if abs(currFont["size"]) + fontSizeDelta <= 0:
            return
        else:
            currFont.configure(size=max(1, abs(currFont["size"]) + fontSizeDelta))
    styleDsTreeview.configure('Treeview', rowheight=fontNormal.metrics()['linespace'])


def resetFontSize() -> None:
    # Shared style
    if sys.platform == 'darwin':
        initsize = 14
    else:
        initsize = 10
    for currFont in [fontNormal, fontFixed]:
        currFont.configure(size=max(1, initsize))


def noUserInput_init(widget):
    widget.configure(state=tk.NORMAL)
    widget.bind('<1>', lambda event: widget.focus_set())
    widget.configure(state=tk.DISABLED)
    return widget


def noUserInput_delete(widget, *args, **kwargs):
    widget.configure(state=tk.NORMAL)
    widget.delete(*args, **kwargs)
    widget.configure(state=tk.DISABLED)


def noUserInput_insert(widget, *args, **kwargs):
    widget.configure(state=tk.NORMAL)
    widget.insert(*args, **kwargs)
    widget.configure(state=tk.DISABLED)
