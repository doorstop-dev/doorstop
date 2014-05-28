"""Unit tests for the doorstop.core.exporter module."""

import unittest
from unittest.mock import patch, Mock, MagicMock

import os
import csv
import tempfile
import shutil
import logging

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


def read_csv(path):
    """Return a list of rows from a CSV file."""
    rows = []
    try:
        with open(path, 'r', newline='') as stream:
            reader = csv.reader(stream)
            for row in reader:
                rows.append(row)
    except FileNotFoundError:
        logging.warning("file not found: {}".format(path))
    return rows


def move_file(src, dst):
    """Move a file from one path to another."""
    try:
        os.remove(dst)
    except FileNotFoundError:
        pass
    shutil.move(src, dst)


@unittest.skipUnless(os.getenv(ENV) or not CHECK_EXPORTED_CONTENT, REASON)  # pylint: disable=R0904
class TestModuleIntegration(BaseTestCase):  # pylint: disable=R0904

    """Integration tests for the doorstop.core.exporter module."""  # pylint: disable=C0103

    def test_export_csv(self):
        """Verify a document can be exported as a CSV file."""
        path = os.path.join(FILES, 'exported.csv')
        temp = os.path.join(FILES, 'exported.temp.csv')
        expected = read_csv(path)
        # Act
        exporter.export(self.document, temp)
        # Assert
        if CHECK_EXPORTED_CONTENT:
            actual = read_csv(temp)
            self.assertEqual(expected, actual)
        move_file(temp, path)
