# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.server.client module."""
import importlib.util
import sys
import unittest
from io import StringIO
from os import sep
from unittest.mock import Mock, patch

import requests

from doorstop.common import DoorstopError
from doorstop.server import client


@patch("doorstop.settings.SERVER_PORT", 8080)
class TestModule(unittest.TestCase):
    """Unit tests for the doorstop.server.client module."""

    @patch("doorstop.settings.SERVER_HOST", "1.2.3.4")
    def test_exists(self):
        """Verify the client can look for a server."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_head = Mock(return_value=mock_response)
        # Act
        with patch("requests.head", mock_head):
            exists = client.exists()
        # Assert
        url = "http://1.2.3.4:8080/documents"
        mock_head.assert_called_once_with(url, timeout=10)
        self.assertTrue(exists)

    @patch("doorstop.settings.SERVER_HOST", "1.2.3.4")
    def test_exists_bad_server(self):
        """Verify the client can look for a bad server."""
        mock_head = Mock(side_effect=requests.exceptions.RequestException)
        # Act
        with patch("requests.head", mock_head):
            exists = client.exists()
        # Assert
        url = "http://1.2.3.4:8080/documents"
        mock_head.assert_called_once_with(url, timeout=10)
        self.assertFalse(exists)

    @patch("doorstop.settings.SERVER_HOST", "1.2.3.4")
    def test_exists_bad_path(self):
        """Verify the client can look for a bad server path."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_head = Mock(return_value=mock_response)
        # Act
        with patch("requests.head", mock_head):
            exists = client.exists()
        # Assert
        url = "http://1.2.3.4:8080/documents"
        mock_head.assert_called_once_with(url, timeout=10)
        self.assertFalse(exists)

    @patch("doorstop.settings.SERVER_HOST", "")
    def test_exists_unknown(self):
        """Verify the client can look for an empty server."""
        # Act
        exists = client.exists()
        # Assert
        self.assertFalse(exists)

    @patch("doorstop.settings.SERVER_HOST", "1.2.3.4")
    def test_check(self):
        """Verify the client can check a server."""
        with patch("doorstop.server.client.exists", Mock(return_value=True)):
            client.check()

    @patch("doorstop.settings.SERVER_HOST", "1.2.3.4")
    def test_check_bad(self):
        """Verify the client can check a bad server."""
        with patch("doorstop.server.client.exists", Mock(return_value=False)):
            self.assertRaises(DoorstopError, client.check)

    @patch("doorstop.settings.SERVER_HOST", "")
    def test_check_unknown(self):
        """Verify the client can check a disabled server."""
        with patch("doorstop.server.client.exists", Mock(return_value=False)):
            self.assertRaises(DoorstopError, client.check)

    @patch("doorstop.settings.SERVER_HOST", None)
    def test_check_disabled(self):
        """Verify the client can check a disabled server."""
        with patch("doorstop.server.client.exists", Mock(return_value=False)):
            client.check()

    @patch("doorstop.settings.SERVER_HOST", "1.2.3.4")
    def test_get_next_number(self):
        """Verify the client can get the next number for a document."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={"next": 42})
        mock_post = Mock(return_value=mock_response)
        # Act
        with patch("requests.post", mock_post):
            number = client.get_next_number("PREFIX")
        # Assert
        url = "http://1.2.3.4:8080/documents/PREFIX/numbers?format=json"
        headers = {"content-type": "application/json"}
        mock_post.assert_called_once_with(url, headers=headers, timeout=10)
        self.assertEqual(42, number)

    @patch("doorstop.settings.SERVER_HOST", "")
    def test_get_next_number_no_server(self):
        """Verify the next number for a document is None with no server."""
        self.assertIs(None, client.get_next_number("PREFIX"))

    @patch("doorstop.settings.SERVER_HOST", "1.2.3.4")
    def test_get_next_number_bad_response(self):
        """Verify the client can handle bad responses for the next number."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json = Mock(return_value={})
        mock_post = Mock(return_value=mock_response)
        # Act and assert
        with patch("requests.post", mock_post):
            self.assertRaises(DoorstopError, client.get_next_number, "PREFIX")

    def test_main_no_args(self):
        """Verify the main client function will return an error if no arguments are given."""
        # Run the main function without arguments.
        testargs = [sep.join(["doorstop", "server", "client.py"])]
        with patch.object(sys, "argv", testargs):
            spec = importlib.util.spec_from_file_location("__main__", testargs[0])
            runpy = importlib.util.module_from_spec(spec)
            # Assert that the main function exits.
            with self.assertRaises(SystemExit):
                spec.loader.exec_module(runpy)
            # Assert
            self.assertIsNotNone(runpy)

    @patch("sys.stdout", new_callable=StringIO)
    @patch("doorstop.server.client.get_next_number", Mock(return_value=100))
    @patch("doorstop.settings.SERVER_HOST", "1.2.3.4")
    def test_main_one_arg(self, stdout):
        """Verify the main client function will return a value if called with one argument."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={"next": 422})
        mock_post = Mock(return_value=mock_response)

        # Run the main function with one argument.
        testargs = [sep.join(["doorstop", "server", "client.py"]), "PREFIX"]
        with patch.object(sys, "argv", testargs):
            spec = importlib.util.spec_from_file_location("__main__", testargs[0])
            runpy = importlib.util.module_from_spec(spec)
            # Assert that the main function exits.
            with patch("requests.post", mock_post):
                spec.loader.exec_module(runpy)
            # Assert
            self.assertIsNotNone(runpy)

        # Assert that the version number is correct.
        self.assertEqual("422\n", stdout.getvalue())
