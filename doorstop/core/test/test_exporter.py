"""Unit tests for the doorstop.core.exporter module."""

import unittest
from unittest.mock import patch

import os
import csv
import tempfile
import shutil
import logging

import openpyxl

from doorstop.common import DoorstopError
from doorstop.core import exporter

from doorstop.core.test import FILES, ENV, REASON
from doorstop.core.test.test_publisher import BaseTestCase

# Whenever the export format is changed:
#  1. set CHECK_EXPORTED_CONTENT to False
#  2. re-run all tests
#  3. manually verify the newly exported content is correct
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

    @patch('doorstop.core.exporter.file_csv')
    def test_file_tsv(self, mock_file_csv):
        """Verify a (mock) TSV file can be created."""
        temp = tempfile.mkdtemp()
        path = os.path.join(temp, 'exported.tsv')
        # Act
        exporter.file_tsv(self.item, path)
        # Assert
        mock_file_csv.assert_called_once_with(self.item, path, delimiter='\t')


def read_csv(path, delimiter=','):
    """Return a list of rows from a CSV file."""
    rows = []
    try:
        with open(path, 'r', newline='') as stream:
            reader = csv.reader(stream, delimiter=delimiter)
            for row in reader:
                rows.append(row)
    except FileNotFoundError:
        logging.warning("file not found: {}".format(path))
    return rows


def read_xlsx(path):
    """Return a list of rows from a CSV file."""
    rows = []
    try:
        workbook = openpyxl.load_workbook(path)
        worksheet = workbook.active
        for data in worksheet.rows:
            rows.append([cell.value for cell in data])
    except openpyxl.exceptions.InvalidFileException:
        logging.warning("file not found: {}".format(path))
    return rows


def move_file(src, dst):
    """Move a file from one path to another."""
    try:
        os.remove(dst)
    except FileNotFoundError:
        pass
    shutil.move(src, dst)


# TODO: move this to test_all.py and use real objects
@unittest.skipUnless(os.getenv(ENV) or not CHECK_EXPORTED_CONTENT, REASON)  # pylint: disable=R0904
class TestModuleIntegration(BaseTestCase):  # pylint: disable=R0904

    """Integration tests for the doorstop.core.exporter module."""  # pylint: disable=C0103

    def setUp(self):
        self.temp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp)

    def test_export_csv(self):
        """Verify a document can be exported as a CSV file."""
        path = os.path.join(FILES, 'exported.csv')
        temp = os.path.join(self.temp, 'exported.csv')
        expected = read_csv(path)
        # Act
        exporter.export(self.document, temp)
        # Assert
        if CHECK_EXPORTED_CONTENT:
            actual = read_csv(temp)
            self.assertEqual(expected, actual)
        move_file(temp, path)

    def test_export_tsv(self):
        """Verify a document can be exported as a TSV file."""
        path = os.path.join(FILES, 'exported.tsv')
        temp = os.path.join(self.temp, 'exported.tsv')
        expected = read_csv(path, delimiter='\t')
        # Act
        exporter.export(self.document, temp)
        # Assert
        if CHECK_EXPORTED_CONTENT:
            actual = read_csv(temp, delimiter='\t')
            self.assertEqual(expected, actual)
        move_file(temp, path)

    def test_export_xlsx(self):
        """Verify a document can be exported as an XLSX file."""
        path = os.path.join(FILES, 'exported.xlsx')
        temp = os.path.join(self.temp, 'exported.xlsx')
        expected = read_xlsx(path)
        # Act
        exporter.export(self.document, temp)
        # Assert
        if CHECK_EXPORTED_CONTENT:
            actual = read_xlsx(temp)
            self.assertEqual(expected, actual)
        else:  # binary file always changes, only copy when not checking
            move_file(temp, path)
