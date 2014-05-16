"""Plug-in module to store requirements in a Veracity repository."""

import logging

from doorstop.core.vcs.base import BaseWorkingCopy


class WorkingCopy(BaseWorkingCopy):  # pragma: no cover (integration test)

    """Veracity working copy."""

    DIRECTORY = '.sgdrawer'
    IGNORES = ('.sgignores', '.vvignores')

    def lock(self, path):
        self.call('vv', 'pull')
        self.call('vv', 'update')
        # TODO: track: http://veracity-scm.com/qa/questions/2034
        msg = "veracity does not support scripted locking: {}".format(path)
        logging.warning(msg)

    def save(self, message=None):
        message = message or input("Commit message: ")  # pylint: disable=W0141
        self.call('vv', 'commit', '-m', message)
        self.call('vv', 'push')
