#!/usr/bin/env python

"""
Unit tests for the doorstop.core.report module.
"""

import unittest
from unittest.mock import Mock

import os

from doorstop.core.report import get_text

from doorstop.core.test import FILES
from doorstop.core.test.test_item import MockItem

ASSERT_CONTENTS = True  # set to False to overrite contents


class TestModule(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for the doorstop.core.report module."""  # pylint: disable=C0103

    @classmethod
    def setUpClass(cls):
        cls.document = Mock()
        cls.document.items = [
            MockItem('path/to/req3.yml',
                     _file="links: [sys3]\ntext: '" + ("Hello, world! " * 10)
                     + "'\nlevel: 1.0"),
            MockItem('path/to/req1.yml',
                     _file="links: []\ntext: 'abc\n123'\nlevel: 1.1"),
            MockItem('path/to/req2.yml',
                     _file="links: [sys1, sys2]\ntext: ''\nlevel: 2.0"),
            MockItem('path/to/req4.yml',
                     _file="links: [sys2]\nref: 'r1'\nlevel: 2.1"),
        ]

    def test_get_text(self):
        """Verify a text report can be created."""
        path = os.path.join(FILES, 'report.txt')
        expected = open(path).read()
        text = ''.join(line + '\n' for line in get_text(self.document))
        if ASSERT_CONTENTS:
            self.assertEqual(expected, text)
        with open(path, 'w') as rep:
            rep.write(text)


if __name__ == '__main__':
    unittest.main()
