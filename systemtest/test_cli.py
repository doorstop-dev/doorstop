#!/usr/bin/env python

""""
Integration tests for the command-line interface.
"""

import os
import sys
import shutil
import tempfile
import logging
from StringIO import StringIO

import unittest2 as unittest


WS = __program__
INFO = 'info'
UPDATE = 'update'
BUILD = 'build'
TEST = 'test'
DEPLOY = 'deploy'
POLLER = 'poller'
BUILDER = 'builder'

FILES = os.path.join(os.path.dirname(__file__), 'files')
NT_SKIP_REASON = "feature not testable on Windows"


def ws(*args):  # pylint: disable=C0103
    """Run a 'ws' command and return the stdout and stderr."""
    sys.argv = [WS] + list(args)
    logging.info("running: {0}".format(' '.join(sys.argv)))
    output = StringIO()
    exitcode = 0
    stdout_backup = sys.stdout
    try:
        sys.stdout = output
        main()
    except SystemExit as exception:
        logging.info("exit code: {0}".format(exception))
        exitcode = int(str(exception))
    finally:
        sys.stdout = stdout_backup
    return output.getvalue().strip(), exitcode


class TestWorkspace(unittest.TestCase):  # pylint: disable=R0904
    """Tests in a workspace."""  # pylint: disable=C0103

    @classmethod
    def setUpClass(cls):
        """Create a temporary workspace for all tests."""
        cls.temp = os.path.join(tempfile.gettempdir(), WS)
        if not os.path.exists(cls.temp):
            os.makedirs(cls.temp)

    def test_info_product_by_path(self):
        """Verify 'ws info' works from a product's sub-directory."""
        # Create workspace
        os.chdir(self.temp)
        ws(UPDATE, 'MAZ_CMU-140_14.07.000', '--no-depends', '--force')
        # Create empty directory
        temp2 = os.path.join(self.temp, 'src', 'cpp', 'temp2')
        if not os.path.exists(temp2):
            os.makedirs(temp2)
        os.chdir(temp2)
        # Run test
        output, exitcode = ws(INFO)
        self.assertEqual("MAZ_CMU-140_14.07.000", output)
        self.assertEqual(0, exitcode)

    @unittest.skipIf(os.name == 'nt', NT_SKIP_REASON)
    def test_build_component_by_name(self):
        """Verify 'ws build <name>' works for a component."""
        os.chdir(self.temp)
        output, exitcode = ws(BUILD, 'cpp_procio', '--force')
        self.assertEqual("", output)
        self.assertEqual(0, exitcode)

class TestEmpty(unittest.TestCase):  # pylint: disable=R0904
    """Tests in a temporary directory."""  # pylint: disable=C0103

    def setUp(self):
        """Create a temporary directory for each test."""
        self.temp = tempfile.mkdtemp()
        if not os.path.exists(self.temp):
            os.makedirs(self.temp)

    def tearDown(self):
        """Delete the temporary directory."""
        if os.path.exists(self.temp):
            os.chdir(tempfile.gettempdir())
            shutil.rmtree(self.temp)

    def test_info_empty_by_path(self):
        """Verify 'ws info' outputs nothing in an empty workspace."""
        os.chdir(self.temp)
        output, exitcode = ws(INFO)
        self.assertEqual("", output)
        self.assertEqual(1, exitcode)

    def test_update_empty_by_path(self):
        """Verify 'ws update' returns an error in an empty workspace."""
        os.chdir(self.temp)
        output, exitcode = ws(UPDATE)
        self.assertEqual("", output)
        self.assertEqual(1, exitcode)


if __name__ == "__main__":
    unittest.main()
