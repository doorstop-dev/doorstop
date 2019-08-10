# SPDX-License-Identifier: LGPL-3.0-only

"""Plug-in module to store requirements in a Subversion (1.7) repository."""

import os

from doorstop import common
from doorstop.core.vcs.base import BaseWorkingCopy

log = common.logger(__name__)


class WorkingCopy(BaseWorkingCopy):
    """Subversion working copy."""

    DIRECTORY = '.svn'
    IGNORES = ('.sgignores', '.vvignores')

    def lock(self, path):
        self.call('svn', 'update')
        self.call('svn', 'lock', path)

    def edit(self, path):
        log.debug("`svn` adds all changes")

    def add(self, path):
        self.call('svn', 'add', path)

    def delete(self, path):
        self.call('svn', 'delete', path)

    def commit(self, message=None):
        message = message or input("Commit message: ")
        self.call('svn', 'commit', '--message', message)

    @property
    def ignores(self):
        if self._ignores_cache is None:
            self._ignores_cache = []
            os.chdir(self.path)
            for line in self.call(
                'svn', 'pg', '-R', 'svn:ignore', '.', return_stdout=True
            ).splitlines():
                self._ignores_cache.append(line)
        return self._ignores_cache
