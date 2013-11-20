#!/usr/bin/env python

"""
Plug-in module to store requirements in a Git repository.
"""

import subprocess
import logging

from doorstop.core.vcs.base import BaseWorkingCopy


class WorkingCopy(BaseWorkingCopy):  # pragma: no cover - integration test
    """Simulated working copy."""

    DIRECTORY = '.git'

    def lock(self, path):
        logging.warning("git does not support locking: {}".format(path))

    def save(self, message=None):
        args = ['git', 'commit', '-a', '-m', message]
        logging.debug("$ {}".format(' '.join(args)))
        subprocess.call(args)
        args = ['git', 'push']
        logging.debug("$ {}".format(' '.join(args)))
        subprocess.call(args)
