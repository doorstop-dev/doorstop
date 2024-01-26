# SPDX-License-Identifier: LGPL-3.0-only
# pylint: disable=unused-argument,protected-access

"""Unit test helper functions to reduce code duplication."""
from logging import NullHandler
from shutil import copytree
from typing import List

from doorstop.core.builder import build
from doorstop.core.tests import ROOT


class ListLogHandler(NullHandler):
    """Create a log handler for asserting log calls."""

    def __init__(self, log):
        super().__init__()
        self.records: List[str] = []
        self.log = log

    def __enter__(self):
        self.log.addHandler(self)
        return self

    def __exit__(self, kind, value, traceback):
        self.log.removeHandler(self)

    def handle(self, record):
        self.records.append(str(record.msg))


def build_expensive_tree(obj):
    # Build a tree.
    copytree(ROOT, obj.datapath)
    obj.mock_tree = build(cwd=obj.datapath, root=obj.datapath, request_next_number=None)
