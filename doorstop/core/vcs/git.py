# SPDX-License-Identifier: LGPL-3.0-only

"""Plug-in module to store requirements in a Git repository."""

from typing import List

from doorstop import common
from doorstop.core.vcs.base import BaseWorkingCopy

log = common.logger(__name__)


class WorkingCopy(BaseWorkingCopy):
    """Git working copy."""

    DIRECTORY = ".git"
    IGNORES = (".gitignore",)
    # characters of paths per call, below the Windows command-line limit (32767)
    MAX_CHARS = 30000

    def lock(self, path):
        log.debug("`git` does not support locking: %s", path)
        self.call("git", "pull")

    def edit(self, path):
        self.call("git", "add", self.relpath(path))

    def edit_many(self, paths):
        chunk: List[str] = []
        size = 0
        for name in map(self.relpath, paths):
            cost = len(name) + 3  # separator and quotes around paths with spaces
            if chunk and size + cost > self.MAX_CHARS:
                self.call("git", "add", "--", *chunk)
                chunk, size = [], 0
            chunk.append(name)
            size += cost
        if chunk:
            self.call("git", "add", "--", *chunk)

    def add(self, path):
        self.call("git", "add", self.relpath(path))

    def delete(self, path):
        self.call("git", "rm", self.relpath(path), "--force", "--quiet")

    def commit(self, message=None):
        message = message or input("Commit message: ")
        self.call("git", "commit", "--all", "--message", message)
        self.call("git", "push")
