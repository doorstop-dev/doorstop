"""Plug-in module to store requirements in a Subversion (1.7) repository."""

import os

from doorstop.core.vcs.base import BaseWorkingCopy


class WorkingCopy(BaseWorkingCopy):  # pragma: no cover (integration test)

    """Subversion working copy."""

    DIRECTORY = '.svn'
    IGNORES = ('.sgignores', '.vvignores')

    def lock(self, path):
        self.call('svn', 'update')
        self.call('svn', 'lock', path)

    def save(self, message=None):
        message = message or input("Commit message: ")  # pylint: disable=W0141
        self.call('svn', 'commit', '-m', message)

    @property
    def ignores(self):
        if not self._ignores:
            os.chdir(self.path)
            for line in self.call('svn', 'pg', '-R', 'svn:ignore', '.',
                                  return_stdout=True).splitlines():
                self._ignores.append(line)
        return self._ignores
