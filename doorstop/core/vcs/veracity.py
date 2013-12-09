"""
Plug-in module to store requirements in a Veracity repository.
"""

import os
import logging

from doorstop.core.vcs.base import BaseWorkingCopy


class WorkingCopy(BaseWorkingCopy):  # pragma: no cover - integration test
    """Veracity working copy."""

    DIRECTORY = '.sgdrawer'
    IGNORES = ('.sgignores', '.vvignores')

    def lock(self, path):
        """Pull and lock the item for editing."""
        self.call('vv', 'pull')
        self.call('vv', 'update')
        # TODO: item locking requires password input
        # tracker: http://veracity-scm.com/qa/questions/2034
        msg = "veracity does not support scripted locking: {}".format(path)
        logging.warning(msg)

    def save(self, message=None):
        """Commit and push changes."""
        message = message or input("Commit message: ")  # pylint: disable=W0141
        self.call('vv', 'commit', '-m', message)
        self.call('vv', 'push')

    @property
    def ignores(self):
        """Get a list of glob expressions to ignore."""
        if not self._ignores:
            for filename in self.IGNORES:
                path = os.path.join(self.path, filename)
                if os.path.isfile(path):
                    with open(path, 'r') as infile:
                        for line in infile:
                            pattern = line.strip(" @\\/*\n")
                            if pattern and not pattern.startswith('#'):
                                self._ignores.append('*' + pattern + '*')
        return self._ignores
