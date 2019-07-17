# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.core.exporter module."""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, Mock, patch

from doorstop.common import DoorstopError
from doorstop.core import exporter
from doorstop.core.tests import MockDataMixIn


class TestModule(MockDataMixIn, unittest.TestCase):
    """Unit tests for the doorstop.core.exporter module."""

    @patch('os.path.isdir', Mock(return_value=False))
    @patch('os.makedirs')
    @patch('doorstop.core.exporter.export_file')
    def test_export_document(self, mock_export_file, mock_makedirs):
        """Verify a document can be exported."""
        dirpath = os.path.join('mock', 'directory')
        path = os.path.join(dirpath, 'exported.xlsx')
        # Act
        path2 = exporter.export(self.document, path)
        # Assert
        self.assertIs(path, path2)
        mock_makedirs.assert_called_once_with(dirpath)
        mock_export_file.assert_called_once_with(self.document, path, '.xlsx')

    def test_export_document_unknown(self):
        """Verify an exception is raised when exporting unknown formats."""
        self.assertRaises(DoorstopError, exporter.export, self.document, 'a.a')
        self.assertRaises(DoorstopError, exporter.export, self.document, 'a.yml', '.a')

    @patch('os.path.isdir', Mock(return_value=False))
    @patch('os.makedirs')
    @patch('builtins.open')
    def test_export_tree(self, mock_open, mock_makedirs):
        """Verify a tree can be exported."""
        dirpath = os.path.join('mock', 'directory')
        # Act
        dirpath2 = exporter.export(self.mock_tree, dirpath)
        # Assert
        self.assertIs(dirpath, dirpath2)
        self.assertEqual(1, mock_makedirs.call_count)
        self.assertEqual(1, mock_open.call_count)

    @patch('os.makedirs')
    @patch('builtins.open')
    def test_export_tree_no_documents(self, mock_open, mock_makedirs):
        """Verify a tree can be exported."""
        dirpath = os.path.join('mock', 'directory')
        mock_tree = MagicMock()
        mock_tree.documents = []
        # Act
        dirpath2 = exporter.export(mock_tree, dirpath)
        # Assert
        self.assertIs(None, dirpath2)
        self.assertEqual(0, mock_makedirs.call_count)
        self.assertEqual(0, mock_open.call_count)

    @patch('os.path.isdir', Mock(return_value=False))
    @patch('os.makedirs')
    @patch('doorstop.common.write_lines')
    def test_export_document_lines(self, mock_write_lines, mock_makedirs):
        """Verify a document can be exported (lines to file)."""
        dirpath = os.path.join('mock', 'directory')
        path = os.path.join(dirpath, 'exported.custom')
        # Act
        path2 = exporter.export(self.document, path, ext='.yml')
        # Assert
        self.assertIs(path, path2)
        mock_makedirs.assert_called_once_with(dirpath)
        self.assertEqual(1, mock_write_lines.call_count)

    def test_lines(self):
        """Verify an item can be exported as lines."""
        expected = (
            "req3:" + '\n'
            "  active: true" + '\n'
            "  derived: false" + '\n'
            "  header: ''" + '\n'
            "  level: 1.1.0" + '\n'
            "  links:" + '\n'
            "  - sys3: null" + '\n'
            "  normative: false" + '\n'
            "  ref: ''" + '\n'
            "  reviewed: null" + '\n'
            "  text: |" + '\n'
            "    Heading" + '\n\n'
        )
        # Act
        lines = exporter.export_lines(self.item)
        text = ''.join(line + '\n' for line in lines)
        # Assert
        self.assertEqual(expected, text)

    def test_lines_unknown(self):
        """Verify an exception is raised when iterating an unknown format."""
        # Act
        gen = exporter.export_lines(self.document, '.a')
        # Assert
        self.assertRaises(DoorstopError, list, gen)

    def test_export_file(self):
        """Verify an item can be exported as a file."""
        temp = tempfile.mkdtemp()
        path = os.path.join(temp, 'exported.csv')
        # Act
        exporter.export_file(self.item, path)
        # Assert
        self.assertTrue(os.path.isfile(path))

    def test_export_file_unknown(self):
        """Verify an item can be exported as a file."""
        self.assertRaises(DoorstopError, exporter.export_file, self.document, 'a.a')
        self.assertRaises(
            DoorstopError, exporter.export_file, self.document, 'a.csv', '.a'
        )

    @patch('doorstop.core.exporter._file_csv')
    def test_file_tsv(self, mock_file_csv):
        """Verify a (mock) TSV file can be created."""
        temp = tempfile.gettempdir()
        path = os.path.join(temp, 'exported.tsv')
        # Act
        exporter._file_tsv(self.item, path)  # pylint:disable=W0212
        # Assert
        mock_file_csv.assert_called_once_with(
            self.item, path, delimiter='\t', auto=False
        )

    @patch('doorstop.core.exporter._get_xlsx')
    def test_file_xlsx(self, mock_get_xlsx):
        """Verify a (mock) XLSX file can be created."""
        temp = tempfile.gettempdir()
        path = os.path.join(temp, 'exported.xlsx')
        # Act
        exporter._file_xlsx(self.item, path)  # pylint:disable=W0212
        # Assert
        mock_get_xlsx.assert_called_once_with(self.item, False)

    def test_get_xlsx(self):
        """Verify an XLSX object can be created."""
        # Act
        workbook = exporter._get_xlsx(self.item4, auto=False)  # pylint: disable=W0212
        # Assert
        rows = []
        worksheet = workbook.active
        for data in worksheet.rows:
            rows.append([cell.value for cell in data])
        self.assertIn('long', rows[0])
        self.assertEqual('req3', rows[1][0])

    def test_get_xlsx_auto(self):
        """Verify an XLSX object can be created with placeholder rows."""
        # Act
        workbook = exporter._get_xlsx(self.item4, auto=True)  # pylint: disable=W0212
        # Assert
        rows = []
        worksheet = workbook.active
        for data in worksheet.rows:
            rows.append([cell.value for cell in data])
        self.assertEqual("...", rows[-1][0])
