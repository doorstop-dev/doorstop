# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.server.client module."""

import unittest
from unittest.mock import Mock, patch

import requests

from doorstop.common import DoorstopError
from doorstop.server import client


@patch('doorstop.settings.SERVER_PORT', 8080)
class TestModule(unittest.TestCase):
    """Unit tests for the doorstop.server.client module."""

    @patch('doorstop.settings.SERVER_HOST', '1.2.3.4')
    def test_exists(self):
        """Verify the client can look for a server."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_head = Mock(return_value=mock_response)
        # Act
        with patch('requests.head', mock_head):
            exists = client.exists()
        # Assert
        url = 'http://1.2.3.4:8080/documents'
        mock_head.assert_called_once_with(url)
        self.assertTrue(exists)

    @patch('doorstop.settings.SERVER_HOST', '1.2.3.4')
    def test_exists_bad_server(self):
        """Verify the client can look for a bad server."""
        mock_head = Mock(side_effect=requests.exceptions.RequestException)
        # Act
        with patch('requests.head', mock_head):
            exists = client.exists()
        # Assert
        url = 'http://1.2.3.4:8080/documents'
        mock_head.assert_called_once_with(url)
        self.assertFalse(exists)

    @patch('doorstop.settings.SERVER_HOST', '1.2.3.4')
    def test_exists_bad_path(self):
        """Verify the client can look for a bad server path."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_head = Mock(return_value=mock_response)
        # Act
        with patch('requests.head', mock_head):
            exists = client.exists()
        # Assert
        url = 'http://1.2.3.4:8080/documents'
        mock_head.assert_called_once_with(url)
        self.assertFalse(exists)

    @patch('doorstop.settings.SERVER_HOST', '')
    def test_exists_unknown(self):
        """Verify the client can look for an empty server."""
        # Act
        exists = client.exists()
        # Assert
        self.assertFalse(exists)

    @patch('doorstop.settings.SERVER_HOST', '1.2.3.4')
    def test_check(self):  # pylint: disable=R0201
        """Verify the client can check a server."""
        with patch('doorstop.server.client.exists', Mock(return_value=True)):
            client.check()

    @patch('doorstop.settings.SERVER_HOST', '1.2.3.4')
    def test_check_bad(self):
        """Verify the client can check a bad server."""
        with patch('doorstop.server.client.exists', Mock(return_value=False)):
            self.assertRaises(DoorstopError, client.check)

    @patch('doorstop.settings.SERVER_HOST', '')
    def test_check_unknown(self):
        """Verify the client can check a disabled server."""
        with patch('doorstop.server.client.exists', Mock(return_value=False)):
            self.assertRaises(DoorstopError, client.check)

    @patch('doorstop.settings.SERVER_HOST', None)
    def test_check_disabled(self):  # pylint: disable=R0201
        """Verify the client can check a disabled server."""
        with patch('doorstop.server.client.exists', Mock(return_value=False)):
            client.check()

    @patch('doorstop.settings.SERVER_HOST', '1.2.3.4')
    def test_get_next_number(self):
        """Verify the client can get the next number for a document."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={'next': 42})
        mock_post = Mock(return_value=mock_response)
        # Act
        with patch('requests.post', mock_post):
            number = client.get_next_number('PREFIX')
        # Assert
        url = 'http://1.2.3.4:8080/documents/PREFIX/numbers'
        headers = {'content-type': 'application/json'}
        mock_post.assert_called_once_with(url, headers=headers)
        self.assertEqual(42, number)

    @patch('doorstop.settings.SERVER_HOST', '')
    def test_get_next_number_no_server(self):
        """Verify the next number for a document is None with no server."""
        self.assertIs(None, client.get_next_number('PREFIX'))

    @patch('doorstop.settings.SERVER_HOST', '1.2.3.4')
    def test_get_next_number_bad_response(self):
        """Verify the client can handle bad responses for the next number."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={})
        mock_post = Mock(return_value=mock_response)
        # Act and assert
        with patch('requests.post', mock_post):
            self.assertRaises(DoorstopError, client.get_next_number, 'PREFIX')
