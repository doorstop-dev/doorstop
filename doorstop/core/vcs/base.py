# SPDX-License-Identifier: LGPL-3.0-only

"""Abstract interface to version control systems."""

import fnmatch
import os
import subprocess
from abc import ABCMeta, abstractmethod
from typing import List, Optional, Tuple

from doorstop import common, settings

log = common.logger(__name__)


class BaseWorkingCopy(metaclass=ABCMeta):
    """Abstract base class for VCS working copies."""

    DIRECTORY: Optional[str] = None  # special hidden directory for the working copy
    IGNORES: Tuple = ()  # hidden filenames containing ignore patterns

    def __init__(self, path):
        self.path = path
        self._ignores_cache: Optional[List[str]] = None
        self._path_cache: Optional[List[Tuple[str, str, str]]] = None

    @staticmethod
    def relpath(path):
        """Get a relative path to the working copy root for commands."""
        return os.path.relpath(path).replace('\\', '/')

    @staticmethod
    def call(*args, return_stdout=False):  # pragma: no cover (abstract method)
        """Call a command with string arguments."""
        log.debug("$ %s", ' '.join(args))
        try:
            if return_stdout:
                return subprocess.check_output(args).decode('utf-8')
            else:
                return subprocess.call(args)
        except FileNotFoundError:
            raise common.DoorstopError("Command not found: {}".format(args[0]))

    @abstractmethod
    def lock(self, path):  # pragma: no cover (abstract method)
        """Pull, update, and lock a file for editing."""
        raise NotImplementedError

    @abstractmethod
    def edit(self, path):  # pragma: no cover (abstract method)
        """Mark a file as modified."""
        raise NotImplementedError

    @abstractmethod
    def add(self, path):  # pragma: no cover (abstract method)
        """Start tracking a file."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, path):  # pragma: no cover (abstract method)
        """Stop tracking a file."""
        raise NotImplementedError

    @abstractmethod
    def commit(self, message=None):  # pragma: no cover (abstract method)
        """Unlock files, commit, and push."""
        raise NotImplementedError

    @property
    def ignores(self):
        """Yield glob expressions to ignore."""
        if self._ignores_cache is None:
            self._ignores_cache = []
            log.debug("reading and caching the ignore patterns...")
            for filename in self.IGNORES:
                path = os.path.join(self.path, filename)
                if os.path.isfile(path):
                    for line in common.read_lines(path):
                        pattern = line.strip(" @\\/*\n")
                        if pattern and not pattern.startswith('#'):
                            self._ignores_cache.append('*' + pattern + '*')
        yield from self._ignores_cache

    @property
    def paths(self):
        """Yield non-ignored paths in the working copy."""
        if self._path_cache is None or not settings.CACHE_PATHS:
            log.debug("reading and caching all file paths...")
            self._path_cache = []
            for dirpath, _, filenames in os.walk(self.path):
                for filename in filenames:
                    path = os.path.join(dirpath, filename)
                    relpath = os.path.relpath(path, self.path)
                    # Skip ignored paths
                    if self.ignored(relpath):
                        continue
                    # Skip hidden paths
                    if os.path.sep + '.' in os.path.sep + relpath:
                        continue
                    self._path_cache.append((path, filename, relpath))
        yield from self._path_cache

    def ignored(self, path):
        """Determine if a path matches an ignored pattern."""
        for pattern in self.ignores:
            if fnmatch.fnmatch(path, pattern):
                return True
        return False
