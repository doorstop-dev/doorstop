# SPDX-License-Identifier: LGPL-3.0-only

"""Unit test helper functions to reduce code duplication."""

# pylint: disable=unused-argument,protected-access

import os

LINES = """
initial: 1.2.3
outline:
        - REQ001: # Lorem ipsum d...
        - REQ003: # Unicode: -40° ±1%
        - REQ004: # Hello, world! !['..
        - REQ002: # Hello, world! !["...
        - REQ2-001: # Hello, world!
"""
YAML_CUSTOM_ATTRIBUTES = """
settings:
  digits: 3
  prefix: REQ
  sep: '-'
attributes:
  defaults:
  publish:
    - CUSTOM-ATTRIB
    - invented-by
"""


def getWalk(walk_path):
    # Get the exported tree.
    walk = []
    for root, _, files in sorted(os.walk(walk_path)):
        level = root.replace(walk_path, "").count(os.sep)
        indent = " " * 4 * (level)
        walk.append("{}{}/\n".format(indent, os.path.basename(root)))
        subindent = " " * 4 * (level + 1)
        for f in sorted(files):
            walk.append("{}{}\n".format(subindent, f))
    return "".join(line + "" for line in walk)


def getLines(gen):
    # Get the generated lines.
    result = ""
    for line in gen:
        result = result + line + "\n"
    return result


def getFileContents(file):
    """Return the contents of a file."""
    data = []
    with open(file, "r") as file_stream:
        data = file_stream.readlines()
    return data
