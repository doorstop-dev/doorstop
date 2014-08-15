"""Plug-in module to store requirements in a Veracity repository."""

from doorstop import common
from doorstop.core.vcs.base import BaseWorkingCopy

log = common.logger(__name__)


class WorkingCopy(BaseWorkingCopy):  # pragma: no cover (integration test)

    """Veracity working copy."""

    DIRECTORY = '.sgdrawer'
    IGNORES = ('.sgignores', '.vvignores')

    def lock(self, path):
        # track: http://veracity-scm.com/qa/questions/2034
        msg = "veracity does not support scripted locking: {}".format(path)
        log.info(msg)
        self.call('vv', 'pull')
        self.call('vv', 'update')

    def save(self, message=None):
        message = message or input("Commit message: ")  # pylint: disable=W0141
        self.call('vv', 'commit', '-m', message)
        self.call('vv', 'push')
