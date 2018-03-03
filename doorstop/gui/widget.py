#!/usr/bin/env python

"""Graphical Widget creator and controller for doorstop."""

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

# # Fonts
fontNormal = font.Font(family='TkDefaultFont', size=1)
fontFixed = font.Font(family='Courier New', size=1)

# # Styles (http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/ttk-style-layer.html)

# Style for Button
styleDsTButton = ttk.Style()
styleDsTButton.configure('ds.TButton', font=fontNormal)

# Style for Checkbutton
styleDsTCheckbutton = ttk.Style()
styleDsTCheckbutton.configure('ds.TCheckbutton', font=fontNormal)

# Style for Combobox
styleDsTCombobox = ttk.Style()
styleDsTCombobox.configure('ds.TCombobox', font=fontNormal)

# Style for Entry
styleDsTEntry = ttk.Style()
styleDsTEntry.configure('ds.TEntry', font=fontNormal)

# Style for Frame
styleDsTFrame = ttk.Style()
styleDsTFrame.configure('ds.TFrame', font=fontNormal)

# Style for Label
styleDsTLabel = ttk.Style()
styleDsTLabel.configure('ds.TLabel', font=fontNormal)

# Style for LabelFrame
styleDsTLabelFrame = ttk.Style()
styleDsTLabelFrame.configure('ds.TLabelFrame', font=fontNormal)

# Style for Menubutton
styleDsTMenubutton = ttk.Style()
styleDsTMenubutton.configure('ds.TMenubutton', font=fontNormal)

# Style for Notebook
styleDsTNotebook = ttk.Style()
styleDsTNotebook.configure('ds.TNotebook', font=fontNormal)

# Style for PanedWindow
styleDsTPanedwindow = ttk.Style()
styleDsTPanedwindow.configure('ds.TPanedwindow', font=fontNormal)

# Style for Progressbar
styleDsHorizontalTProgressbar = ttk.Style()
styleDsHorizontalTProgressbar.configure('ds.Horizontal.TProgressbar', font=fontNormal)
styleDsVerticalTProgressbar = ttk.Style()
styleDsVerticalTProgressbar.configure('ds.Vertical.TProgressbar', font=fontNormal)

# Style for Radiobutton
styleDsTRadiobutton = ttk.Style()
styleDsTRadiobutton.configure('ds.TRadiobutton', font=fontNormal)

# Style for Scale
styleDsHorizontalTScale = ttk.Style()
styleDsHorizontalTScale.configure('ds.Horizontal.TScale', font=fontNormal)
styleDsVerticalTScale = ttk.Style()
styleDsVerticalTScale.configure('ds.Vertical.TScale', font=fontNormal)

# Style for Scrollbar
styleDsHorizontalTScrollbar = ttk.Style()
styleDsHorizontalTScrollbar.configure('ds.Horizontal.TScrollbar', font=fontNormal)
styleDsVerticalTScrollbar = ttk.Style()
styleDsVerticalTScrollbar.configure('ds.Vertical.TScrollbar', font=fontNormal)

# Style for Separator
styleDsTSeparator = ttk.Style()
styleDsTSeparator.configure('ds.TSeparator', font=fontNormal)

# Style for Sizegrip
styleDsTSizegrip = ttk.Style()
styleDsTSizegrip.configure('ds.TSizegrip', font=fontNormal)

# Style for Treeview
styleDsTreeview = ttk.Style()
styleDsTreeview.configure('ds.Treeview', font=fontNormal)

# # Widget


class _Listbox2(tk.Listbox):  # pragma: no cover (manual test), pylint: disable=R0901
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


def Button(parent, **extra):
    result = ttk.Button(parent, **extra, style="ds.TButton")
    return result


def Checkbutton(parent, **extra):
    result = ttk.Checkbutton(parent, **extra, style="ds.TCheckbutton")
    return result


def Combobox(parent, **extra):
    result = ttk.Combobox(parent, font=fontNormal, **extra)
    return result


def Label(parent, **extra):
    result = ttk.Label(parent, **extra)
    result.configure(font=fontNormal)
    return result


def Listbox(parent, **extra):
    result = tk.Listbox(parent, **extra)
    result.configure(font=fontNormal)
    return result


def Listbox2(parent, **extra):
    result = _Listbox2(parent, **extra)
    result.configure(font=fontNormal)
    return result


def Entry(parent, **extra):
    result = ttk.Entry(parent, **extra, font=fontFixed)
    return result


def Text(parent, **extra):
    result = tk.Text(parent, font=fontFixed, **extra)
    return result
    

def Tk(root, **extra):
    resetFontSize()
    root.option_add('*TCombobox*Listbox.font', fontNormal)

# Manage font size.


def adjustFontSize(fontSizeDelta: int) -> None:
    for currFont in [fontNormal, fontFixed]:
        if 0 >= abs(currFont["size"]) + fontSizeDelta:
            return
        else:
            currFont.configure(size=max(1, abs(currFont["size"]) + fontSizeDelta))


def resetFontSize() -> None:
    # Shared style
    if sys.platform == 'darwin':
        initsize = 14
    else:
        initsize = 10
    for currFont in [fontNormal, fontFixed]:
        currFont.configure(size=max(1, initsize))
