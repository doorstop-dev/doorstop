#!/bin/usr/env python

"""
Abstract interface to verson control systems.
"""

import fnmatch
import subprocess
import logging
from abc import ABCMeta, abstractmethod  # pylint: disable=W0611


class BaseWorkingCopy(object, metaclass=ABCMeta):  # pylint: disable=R0921
    """Abstract base class for VCS working copies."""

    DIRECTORY = None  # special hidden directory for the working copy

    def __init__(self, path):
        self.path = path
        self._ignores = []

    @staticmethod
    def call(*args):  # pragma: no cover - abstract method
        """Call a command with string arguments."""
        logging.debug("$ {}".format(' '.join(args)))
        subprocess.call(args)

    @abstractmethod
    def lock(self, path):  # pragma: no cover - abstract method
        """Pull, update, and lock a file for editing."""
        raise NotImplementedError()

    @abstractmethod
    def save(self, message=None):  # pragma: no cover - abstract method
        """Unlock files, commit, and push."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def ignores(self):  # pragma: no cover - abstract method
        """Get a list of glob expressions to ignore."""
        return []

    def ignored(self, path):
        """Indicates if a path should be considered ignored."""
        for pattern in self.ignores:
            if fnmatch.fnmatch(path, pattern):
                return True
        return False
