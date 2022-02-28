# SPDX-License-Identifier: LGPL-3.0-only

"""Unit test helper functions to reduce code duplication."""

# pylint: disable=unused-argument,protected-access

import os


def getWalk(walk_path):
    # Get the exported tree.
    walk = ""
    for root, _, files in os.walk(walk_path):
        level = root.replace(walk_path, "").count(os.sep)
        indent = " " * 4 * (level)
        walk = walk + "{}{}/\n".format(indent, os.path.basename(root))
        subindent = " " * 4 * (level + 1)
        for f in files:
            walk = walk + "{}{}\n".format(subindent, f)
    return walk


def getLines(gen):
    # Get the generated lines.
    result = ""
    for line in gen:
        result = result + line + "\n"
    return result
