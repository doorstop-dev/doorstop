"""Plug-in module to simulate the storage of requirements in a repository."""


from doorstop import common
from doorstop.core.vcs.base import BaseWorkingCopy

log = common.logger(__name__)


class WorkingCopy(BaseWorkingCopy):

    """Simulated working copy."""

    DIRECTORY = '.mockvcs'

    def lock(self, path):
        log.info("simulated lock on: {}...".format(path))

    def edit(self, path):
        log.info("simulated edit on: {}...".format(path))

    def add(self, path):
        log.info("simulated add on: {}...".format(path))

    def delete(self, path):
        log.info("simulated delete on: {}...".format(path))

    def commit(self, message=None):
        log.info("simulated save")

    @property
    def ignores(self):  # pragma: no cover (manual test)
        return ("*/env/*", "*/apidocs/*", "*/build/lib/*")
