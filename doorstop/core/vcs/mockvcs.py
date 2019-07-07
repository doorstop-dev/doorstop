# SPDX-License-Identifier: LGPL-3.0-only

"""Plug-in module to simulate the storage of requirements in a repository."""
import os

from doorstop import common
from doorstop.core.vcs.base import BaseWorkingCopy

log = common.logger(__name__)


class WorkingCopy(BaseWorkingCopy):
    """Simulated working copy."""

    DIRECTORY = '.mockvcs'

    def __init__(self, path):
        super().__init__(path)
        self._ignores_cache = ["*/env/*", "*/apidocs/*", "*/build/lib/*"]

    def lock(self, path):
        log.debug("$ simulated lock on: {}...".format(path))

    def edit(self, path):
        log.debug("$ simulated edit on: {}...".format(path))

    def add(self, path):
        log.debug("$ simulated add on: {}...".format(path))

    def delete(self, path):
        os.remove(path)
        log.debug("$ Deleted {}...".format(path))

    def commit(self, message=None):
        log.debug("$ simulated commit")
