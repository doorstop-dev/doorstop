#!/usr/bin/env python

"""
Interfaces to SCM systems.
"""

# TODO: rename package to vcs

import os
import logging

SCM_DIRECTORIES = [
'.git',
'.sgdrawer',
]  # TODO: build dymacially from the modules in this package


class VersionControlError(EnvironmentError):
    pass


def find_root(cwd):
    """Find the root of the working copy.

    @param: current working directory
    """
    path = cwd

    logging.debug("looking for working copy from {}...".format(path))
    while not any(d in SCM_DIRECTORIES for d in os.listdir(path)):
        parent = os.path.dirname(path)
        if path == parent:
            msg = "no working copy found from: {}".format(cwd)
            raise VersionControlError(msg)
        else:
            path = parent

    logging.debug("found working copy: {}".format(path))
    return path






