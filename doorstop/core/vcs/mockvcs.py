"""Plug-in module to simulate the storage of requirements in a repository."""

import logging

from doorstop.core.vcs.base import BaseWorkingCopy


class WorkingCopy(BaseWorkingCopy):  # pragma: no cover (integration test)

    """Simulated working copy."""

    DIRECTORY = '.mockvcs'

    def lock(self, path):
        logging.info("simulated lock on: {}...".format(path))

    def save(self, message=None):
        logging.info("simulated save")

    @property
    def ignores(self):
        return ("*/env/*", "*/apidocs/*", "*/build/lib/*")
