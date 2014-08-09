"""Unit tests for the doorstop.web.client package."""

import unittest
from unittest.mock import patch, Mock

from doorstop.server import client


class TestModule(unittest.TestCase):

    """Unit tests for the doorstop.web.client module."""

    def test_get_next_number(self):
        """Verify the client can get the next number for a document."""
        mock_response = Mock()
        mock_response.json = Mock(return_value={'next': 42})
        mock_post = Mock(return_value=mock_response)
        # Act
        with patch('requests.post', mock_post):
            number = client.get_next_number('PREFIX')
        # Assert
        url = 'http://127.0.0.1:8080/documents/PREFIX/numbers'
        headers = {'content-type': 'application/json'}
        mock_post.assert_called_once_with(url, headers=headers)
        self.assertEqual(42, number)
