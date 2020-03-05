#!/usr/bin/env python
# SPDX-License-Identifier: LGPL-3.0-only

"""Integration tests for the documentation tutorials."""

import logging
import os
import shutil
import subprocess
import tempfile
import unittest

from doorstop.cli.tests import FILES, ROOT

if 'TRAVIS' in os.environ:
    PATH = os.path.join(os.environ['VIRTUAL_ENV'], 'bin', 'doorstop')
elif os.name == 'nt':
    PATH = os.path.join(ROOT, '.venv', 'Scripts', 'doorstop.exe')
else:
    PATH = os.path.join(ROOT, '.venv', 'bin', 'doorstop')
DOORSTOP = os.path.normpath(PATH)


class TestBase(unittest.TestCase):
    """Base class for tutorial tests."""

    def setUp(self):
        print()
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
    def doorstop(args="", returncode=0, stdout=None):
        """Call 'doorstop' with a string of arguments."""
        print("$ doorstop {}".format(args))
        cmd = "{} {} -v".format(DOORSTOP, args)
        cp = subprocess.run(cmd, shell=True, stdout=stdout, stderr=subprocess.PIPE)
        if cp.returncode != returncode:
            raise AssertionError("command failed: doorstop {}".format(args))
        return cp


class TestSection1(TestBase):
    """Integration tests for section 1.0 of the tutorial."""

    def test_tutorial_section_1(self):
        """Verify tutorial section 1.0 is working."""

        # 1.1

        self.doorstop("create REQ ./reqs")

        self.doorstop("add REQ")
        self.doorstop("add REQ")
        self.doorstop("add REQ")

        self.doorstop("edit REQ1 --tool cat")
        self.doorstop("edit REQ2 --tool cat")

        # 1.2

        self.doorstop("create TST ./reqs/tests --parent REQ")

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

    def test_tutorial_section_2(self):
        """Verify tutorial section 2.0 is working."""

        # Create a basic document
        self.doorstop("create REQ ./reqs")
        self.doorstop("add REQ")
        self.doorstop("add REQ")
        self.doorstop("create TST ./reqs/tests --parent REQ")
        self.doorstop("add TST")
        self.doorstop("add TST")
        self.doorstop("link TST1 REQ1")
        self.doorstop("link TST2 REQ1")
        self.doorstop("link TST2 REQ2")

        # 2.1

        self.doorstop("publish REQ")
        self.doorstop("publish TST")

        # 2.2

        self.doorstop("publish all path/to/htmldir")

    def test_tutorial_section_3(self):
        """Verify tutorial section 3.0 is working."""

        # 3.2

        self.doorstop("import --document HLR reqs/hlr")
        self.doorstop("import --document LLR reqs/llr --parent HLR")

        # 3.3

        self.doorstop("import --item HLR HLR001")
        self.doorstop(
            "import --item LLR LLR001 " "--attr \"{'text': 'The item text.'}\""
        )

        # 3.1

        dirpath = os.path.join(self.temp, 'path', 'to')
        os.makedirs(dirpath)
        path = os.path.join(FILES, 'exported.xlsx')
        shutil.copy(path, dirpath)
        self.doorstop("import path/to/exported.xlsx HLR")

    def test_tutorial_section_4(self):
        """Verify tutorial section 4.0 is working."""

        # Create a basic document
        self.doorstop("create REQ ./reqs")
        self.doorstop("add REQ")
        self.doorstop("add REQ")
        self.doorstop("create TST ./reqs/tests --parent REQ")
        self.doorstop("add TST")
        self.doorstop("add TST")
        self.doorstop("link TST1 REQ1")
        self.doorstop("link TST2 REQ1")
        self.doorstop("link TST2 REQ2")

        # 4.1

        self.doorstop("export TST")
        self.doorstop("export all dirpath/to/exports")
        self.doorstop("export REQ path/to/req.xlsx")

    def test_validate_cycles(self):
        """Verify cycle detection is working."""

        self.doorstop("create A .")
        self.doorstop("create B b --parent A")

        src = os.path.join(FILES, 'A001.txt')
        dst = os.path.join(self.temp, 'A001.yml')
        shutil.copy(src, dst)
        src = os.path.join(FILES, 'A002.txt')
        dst = os.path.join(self.temp, 'A002.yml')
        shutil.copy(src, dst)
        src = os.path.join(FILES, 'B001.txt')
        dst = os.path.join(self.temp, 'b', 'B001.yml')
        shutil.copy(src, dst)
        src = os.path.join(FILES, 'B002.txt')
        dst = os.path.join(self.temp, 'b', 'B002.yml')
        shutil.copy(src, dst)

        cp = self.doorstop()
        self.assertIn(
            b'WARNING: A: A001: detected a cycle with a back edge from B001 to A001',
            cp.stderr,
        )
        self.assertIn(
            b'WARNING: A: A001: detected a cycle with a back edge from A002 to A002',
            cp.stderr,
        )

    def test_clear_links(self):
        """Verify clear links is working."""

        self.doorstop("create C .")

        src = os.path.join(FILES, 'C001.txt')
        dst = os.path.join(self.temp, 'C001.yml')
        shutil.copy(src, dst)
        src = os.path.join(FILES, 'C002.txt')
        dst = os.path.join(self.temp, 'C002.yml')
        shutil.copy(src, dst)
        src = os.path.join(FILES, 'C003.txt')
        dst = os.path.join(self.temp, 'C003.yml')
        shutil.copy(src, dst)

        cp = self.doorstop()
        self.assertIn(b'WARNING: C: C001: suspect link: C002', cp.stderr)
        self.assertIn(b'WARNING: C: C001: suspect link: C003', cp.stderr)

        cp = self.doorstop("clear C001 C004", 1)
        self.assertIn(b'ERROR: no item with UID: C004', cp.stderr)

        cp = self.doorstop("clear C001 C001 C002", stdout=subprocess.PIPE)
        self.assertIn(
            b'clearing item C001\'s suspect links to C001, C002...', cp.stdout
        )

        cp = self.doorstop()
        self.assertIn(b'WARNING: C: C001: suspect link: C003', cp.stderr)

        cp = self.doorstop("clear C001", stdout=subprocess.PIPE)
        self.assertIn(b'clearing item C001\'s suspect links...', cp.stdout)

        cp = self.doorstop()
        self.assertNotIn(b'suspect link', cp.stderr)

    def test_custom_defaults(self):
        """Verify new item with custom defaults is working."""

        self.doorstop("create REQ .")

        cp = self.doorstop("add -d no/such/file.yml REQ", 1)
        self.assertIn(b'ERROR: reading ', cp.stderr)

        self.assertFalse(os.path.isfile('REQ001.yml'))

        template = os.path.join(FILES, 'template.yml')
        self.doorstop("add -d {} REQ".format(template))

        self.assertTrue(os.path.isfile('REQ001.yml'))

        cp = self.doorstop("publish REQ", stdout=subprocess.PIPE)
        self.assertIn(
            b'1.0     REQ001'
            + str.encode(os.linesep)
            + str.encode(os.linesep)
            + b'        Some text'
            + str.encode(os.linesep)
            + b'        with more than'
            + str.encode(os.linesep)
            + b'        one line.'
            + str.encode(os.linesep),
            cp.stdout,
        )

    def test_item_with_name(self):
        """Verify new item with custom defaults is working."""

        self.doorstop("create -s - REQ .")

        self.doorstop("add -n ABC REQ")
        self.assertTrue(os.path.isfile('REQ-ABC.yml'))

        self.doorstop("add -n 9 REQ")
        self.assertTrue(os.path.isfile('REQ-009.yml'))

        self.doorstop("add --name XYZ REQ")
        self.assertTrue(os.path.isfile('REQ-XYZ.yml'))

        self.doorstop("add --number 99 REQ")
        self.assertTrue(os.path.isfile('REQ-099.yml'))

        cp = self.doorstop("publish REQ", stdout=subprocess.PIPE)
        self.assertIn(
            b'1.0     REQ-ABC'
            + str.encode(os.linesep)
            + str.encode(os.linesep)
            + b'1.1     REQ-009'
            + str.encode(os.linesep)
            + str.encode(os.linesep)
            + b'1.2     REQ-XYZ'
            + str.encode(os.linesep)
            + str.encode(os.linesep)
            + b'1.3     REQ-099',
            cp.stdout,
        )


if __name__ == '__main__':
    logging.basicConfig(format="%(message)s", level=logging.INFO)
    unittest.main(verbosity=0)
