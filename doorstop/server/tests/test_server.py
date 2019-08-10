# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.server.main module."""

import unittest
from unittest.mock import MagicMock, Mock, patch

from doorstop.server import main as server


class BaseTestCase(unittest.TestCase):
    """Base test class for server tests."""

    mock_item = MagicMock()
    mock_item.uid = 'UID'
    mock_item.data = {'links': ['UID3', 'UID4'], 'text': 'TEXT'}

    mock_item2 = Mock()
    mock_item2.uid = 'UID2'
    mock_item2.data = {}

    mock_document = MagicMock()
    mock_document.__iter__.return_value = [mock_item, mock_item2]
    mock_document.prefix = 'PREFIX'
    mock_document.next_number = 42
    mock_document.find_item = Mock(return_value=mock_item)

    mock_document2 = MagicMock()
    mock_document2.__iter__.return_value = []
    mock_document2.prefix = 'PREFIX2'

    mock_tree = MagicMock()
    mock_tree.__iter__.return_value = [mock_document, mock_document2]
    mock_tree.find_document = Mock(return_value=mock_document)
    mock_tree.find_item = Mock(return_value=mock_item)

    def setUp(self):
        self.server = server
        self.server.tree = self.mock_tree


class TestModule(BaseTestCase):
    """Unit tests for the doorstop.server.main module."""

    @patch('doorstop.server.main.build')
    @patch('bottle.run')
    def test_main(self, mock_run, mock_build):
        """Verify the server can started (mock)."""
        self.server.main([])
        self.assertEqual(1, mock_build.call_count)
        self.assertEqual(1, mock_run.call_count)

    @patch('doorstop.settings.SERVER_PORT', 8080)
    @patch('doorstop.server.main.build')
    @patch('webbrowser.open')
    @patch('bottle.run')
    def test_main_debug(self, mock_run, mock_open, mock_build):
        """Verify the server can started (mock, debug)."""
        self.server.main(['--debug', '--launch'])
        self.assertEqual(1, mock_build.call_count)
        mock_open.assert_called_once_with("http://127.0.0.1:8080")
        self.assertEqual(1, mock_run.call_count)


class TestRoutesHTML(BaseTestCase):
    """Unit tests for the doorstop.server.main module HTML responses."""

    def test_get_index(self):
        """Verify `/` works (HTML)."""
        for line in self.server.index():
            print(line)
        self.mock_tree.draw.assert_called_once_with(html_links=True)

    def test_get_documents(self):
        """Verify `/documents` works (HTML)."""
        text = server.get_documents()
        self.assertIn("PREFIX", text)
        self.assertIn("PREFIX2", text)

    def test_get_document(self):  # pylint: disable=R0201
        """Verify `/document/PREFIX` works (HTML)."""
        for line in server.get_document('prefix'):
            print(line)

    def test_get_all_documents(self):  # pylint: disable=R0201
        """Verify `/document/all` works (HTML)."""
        for line in server.get_all_documents():
            print(line)

    def test_get_items(self):
        """Verify `/document/PREFIX/items` works (HTML)."""
        text = server.get_items('prefix')
        self.assertIn("UID", text)
        self.assertIn("UID2", text)

    def test_get_item(self):  # pylint: disable=R0201
        """Verify `/document/PREFIX/items/UID` works (HTML)."""
        for line in server.get_item('prefix', 'uid'):
            print(line)

    def test_get_attrs(self):
        """Verify `/document/PREFIX/items/UID/attrs` works (HTML)."""
        text = server.get_attrs('prefix', 'uid')
        self.assertEqual("links<br>text", text)

    def test_get_attr(self):
        """Verify `/document/PREFIX/items/UID/attrs/NAME` works (HTML)."""
        text = server.get_attr('prefix', 'uid', 'name')
        self.assertEqual("None", text)

    def test_get_attr_str(self):
        """Verify `/document/PREFIX/items/UID/attrs/NAME:str` works (HTML)."""
        text = server.get_attr('prefix', 'uid', 'text')
        self.assertEqual("TEXT", text)

    def test_get_attr_list(self):
        """Verify `/document/PREFIX/items/UID/attrs/NAME:list` works (HTML)."""
        text = server.get_attr('prefix', 'uid', 'links')
        self.assertEqual("UID3<br>UID4", text)

    def test_post_numbers(self):
        """Verify `/document/PREFIX/numbers` works (HTML)."""
        text = server.post_numbers('prefix')
        self.assertEqual("42", text)
        self.assertEqual(43, self.server.numbers['prefix'])


@patch('doorstop.server.utilities.json_response', Mock(return_value=True))
class TestRoutesJSON(BaseTestCase):
    """Unit tests for the doorstop.server.main module JSON responses."""

    def test_get_documents(self):
        """Verify `/documents` works (JSON)."""
        data = self.server.get_documents()
        self.assertEqual({'prefixes': ['PREFIX', 'PREFIX2']}, data)

    def test_get_document(self):
        """Verify `/document/PREFIX` works (JSON)."""
        data = server.get_document('prefix')
        self.assertEqual(
            {'UID': {'links': ['UID3', 'UID4'], 'text': 'TEXT'}, 'UID2': {}}, data
        )

    def test_get_all_documents(self):
        """Verify `/documents/all` works (JSON)."""
        data = server.get_all_documents()
        expected = {
            'PREFIX': {'UID': {'links': ['UID3', 'UID4'], 'text': 'TEXT'}, 'UID2': {}},
            'PREFIX2': {},
        }
        self.assertEqual(expected, data)

    def test_get_items(self):
        """Verify `/document/PREFIX/items` works (JSON)."""
        data = server.get_items('prefix')
        self.assertEqual({'uids': ['UID', 'UID2']}, data)

    def test_get_item(self):
        """Verify `/document/PREFIX/items/UID` works (JSON)."""
        data = server.get_item('prefix', 'uid')
        self.assertEqual({'data': {'links': ['UID3', 'UID4'], 'text': 'TEXT'}}, data)

    def test_get_attrs(self):
        """Verify `/document/PREFIX/items/UID/attrs` works (JSON)."""
        data = server.get_attrs('prefix', 'uid')
        self.assertEqual({'attrs': ['links', 'text']}, data)

    def test_get_attr(self):
        """Verify `/document/PREFIX/items/UID/attrs/NAME` works (JSON)."""
        data = server.get_attr('prefix', 'uid', 'name')
        self.assertEqual({'value': None}, data)

    def test_get_attr_str(self):
        """Verify `/document/PREFIX/items/UID/attrs/NAME:str` works (JSON)."""
        data = server.get_attr('prefix', 'uid', 'text')
        self.assertEqual({'value': 'TEXT'}, data)

    def test_get_attr_list(self):
        """Verify `/document/PREFIX/items/UID/attrs/NAME:list` works (JSON)."""
        data = server.get_attr('prefix', 'uid', 'links')
        self.assertEqual({'value': ['UID3', 'UID4']}, data)

    @patch('doorstop.server.main.numbers', {'prefix': 123})
    def test_post_numbers(self):
        """Verify `/document/PREFIX/numbers` works (JSON)."""
        data = server.post_numbers('prefix')
        self.assertEqual({'next': 123}, data)
