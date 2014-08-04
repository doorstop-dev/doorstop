"""Unit tests for the doorstop.web.server package."""

import unittest
from unittest.mock import patch, Mock


from doorstop.web import server

mock_item = Mock()
mock_document = Mock()
mock_tree = Mock()


@patch.object(server, 'tree', mock_tree)
class TestModule(unittest.TestCase):  # pylint: disable=R0904

    """Unit tests for the doorstop.web.server module."""

    def test_get_tree(self):
        """Verify `/` works."""
        text = server.get_tree()
        mock_tree.draw.assert_called_once_with()

    def test_get_documents(self):
        """Verify `/documents` works."""
        text = server.get_documents()
        self.assertEqual("", text)
