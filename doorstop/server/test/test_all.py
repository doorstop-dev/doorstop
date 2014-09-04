"""Integration tests for the doorstop.web package."""

import unittest
from unittest.mock import patch
from multiprocessing import Process

from doorstop.server import main
from doorstop.server import check, get_next_number


# @unittest.skipUnless(os.getenv(ENV), REASON)
@patch('doorstop.settings.SERVER_HOST', 'localhost')
class TestServer(unittest.TestCase):

    """Integration tests for the client/server feature."""

    def setUp(self):
        self.process = Process(target=main.main)
        self.process.start()

    def tearDown(self):
        self.process.terminate()

    def test_check(self):
        """Verify the server can be checked."""
        self.assertTrue(self.process.is_alive())
        check()

    def test_get_next_number(self):
        """Verify the next number can be requested from the server."""
        self.assertTrue(self.process.is_alive())
        number = get_next_number('req')
        number2 = get_next_number('req')
        self.assertIsNot(None, number)
        self.assertIsNot(None, number2)
        self.assertGreater(number, number2)
