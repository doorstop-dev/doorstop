#!/usr/bin/env python

"""
Integration tests for the documentation tutorials.
"""

import unittest

import os
import shutil
import tempfile
import subprocess
import logging

from doorstop.cli.test import ENV, REASON, ROOT

if os.name == 'nt':
    PATH = os.path.join(ROOT, 'env', 'Scripts', 'doorstop.exe')
    DOORSTOP = os.path.normpath(PATH)
else:
    PATH = os.path.join(ROOT, 'env', 'bin', 'doorstop')
    DOORSTOP = os.path.normpath(PATH)


if __name__ == '__main__':
    os.environ[ENV] = '1'  # run the integration tests when called directly


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestBase(unittest.TestCase):  # pylint: disable=R0904
    """Base class for tutorial tests."""

    def setUp(self):
        self.cwd = os.getcwd()
        self.temp = tempfile.mkdtemp()
        print("$ cd {}".format(self.temp))
        os.chdir(self.temp)
        os.mkdir('.mockvcs')  # simulate a working copy
        os.environ['EDITOR'] = 'cat'

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.temp)

    @staticmethod
    def doorstop(args=""):
        """Call 'doorstop' with a string of arguments."""
        print("$ doorstop {}".format(args))
        cmd = "{} {} -v".format(DOORSTOP, args)
        if subprocess.call(cmd, shell=True, stderr=subprocess.PIPE) != 0:
            raise AssertionError("command failed: doorstop {}".format(args))


@unittest.skipUnless(os.getenv(ENV), REASON)  # pylint: disable=R0904
class TestSection1(TestBase):  # pylint: disable=R0904
    """Integration tests for section 1.0 of the tutorial."""

    def test_tutorial_section_1(self):
        """Verify tutorial section 1.0 is working."""

        # 1.1

        self.doorstop("new REQ ./reqs")

        self.doorstop("add REQ")
        self.doorstop("add REQ")
        self.doorstop("add REQ")

        self.doorstop("edit REQ1 --tool cat")
        self.doorstop("edit REQ2 --tool cat")

        # 1.2

        self.doorstop("new TST ./reqs/tests --parent REQ")

        self.doorstop("add TST")
        self.doorstop("add TST")

        self.doorstop("edit TST1 --tool cat")
        self.doorstop("edit TST2 --tool cat")

        self.doorstop("link TST1 REQ1")
        self.doorstop("link TST1 REQ3")
        self.doorstop("link TST2 REQ1")
        self.doorstop("link TST2 REQ2")

        # 1.3

        self.doorstop("unlink TST1 REQ3")

        self.doorstop("remove REQ3")

        # 1.4

        self.doorstop()


if __name__ == '__main__':
    logging.basicConfig(format="%(message)s", level=logging.INFO)
    unittest.main()
