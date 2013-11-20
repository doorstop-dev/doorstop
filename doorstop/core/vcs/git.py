#!/usr/bin/env python

"""
Plug-in module to store requirements in a Git repository.
"""

import logging

from doorstop.core.vcs.base import BaseWorkingCopy


class WorkingCopy(BaseWorkingCopy):  # pragma: no cover - integration test
    """Simulated working copy."""

    DIRECTORY = '.git'

    def lock(self, path):
        logging.warning("git does not support locking: {}".format(path))

    def save(self, message=None):
        message = message or input("Commit message: ")  # pylint: disable=W0141
        self.call('git', 'commit', '-a', '-m', message)
        self.call('git', 'push')
