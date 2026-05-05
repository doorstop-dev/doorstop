# SPDX-License-Identifier: LGPL-3.0-only
# pylint: disable=unused-argument,protected-access

"""Unit test helper functions to reduce code duplication."""

import time
from logging import NullHandler
from os import chmod
from shutil import copytree, ignore_patterns
from stat import S_IWRITE
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
    """
    Build a complete test tree by copying the entire repository.

    Creates a temporary copy of ROOT for tests that modify the document tree.
    Ignores cache files, mock directories, and version control artifacts to
    avoid copying errors (e.g., broken symlinks in VSCode worktrees).

    Args:
        obj: Test object with 'datapath' attribute; sets obj.mock_tree
    """
    copytree(
        ROOT,
        obj.datapath,
        ignore=ignore_patterns(
            "mock_test_publisher_*",  # Ignore mock directories
            ".pytest_cache",  # Ignore pytest cache
            "__pycache__",  # Ignore Python cache
            "*.pyc",  # Ignore compiled Python files
            ".git",  # Ignore .git directory (NOT .git*)
            ".gitignore",  # Ignore .gitignore
            ".gitattributes",  # Ignore .gitattributes
            ".venv",
            "venv",  # Ignore virtual environments (NOT .venv*)
            "htmlcov",  # Ignore coverage reports
            ".coverage",  # Ignore coverage data (NOT .coverage*)
            "*.egg-info",  # Ignore package metadata
        ),
    )
    obj.mock_tree = build(cwd=obj.datapath, root=obj.datapath, request_next_number=None)


def on_error_with_retry(func, path, exc_info, max_retries=10, max_time=5):
    """Define a separate function to handle errors for rmtree.

    This callback function is used to retry rmtree operations
    that fail for up to max_time seconds. This is necessary because
    Windows does not always release file handles immediately,
    and the rmtree operation can fail.
    """

    start_time = time.time()

    for attempt in range(max_retries):
        elapsed = time.time() - start_time

        # Timeout check
        if elapsed >= max_time:
            print(f"Timeout: Failed to remove {path} after {elapsed:.1f}s. Giving up.")
            return

        # Change the file permissions
        try:
            chmod(path, S_IWRITE)
        except Exception:
            pass  # Ignore chmod failures

        # Sleep briefly
        time.sleep(0.2)

        try:
            # Try the operation again
            func(path)
            return  # Success!
        except Exception as e:
            print(f"Retry {attempt + 1}/{max_retries} failed for {path}, error: {e}")
            # Continue to next attempt

    # All retries exhausted
    elapsed = time.time() - start_time
    print(
        f"Failed to remove {path} after {attempt + 1} retries ({elapsed:.1f}s). Giving up."
    )
