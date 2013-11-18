#!/usr/bin/env python

"""
Plug-in module to store requirements in a Veracity repository.
"""

from doorstop.core.vcs.base import BaseWorkingCopy


class WorkingCopy(BaseWorkingCopy):  # pragma: no cover - integration test
    """Veracity working copy."""

    DIRECTORY = '.sgdrawer'

    def lock(self, path):
        raise NotImplementedError("TODO: add veracity lock")

    def save(self):
        raise NotImplementedError("TODO: add veracity commit/push")
