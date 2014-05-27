"""Unit tests for the doorstop.core.exporter module."""

import unittest
from unittest.mock import patch, Mock, MagicMock

import os
import tempfile
import shutil

from doorstop.common import DoorstopError
from doorstop.core import exporter

from doorstop.core.test import FILES, EMPTY, ENV, REASON
from doorstop.core.test.test_publisher import BaseTestCase

# Whenever the export format is changed:
#  1. set CHECK_EXPORTED_CONTENT to False
#  2. re-run all tests
#  3. manually verify the newly generated reports are correct
#  4. set CHECK_EXPORTED_CONTENT to True
CHECK_EXPORTED_CONTENT = True


class TestModule(BaseTestCase):  # pylint: disable=R0904

    """Unit tests for the doorstop.core.exporter module."""  # pylint: disable=C0103

    @patch('os.makedirs')
    @patch('doorstop.core.exporter.create')
    def test_export(self, mock_create, mock_makedirs):
        """Verify a document can be exported."""
        dirpath = os.path.join('mock', 'directory')
        path = os.path.join(dirpath, 'exported.xlsx')
        # Act
        exporter.export(self.document, path)
        # Assert
        mock_makedirs.assert_called_once_with(dirpath)
        mock_create.assert_called_once_with(self.document, path, '.xlsx')

    def test_export_unknown(self):
        """Verify an exception is raised when exporting unknown formats."""
        self.assertRaises(DoorstopError,
                          exporter.export, self.document, 'a.a')
        self.assertRaises(DoorstopError,
                          exporter.export, self.document, 'a.yml', '.a')

    def test_lines(self):
        """Verify an item can be exported as lines."""
        expected = ("req3:" + '\n'
                    "  active: true" + '\n'
                    "  derived: false" + '\n'
                    "  level: 1.0" + '\n'
                    "  links: []" + '\n'
                    "  normative: true" + '\n'
                    "  ref: ''" + '\n'
                    "  text: ''" + '\n\n')
        # Act
        lines = exporter.lines(self.item)
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertEqual(expected, text)

    def test_lines_unknown(self):
        """Verify an exception is raised when iterating an unknown format."""
        # Act
        gen = exporter.lines(self.document, '.a')
        # Assert
        self.assertRaises(DoorstopError, list, gen)

    def test_create(self):
        """Verify an item can be exported as a file."""
        temp = tempfile.mkdtemp()
        path = os.path.join(temp, 'exported.csv')
        # Act
        exporter.create(self.item, path)
        # Assert
        self.assertTrue(os.path.isfile(path))

    def test_create_unknown(self):
        """Verify an item can be exported as a file."""
        self.assertRaises(DoorstopError,
                          exporter.create, self.document, 'a.a')
        self.assertRaises(DoorstopError,
                          exporter.create, self.document, 'a.csv', '.a')


@unittest.skip("TODO: implement tests")
@unittest.skipUnless(os.getenv(ENV) or not CHECK_EXPORTED_CONTENT, REASON)  # pylint: disable=R0904
class TestModuleIntegration(BaseTestCase):  # pylint: disable=R0904

    """Integration tests for the doorstop.core.exporter module."""  # pylint: disable=C0103

    def test_publish_html(self):
        """Verify an HTML file can be created."""
        temp = tempfile.mkdtemp()
        try:
            path = os.path.join(temp, 'report.html')
            publisher.publish(self.document, path, '.html')
            self.assertTrue(os.path.isfile(path))
        finally:
            shutil.rmtree(temp)

    def test_lines_text_document(self):
        """Verify text can be published from a document."""
        path = os.path.join(FILES, 'report.txt')
        expected = open(path).read()
        lines = publisher.lines(self.document, '.txt')
        text = ''.join(line + '\n' for line in lines)
        if CHECK_EXPORTED_CONTENT:
            self.assertEqual(expected, text)
        with open(path, 'w') as outfile:
            outfile.write(text)

    @patch('doorstop.settings.PUBLISH_CHILD_LINKS', True)
    def test_lines_text_document_with_child_links(self):
        """Verify text can be published from a document with child links."""
        path = os.path.join(FILES, 'report2.txt')
        expected = open(path).read()
        lines = publisher.lines(self.document, '.txt')
        text = ''.join(line + '\n' for line in lines)
        if CHECK_EXPORTED_CONTENT:
            self.assertEqual(expected, text)
        with open(path, 'w') as outfile:
            outfile.write(text)

    def test_lines_markdown_document(self):
        """Verify Markdown can be published from a document."""
        path = os.path.join(FILES, 'report.md')
        expected = open(path).read()
        lines = publisher.lines(self.document, '.md')
        text = ''.join(line + '\n' for line in lines)
        if CHECK_EXPORTED_CONTENT:
            self.assertEqual(expected, text)
        with open(path, 'w') as outfile:
            outfile.write(text)

    @patch('doorstop.settings.PUBLISH_CHILD_LINKS', True)
    def test_lines_markdown_document_with_child_links(self):
        """Verify Markdown can be published from a document w/ child links."""
        path = os.path.join(FILES, 'report2.md')
        expected = open(path).read()
        lines = publisher.lines(self.document, '.md')
        text = ''.join(line + '\n' for line in lines)
        if CHECK_EXPORTED_CONTENT:
            self.assertEqual(expected, text)
        with open(path, 'w') as outfile:
            outfile.write(text)

    def test_lines_html_document(self):
        """Verify HTML can be published from a document."""
        path = os.path.join(FILES, 'report.html')
        expected = open(path).read()
        lines = publisher.lines(self.document, '.html')
        text = ''.join(line + '\n' for line in lines)
        if CHECK_EXPORTED_CONTENT:
            self.assertEqual(expected, text)
        with open(path, 'w') as outfile:
            outfile.write(text)

    @patch('doorstop.settings.PUBLISH_CHILD_LINKS', True)
    def test_lines_html_document_with_child_links(self):
        """Verify HTML can be published from a document with child links."""
        path = os.path.join(FILES, 'report2.html')
        expected = open(path).read()
        lines = publisher.lines(self.document, '.html')
        text = ''.join(line + '\n' for line in lines)
        if CHECK_EXPORTED_CONTENT:
            self.assertEqual(expected, text)
        with open(path, 'w') as outfile:
            outfile.write(text)
