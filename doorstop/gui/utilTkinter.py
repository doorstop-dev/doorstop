#!/usr/bin/env python
# SPDX-License-Identifier: LGPL-3.0-only
# type: ignore

import sys
from unittest.mock import Mock

try:
    import tkinter as tk
except ImportError as _exc:
    sys.stderr.write("WARNING: {}\n".format(_exc))
    tk = Mock()
    ttk = Mock()


class HyperlinkManager:
    def __init__(self, text) -> None:

        self.text = text

        self.text.tag_config("hyper", underline=True)

        self.text.tag_bind("hyper", "<Enter>", self._enter)
        self.text.tag_bind("hyper", "<Leave>", self._leave)
        self.text.tag_bind("hyper", "<Button-1>", self._click)

        self.reset()

    def reset(self):
        """Remove all hyperlinks."""
        self.links = {}

    def add(self, action, p_id, p_Tags=[]):  # pylint: disable=W0102
        """
        Add a new hyper link.

        @param action: method that will be called for this hyperlink
        @param p_id: the arbitration id that we are associating this action.
        """
        # add an action to the manager.  returns tags to use in
        # associated text widget
        thetags = []
        uniquetag = "hyper-%d" % len(self.links)
        thetags.extend(p_Tags)
        thetags.append("hyper")
        thetags.append(uniquetag)
        self.links[uniquetag] = [action, p_id]
        return tuple(thetags)

    def _enter(self, event):  # pylint: disable=W0613
        self.text.config(cursor="hand2")

    def _leave(self, event):  # pylint: disable=W0613
        self.text.config(cursor="")

    def _click(self, event):  # pylint: disable=W0613
        """If somebody clicks on the link it will find the method to call."""
        for tag in self.text.tag_names(tk.CURRENT):
            if tag[:6] == "hyper-":
                self.links[tag][0](self.links[tag][1])


def getAllChildren(treeView, item=None):
    """Recursive generator of all the children item of the provided ttk.Treeview."""
    for c_currUID in treeView.get_children(item):
        yield c_currUID
        yield from getAllChildren(treeView, c_currUID)
