# SPDX-License-Identifier: LGPL-3.0-only
# pylint: disable=unused-argument,protected-access

"""Unit test helper functions to reduce code duplication."""
from logging import NullHandler
from typing import List


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
