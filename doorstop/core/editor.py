""""Functions to edit documents and items."""

import os
import sys
from distutils.spawn import find_executable
import subprocess
import time
import logging


# TODO: add edit_document
# TODO: add edit_item, refactor code from Tree.edit_item

LAUNCH_DELAY = 1.0  # number of seconds to let a program try to launch


def edit(path, tool=None):  # pragma: no cover (integration test)
    """Open a file and wait for the default editor to exit.

    @param path: path of file to open
    @param tool: path of alternate editor

    @return: launched process

    """
    process = launch(path, tool=tool)
    try:
        time.sleep(LAUNCH_DELAY)
        if process.poll() is None:
            logging.debug("process is running")
            process.wait()
        else:
            logging.debug("process exited immediately")
    except KeyboardInterrupt:
        logging.warning("force closed editor")
    else:
        logging.debug("process is not running")
    finally:
        if process.returncode is None:
            process.terminate()
    logging.debug("returncode: {}".format(process.returncode))


def launch(path, tool=None):  # pragma: no cover (integration test)
    """Open a file using the default editor.

    @param path: path of file to open
    @param tool: path of alternate editor

    @return: launched process

    """
    relpath = os.path.relpath(path)
    if tool:
        args = [tool, relpath]
    elif sys.platform.startswith('darwin'):
        args = ['open', relpath]
    elif os.name == 'nt':
        cygstart = find_executable('cygstart')
        if cygstart:
            args = [cygstart, relpath]
        else:
            args = ['start', relpath]
    elif os.name == 'posix':
        args = ['xdg-open', relpath]

    return _call(args)


def _call(args):  # pragma: no cover (integration test)
    """Call a program with arguments and return the process."""
    logging.debug("$ {}".format(' '.join(args)))
    process = subprocess.Popen(args)
    return process
