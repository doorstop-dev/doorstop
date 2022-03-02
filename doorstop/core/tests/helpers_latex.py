# SPDX-License-Identifier: LGPL-3.0-only

"""Unit test helper functions to reduce code duplication."""

# pylint: disable=unused-argument,protected-access

import os

YAML_LATEX_DOC = """
settings:
  digits: 3
  prefix: REQ
  sep: '-'
attributes:
  defaults:
    doc:
      name: 'Tutorial'
      title: 'Development test document'
      ref: 'TUT-DS-22'
      by: 'Jng'
      major: 1
      minor: A
  publish:
    - CUSTOM-ATTRIB
    - invented-by
"""

YAML_LATEX_NO_DOC = """
settings:
  digits: 3
  prefix: TST
  sep: '-'
attributes:
  defaults:
    doc:
      name: ''
      title: ''
      ref: ''
      by: ''
      major: ''
      minor: ''
  publish:
    - CUSTOM-ATTRIB
"""

LINES = """
initial: 1.2.3
outline:
        - REQ001: # Lorem ipsum d...
        - REQ003: # Unicode: -40° ±1%
        - REQ004: # Hello, world! !['..
        - REQ002: # Hello, world! !["...
        - REQ2-001: # Hello, world!
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
