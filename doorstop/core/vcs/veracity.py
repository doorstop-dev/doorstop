#!/usr/bin/env python

"""
Plug-in module to store requirements in a Veracity repository.
"""

import logging

from veracity import WorkingCopy as VeracityWorkingCopy

from doorstop.core.vcs.base import BaseWorkingCopy


class WorkingCopy(BaseWorkingCopy):  # pragma: no cover - integration test
    """Veracity working copy."""

    DIRECTORY = '.sgdrawer'

    def __init__(self, path):
        super().__init__(path)
        self._wc = VeracityWorkingCopy(path)

    def lock(self, path):
        """Pull and lock the item for editing."""
        self._wc.repo.pull()
        # TODO: item locking requires password input
        # tracker: http://veracity-scm.com/qa/questions/2034
        # item = Item(path, work=self._wc)
        # item.lock()
        msg = "veracity does not support scripted locking: {}".format(path)
        logging.warning(msg)

    def save(self, message=None):
        """Commit and push changes."""
        message = message or input("Commit message: ")  # pylint: disable=W0141
        self._wc.commit(message)
        self._wc.repo.push()
