# SPDX-License-Identifier: LGPL-3.0-only

"""Functions to edit documents and items."""

import os
import subprocess
import sys
import tempfile
import time
from distutils.spawn import find_executable

from doorstop import common
from doorstop.common import DoorstopError

LAUNCH_DELAY = 0.5  # number of seconds to let a program try to launch

log = common.logger(__name__)


def edit(path, tool=None):
    """Open a file and wait for the default editor to exit.

    :param path: path of file to open
    :param tool: path of alternate editor

    :return: launched process

    """
    process = launch(path, tool=tool)
    if process:
        try:
            process.wait()
        except KeyboardInterrupt:
            log.debug("user cancelled")
        finally:
            if process.returncode is None:
                process.terminate()
                log.warning("force closed editor")
        log.debug("process exited: {}".format(process.returncode))


def edit_tmp_content(title=None, original_content=None, tool=None):
    """Edit content in a temporary file and return the saved content.

    :param title: text that will appear in the name of the temporary file.
        If not given, name is only random characters.
    :param original_content: content to insert in the temporary file before
        opening it with the editor. If not given, file is empty.
        Must be a string object.
    :param tool: path of alternate editor

    :return: content of the temporary file after user closes the editor.

    """
    # Create a temporary file to edit the text
    tmp_fd, tmp_path = tempfile.mkstemp(prefix='{}_'.format(title), text=True)
    os.close(tmp_fd)  # release the file descriptor because it is not needed
    with open(tmp_path, 'w') as tmp_f:
        tmp_f.write(original_content)

    # Open the editor to edit the temporary file with the original text
    edit(tmp_path, tool=tool)

    # Read the edited text and remove the tmp file
    with open(tmp_path, 'r') as tmp_f:
        edited_content = tmp_f.read()
    os.remove(tmp_path)

    return edited_content


def launch(path, tool=None):
    """Open a file using the default editor.

    :param path: path of file to open
    :param tool: path of alternate editor

    :raises: :class:`~doorstop.common.DoorstopError` no default editor
        or editor unavailable

    :return: launched process if long-running, else None

    """
    # Determine how to launch the editor
    if tool:
        args = [tool, path]
    elif sys.platform.startswith('darwin'):
        args = ['open', path]
    elif os.name == 'nt':
        cygstart = find_executable('cygstart')
        if cygstart:
            args = [cygstart, path]
        else:
            args = ['start', path]
    elif os.name == 'posix':
        args = ['xdg-open', path]

    # Launch the editor
    try:
        log.info("opening '{}'...".format(path))
        process = _call(args)
    except FileNotFoundError:
        raise DoorstopError("editor not found: {}".format(args[0]))

    # Wait for the editor to launch
    time.sleep(LAUNCH_DELAY)
    if process.poll() is None:
        log.debug("process is running...")
    else:
        log.debug("process exited: {}".format(process.returncode))
        if process.returncode != 0:
            raise DoorstopError("no default editor for: {}".format(path))

    # Return the process if it's still running
    return process if process.returncode is None else None


def _call(args):
    """Call a program with arguments and return the process."""
    log.debug("$ {}".format(' '.join(args)))
    process = subprocess.Popen(args)
    return process
