# SPDX-License-Identifier: LGPL-3.0-only

"""Integration tests for the doorstop.server package."""

import logging
import os
import time
import unittest
from multiprocessing import Process
from unittest.mock import patch

import requests

from doorstop import server
from doorstop.server import main
from doorstop.server.tests import ENV, REASON


@unittest.skipUnless(os.getenv(ENV), REASON)
@patch("doorstop.settings.SERVER_HOST", "localhost")
class TestServer(unittest.TestCase):
    """Integration tests for the client/server feature.

    These tests are vital for verifying that the server works as expected.
    Unfortunately, there is currently no way to measure the code coverage of
    these tests because the server is started in a separate process.
    """

    @classmethod
    def setUpClass(cls):
        if os.getenv(ENV):
            cls.process = Process(target=main.main, kwargs={"args": []})
            cls.process.start()
            logging.info("waiting for the server to initialize...")
            # Check for response!
            cls.base_url = "http://localhost:7867"
            url = "{}/documents".format(cls.base_url)
            for _ in range(0, 29):
                try:
                    _ = requests.head(url, timeout=10)
                    break
                except requests.exceptions.RequestException:
                    time.sleep(1)
            logging.info("server is answering!")
            assert cls.process.is_alive()

    @classmethod
    def tearDownClass(cls):
        if os.getenv(ENV):
            cls.process.terminate()
            logging.info("delaying for the server to shutdown...")
            time.sleep(1)

    def make_the_call(self, url):
        """Make a call to the server, with timeout."""
        for _ in range(0, 29):
            try:
                response = requests.get(url, timeout=10)
                break
            except requests.exceptions.RequestException:
                time.sleep(1)
        return response

    def test_check(self):
        """Verify the server can be checked."""
        server.check()

    def test_get_next_number(self):
        """Verify the next number can be requested from the server."""
        number1 = server.get_next_number("req")
        number2 = server.get_next_number("req")
        self.assertIsNot(None, number1)
        self.assertIsNot(None, number2)
        self.assertLess(number1, number2)

    def test_get_index(self):
        """Verify the index can be requested from the server."""
        url = "{}/index.html".format(self.base_url)
        response = self.make_the_call(url)
        self.assertIn("<title>Index</title>", response.text)
        self.assertGreater(len(response.text), 3000)

    def test_get_documents_end_slash(self):
        """Verify the documents/ and that / is stripped."""
        url = "{}/documents/".format(self.base_url)
        response = self.make_the_call(url)
        self.assertIn("<title>Documents</title>", response.text)
        self.assertGreater(len(response.text), 300)

    def test_get_req_with_extension(self):
        """Verify the a document can be requested from the server."""
        url = "{}/documents/REQ.html".format(self.base_url)
        response = self.make_the_call(url)
        self.assertIn("<title>Requirements</title>", response.text)
        self.assertGreater(len(response.text), 3000)

    def test_get_req_no_extension(self):
        """Verify the a document can be requested from the server."""
        url = "{}/documents/REQ".format(self.base_url)
        response = self.make_the_call(url)
        self.assertIn("<title>Requirements</title>", response.text)
        self.assertGreater(len(response.text), 3000)

    def test_get_traceabilty(self):
        """Verify the the traceability can be requested from the server."""
        url = "{}/traceability".format(self.base_url)
        response = self.make_the_call(url)
        self.assertIn("<title>Traceability</title>", response.text)
        self.assertGreater(len(response.text), 3000)
