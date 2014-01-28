"""
Plug-in module to store requirements in a Git repository.
"""

import os
import logging

from doorstop.core.vcs.base import BaseWorkingCopy


class WorkingCopy(BaseWorkingCopy):  # pragma: no cover - integration test
    """Simulated working copy."""

    DIRECTORY = '.git'

    def lock(self, path):
        self.call('git', 'pull')
        logging.warning("git does not support locking: {}".format(path))

    def save(self, message=None):
        message = message or input("Commit message: ")  # pylint: disable=W0141
        self.call('git', 'commit', '-a', '-m', message)
        self.call('git', 'push')

    @property
    def ignores(self):
        if not self._ignores:
            path = os.path.join(self.path, '.gitignore')
            if os.path.isfile(path):
                with open(path, 'r') as infile:
                    for line in infile:
                        pattern = line.strip(" @\\/*\n")
                        if pattern and not pattern.startswith('#'):
                            self._ignores.append('*' + pattern + '*')
        return self._ignores
