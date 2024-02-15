# SPDX-License-Identifier: LGPL-3.0-only
# pylint: disable=unused-argument,protected-access

"""Unit test helper functions to reduce code duplication."""
from logging import NullHandler
from os import chmod
from shutil import copytree
from stat import S_IWRITE
from time import sleep
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


def on_error_with_retry(func, path, exc_info, retries=60):
    """Define a separate function to handle errors for rmtree.

    This callback function is used to retry rmtree operations
    that fail for up to 60 seconds. This is necessary because
    Windows does not always release file handles immediately,
    and the rmtree operation can fail.
    """
    if retries > 0:
        # Change the file permissions
        chmod(path, S_IWRITE)
        # Sleep for 1 seconds to wait for the race condition to resolve
        sleep(1)
        try:
            # Try the operation again
            func(path)
        # pylint: disable=broad-except
        except Exception as e:
            # If an error occurs, recurse with one fewer retry available
            print(f"Retry {5 - retries} failed for {path}, error: {e}. Retrying...")
            on_error_with_retry(func, path, exc_info, retries - 1)
    else:
        # If no retries are left, raise an exception or handle the final failure case
        print(f"Failed to remove {path} after multiple retries.")
