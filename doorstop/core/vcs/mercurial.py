# SPDX-License-Identifier: LGPL-3.0-only

"""Plug-in module to store requirements in a Mercurial repository."""

from doorstop import common
from doorstop.core.vcs.base import BaseWorkingCopy

log = common.logger(__name__)


class WorkingCopy(BaseWorkingCopy):
    """Mercurial working copy."""

    DIRECTORY = '.hg'
    IGNORES = ('.hgignore',)

    def lock(self, path):
        log.debug("`hg` does not support locking: {}".format(path))
        self.call('hg', 'pull', '-u')

    def edit(self, path):
        self.call('hg', 'add', path)

    def add(self, path):
        self.call('hg', 'add', path)

    def delete(self, path):
        self.call('hg', 'remove', path, '--force')

    def commit(self, message=None):
        message = message or input("Commit message: ")
        self.call('hg', 'commit', '--message', message)
        self.call('hg', 'push')
