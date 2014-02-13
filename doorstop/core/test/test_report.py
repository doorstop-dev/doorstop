#!/usr/bin/env python

"""
Unit tests for the doorstop.core.report module.
"""

import unittest
from unittest.mock import patch, MagicMock

import os
import tempfile
import shutil

from doorstop.core import report
from doorstop.core.vcs.mockvcs import WorkingCopy
from doorstop.common import DoorstopError

from doorstop.core.test import FILES, ENV, REASON
from doorstop.core.test.test_item import MockItem

# Whenever the report format is changed:
#  1. set ASSERT_CONTENTS to False
#  2. re-run all tests
#  3. manually verify the newly generated reports are correct
#  4. set ASSERT_CONTENTS to True
ASSERT_CONTENTS = True  # set to False to override contents


class TestModule(unittest.TestCase):  # pylint: disable=R0904
    """Unit tests for the doorstop.core.report module."""  # pylint: disable=C0103

    @classmethod
    def setUpClass(cls):
        cls.item = MockItem('path/to/req3.yml',
                            _file="links: [sys3]\ntext: 'Heading'\n"
                            "level: 1.0\nnormative: false")
        cls.document = MagicMock()
        cls.document.items = [
            cls.item,
            MockItem('path/to/req3.yml',
                     _file="links: [sys3]\ntext: '" + ("Hello, world! " * 10)
                     + "'\nlevel: 1.2"),
            MockItem('path/to/req1.yml',
                     _file="links: []\ntext: 'abc\n123'\nlevel: 1.1"),
            MockItem('path/to/req2.yml',
                     _file="links: [sys1, sys2]\ntext: ''\nlevel: 2"),
            MockItem('path/to/req4.yml',
                     _file="links: [sys2]\nref: '123456789'\nlevel: 2.1.1"),
            MockItem('path/to/req2.yml',
                     _file="links: [sys1]\ntext: 'Heading 2'\nlevel: 2.1.0\n"
                     "normative: false"),
        ]
        cls.work = WorkingCopy(None)

    @patch('builtins.open')
    @patch('doorstop.core.report.lines')
    def test_publish_html(self, mock_lines, mock_open):
        """Verify an HTML file can be created."""
        path = os.path.join('mock', 'report.html')
        report.publish(self.document, path, '.html')
        mock_open.assert_called_once_with(path, 'wb')
        mock_lines.assert_called_once_with(self.document, '.html',
                                           ignored=None)

    @unittest.skipUnless(os.getenv(ENV), REASON)
    def test_publish_html_long(self):
        """Verify an HTML file can be created (long)."""
        temp = tempfile.mkdtemp()
        try:
            path = os.path.join(temp, 'report.html')
            report.publish(self.document, path, '.html')
            self.assertTrue(os.path.isfile(path))
        finally:
            shutil.rmtree(temp)

    def test_publish_unknown(self):
        """Verify publishing to an unknown format raises an exception."""
        self.assertRaises(DoorstopError,
                          report.publish, self.document, 'a.a', '.a')

    def test_lines_text_item(self):
        """Verify a text report can be created from an item."""
        expected = "1.0     Heading\n\n"
        lines = report.lines(self.item, '.txt', ignored=self.work.ignored)
        text = ''.join(line + '\n' for line in lines)
        self.assertEqual(expected, text)

    def test_lines_text_document(self):
        """Verify a text report can be created from a document."""
        path = os.path.join(FILES, 'report.txt')
        expected = open(path).read()
        lines = report.lines(self.document, '.txt', ignored=self.work.ignored)
        text = ''.join(line + '\n' for line in lines)
        if ASSERT_CONTENTS:
            self.assertEqual(expected, text)
        with open(path, 'wb') as outfile:
            outfile.write(bytes(text, 'utf-8'))

    def test_lines_markdown_item(self):
        """Verify a Markdown report can be created from an item."""
        expected = "# 1.0 Heading\n\n"
        lines = report.lines(self.item, '.md', ignored=self.work.ignored)
        text = ''.join(line + '\n' for line in lines)
        self.assertEqual(expected, text)

    def test_lines_markdown_document(self):
        """Verify a Markdown report can be created from a document."""
        path = os.path.join(FILES, 'report.md')
        expected = open(path).read()
        lines = report.lines(self.document, '.md', ignored=self.work.ignored)
        text = ''.join(line + '\n' for line in lines)
        if ASSERT_CONTENTS:
            self.assertEqual(expected, text)
        with open(path, 'wb') as outfile:
            outfile.write(bytes(text, 'utf-8'))

    def test_lines_html_item(self):
        """Verify an HTML report can be created from an item."""
        expected = "<h1>1.0 Heading</h1>\n"
        lines = report.lines(self.item, '.html', ignored=self.work.ignored)
        text = ''.join(line + '\n' for line in lines)
        self.assertEqual(expected, text)

    def test_lines_html_document(self):
        """Verify an HTML report can be created from a document."""
        path = os.path.join(FILES, 'report.html')
        expected = open(path).read()
        lines = report.lines(self.document, '.html', ignored=self.work.ignored)
        text = ''.join(line + '\n' for line in lines)
        if ASSERT_CONTENTS:
            self.assertEqual(expected, text)
        with open(path, 'wb') as outfile:
            outfile.write(bytes(text, 'utf-8'))

    def test_lines_unknown(self):
        """Verify iterating an unknown format raises."""
        gen = report.lines(self.document, '.a')
        self.assertRaises(DoorstopError, list, gen)


if __name__ == '__main__':
    unittest.main()
