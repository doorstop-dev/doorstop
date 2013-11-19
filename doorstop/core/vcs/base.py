#!/bin/usr/env python

"""
Abstract interface to verson control systems.
"""

from abc import ABCMeta, abstractmethod  # pylint: disable=W0611


class BaseWorkingCopy(object, metaclass=ABCMeta):  # pylint: disable=R0921
    """Abstract base class for VCS working copies."""

    DIRECTORY = None  # special hidden directory for the working copy

    def __init__(self, path):
        self.path = path

    @abstractmethod
    def lock(self, path):  # pragma: no cover - abstract method
        """Pull, update, and lock a file for editing."""
        raise NotImplementedError()

    @abstractmethod
    def save(self, message=None):  # pragma: no cover - abstract method
        """Unlock files, commit, and push."""
        raise NotImplementedError()
