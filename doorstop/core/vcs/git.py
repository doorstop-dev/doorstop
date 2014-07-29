"""Plug-in module to store requirements in a Git repository."""

from doorstop import common
from doorstop.core.vcs.base import BaseWorkingCopy

log = common.logger(__name__)  # pylint: disable=C0103


class WorkingCopy(BaseWorkingCopy):  # pragma: no cover (integration test)

    """Git working copy."""

    DIRECTORY = '.git'
    IGNORES = ('.gitignore',)

    def lock(self, path):
        self.call('git', 'pull')
        log.warning("git does not support locking: {}".format(path))

    def save(self, message=None):
        message = message or input("Commit message: ")  # pylint: disable=W0141
        self.call('git', 'commit', '-a', '-m', message)
        self.call('git', 'push')
