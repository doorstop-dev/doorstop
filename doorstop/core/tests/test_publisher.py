# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.core.publisher module."""

# pylint: disable=unused-argument,protected-access

import os
import unittest
from secrets import token_hex
from shutil import rmtree
from unittest import mock
from unittest.mock import Mock, call, patch

from doorstop.common import DoorstopError
from doorstop.core import publisher
from doorstop.core.tests import MockDataMixIn


class TestModule(MockDataMixIn, unittest.TestCase):
    """Unit tests for the doorstop.core.publisher module."""

    # pylint: disable=no-value-for-parameter
    def setUp(self):
        """Setup test folder."""
        self.hex = token_hex()
        self.dirpath = os.path.abspath(os.path.join("mock_%s" % __name__, self.hex))

    @classmethod
    def tearDownClass(cls):
        """Remove test folder."""
        rmtree("mock_%s" % __name__)

    @patch("os.path.isdir", Mock(side_effect=[False, False, False, False]))
    @patch("os.makedirs")
    @patch("builtins.open")
    def test_publish_document(self, mock_open, mock_makedirs):
        """Verify a document can be published."""
        path = os.path.join(self.dirpath, "published.html")
        self.document.items = []
        # Act
        path2 = publisher.publish(self.document, path)
        # Assert
        self.assertIs(path, path2)
        mock_makedirs.assert_called_once_with(self.dirpath)
        mock_open.assert_called_once_with(path, "wb")

    def test_publish_document_unknown(self):
        """Verify an exception is raised when publishing unknown formats."""
        self.assertRaises(DoorstopError, publisher.publish, self.document, "a.a")
        self.assertRaises(
            DoorstopError, publisher.publish, self.document, "a.txt", ".a"
        )

    @patch("os.path.isdir", Mock(return_value=False))
    @patch("os.makedirs")
    @patch("doorstop.core.publisher._index")
    @patch("builtins.open")
    def test_publish_tree(self, mock_open, mock_index, mock_makedirs):
        """Verify a tree can be published."""
        mock_open.side_effect = lambda *args, **kw: mock.mock_open(
            read_data="$body"
        ).return_value
        expected_calls = [
            call(os.path.join(self.dirpath, "MOCK.html"), "wb"),
            call(
                os.path.join(self.dirpath, "traceability.csv"),
                "w",
                encoding="utf-8",
                newline="",
            ),
        ]
        # Act
        dirpath2 = publisher.publish(self.mock_tree, self.dirpath)
        # Assert
        self.assertIs(self.dirpath, dirpath2)
        self.assertEqual(expected_calls, mock_open.call_args_list)
        mock_index.assert_called_once_with(self.dirpath, tree=self.mock_tree)

    @patch("os.path.isdir", Mock(return_value=False))
    @patch("os.makedirs")
    @patch("doorstop.core.publisher._index")
    @patch("builtins.open")
    def test_publish_tree_no_index(self, mock_open, mock_index, mock_makedirs):
        """Verify a tree can be published."""
        mock_open.side_effect = lambda *args, **kw: mock.mock_open(
            read_data="$body"
        ).return_value
        expected_calls = [call(os.path.join(self.dirpath, "MOCK.html"), "wb")]
        # Act
        dirpath2 = publisher.publish(self.mock_tree, self.dirpath, index=False)
        # Assert
        self.assertIs(self.dirpath, dirpath2)
        self.assertEqual(0, mock_index.call_count)
        self.assertEqual(expected_calls, mock_open.call_args_list)

    def test_lines_text_item(self):
        """Verify text can be published from an item."""
        with patch.object(
            self.item5, "find_ref", Mock(return_value=("path/to/mock/file", 42))
        ):
            lines = publisher.publish_lines(self.item5, ".txt")
            text = "".join(line + "\n" for line in lines)
        self.assertIn("Reference: path/to/mock/file (line 42)", text)
