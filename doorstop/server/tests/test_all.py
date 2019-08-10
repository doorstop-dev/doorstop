# SPDX-License-Identifier: LGPL-3.0-only

"""Integration tests for the doorstop.server package."""

import logging
import os
import time
import unittest
from multiprocessing import Process
from unittest.mock import patch

from doorstop import server
from doorstop.server import main
from doorstop.server.tests import ENV, REASON


@unittest.skipUnless(os.getenv(ENV), REASON)
@patch('doorstop.settings.SERVER_HOST', 'localhost')
class TestServer(unittest.TestCase):
    """Integration tests for the client/server feature."""

    @classmethod
    def setUpClass(cls):
        if os.getenv(ENV):
            cls.process = Process(target=main.main, kwargs={'args': []})
            cls.process.start()
            logging.info("delaying for the server to initialize...")
            time.sleep(3)
            assert cls.process.is_alive()

    @classmethod
    def tearDownClass(cls):
        if os.getenv(ENV):
            cls.process.terminate()
            logging.info("delaying for the server to shutdown...")
            time.sleep(1)

    def test_check(self):  # pylint: disable=R0201
        """Verify the server can be checked."""
        server.check()

    def test_get_next_number(self):
        """Verify the next number can be requested from the server."""
        number1 = server.get_next_number('req')
        number2 = server.get_next_number('req')
        self.assertIsNot(None, number1)
        self.assertIsNot(None, number2)
        self.assertLess(number1, number2)
