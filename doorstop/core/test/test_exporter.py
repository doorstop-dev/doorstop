"""Unit tests for the doorstop.core.exporter module."""

import unittest
from unittest.mock import patch, MagicMock

import os
import tempfile

from doorstop.common import DoorstopError
from doorstop.core import exporter

from doorstop.core.test import MockDataMixIn


class TestModule(MockDataMixIn, unittest.TestCase):  # pylint: disable=R0904

    """Unit tests for the doorstop.core.exporter module."""  # pylint: disable=C0103

    @patch('os.makedirs')
    @patch('doorstop.core.exporter.create')
    def test_export_document(self, mock_create, mock_makedirs):
        """Verify a document can be exported."""
        dirpath = os.path.join('mock', 'directory')
        path = os.path.join(dirpath, 'exported.xlsx')
        # Act
        exporter.export(self.document, path)
        # Assert
        mock_makedirs.assert_called_once_with(dirpath)
        mock_create.assert_called_once_with(self.document, path, '.xlsx')

    def test_export_document_unknown(self):
        """Verify an exception is raised when exporting unknown formats."""
        self.assertRaises(DoorstopError,
                          exporter.export, self.document, 'a.a')
        self.assertRaises(DoorstopError,
                          exporter.export, self.document, 'a.yml', '.a')

    @patch('os.makedirs')
    @patch('builtins.open')
    def test_export_tree(self, mock_open, mock_makedirs):
        """Verify a tree can be exported."""
        dirpath = os.path.join('mock', 'directory')
        mock_document = MagicMock()
        mock_document.prefix = 'MOCK'
        mock_document.items = []
        mock_tree = MagicMock()
        mock_tree.documents = [mock_document]
        # Act
        exporter.export(mock_tree, dirpath)
        # Assert
        self.assertEqual(1, mock_makedirs.call_count)
        self.assertEqual(1, mock_open.call_count)

    def test_lines(self):
        """Verify an item can be exported as lines."""
        expected = ("req3:" + '\n'
                    "  active: true" + '\n'
                    "  derived: false" + '\n'
                    "  level: 1.1.0" + '\n'
                    "  links: [sys3]" + '\n'
                    "  normative: false" + '\n'
                    "  ref: ''" + '\n'
                    "  text: |" + '\n' +
                    "    Heading" + '\n\n')
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
        temp = tempfile.gettempdir()
        path = os.path.join(temp, 'exported.tsv')
        # Act
        exporter.file_tsv(self.item, path)
        # Assert
        mock_file_csv.assert_called_once_with(self.item, path, delimiter='\t')

    @patch('doorstop.core.exporter._get_xlsx')
    def test_file_xlsx(self, mock_get_xlsx):
        """Verify a (mock) XLSX file can be created."""
        temp = tempfile.gettempdir()
        path = os.path.join(temp, 'exported.xlsx')
        # Act
        exporter.file_xlsx(self.item, path)
        # Assert
        mock_get_xlsx.assert_called_once_with(self.item)

    def test_get_xlsx(self):
        """Verify an XLSX object can be created."""
        # Act
        workbook = exporter._get_xlsx(self.item4)  # pylint: disable=W0212
        # Assert
        rows = []
        worksheet = workbook.active
        for data in worksheet.rows:
            rows.append([cell.value for cell in data])
        self.assertIn('long', rows[0])
        self.assertEqual('req3', rows[1][0])
