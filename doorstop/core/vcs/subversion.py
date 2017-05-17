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

    def commit(self, path, message=None, username=None, password=None):
        args = ['svn', 'commit', '--non-interactive', '--message', message]
        if username:
            args.extend(['--username', username])
        if password:
            args.extend(['--password', password])
        args.append(path)
        return self.call(*args, return_stdout=True)

    @property
    def ignores(self):  # pragma: no cover (manual test)
        if self._ignores_cache is None:
            self._ignores_cache = []
            os.chdir(self.path)
            for line in self.call('svn', 'pg', '-R', 'svn:ignore', '.',
                                  return_stdout=True).splitlines():
                self._ignores_cache.append(line)
        return self._ignores_cache
