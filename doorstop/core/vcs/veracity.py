"""Plug-in module to store requirements in a Veracity repository."""

from doorstop import common
from doorstop.core.vcs.base import BaseWorkingCopy

log = common.logger(__name__)


class WorkingCopy(BaseWorkingCopy):

    """Veracity working copy."""

    DIRECTORY = '.sgdrawer'
    IGNORES = ('.sgignores', '.vvignores')

    def lock(self, path):
        # TODO: track: http://veracity-scm.com/qa/questions/2034
        log.info("veracity does not support scripted locking: {}".format(path))
        self.call('vv', 'pull')
        self.call('vv', 'update')

    def save(self, message=None):
        message = message or input("Commit message: ")  # pylint: disable=W0141
        self.call('vv', 'commit', '--message', message)
        self.call('vv', 'push')
