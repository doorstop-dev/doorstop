# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.server.main module including decorators."""

import unittest

from webtest import TestApp

from doorstop.server.main import app, main


class TestAPIHtml(unittest.TestCase):
    """Test the server API calls, including the Bottle decorators with HTML responses."""

    def setUp(self):
        """Test setup."""
        # Wrap the real app in a TestApp object.
        self.app = TestApp(app)

        # Create a standard argument list.
        # Set as wsgi so that the server doesn't try to launch.
        self.args = ["--wsgi"]

        # Initialize the server.
        main(self.args)

    def test_get_root(self):
        """Test GET /"""
        # Simulate a call (HTTP GET).
        response = self.app.get("/")

        # Validate the response.
        self.assertIn("<title>Index</title>", response.text)
        self.assertGreater(len(response.text), 3000)

    def test_get_index(self):
        """Test GET /index.html"""
        # Simulate a call (HTTP GET).
        response = self.app.get("/index.html")

        # Validate the response.
        self.assertIn("<title>Index</title>", response.text)
        self.assertGreater(len(response.text), 3000)

    def test_get_traceabilty(self):
        """Test GET /traceability.html"""
        # Simulate a call (HTTP GET).
        response = self.app.get("/traceability.html")

        # Validate the response.
        self.assertIn("<title>Traceability</title>", response.text)
        self.assertGreater(len(response.text), 3000)

    def test_get_traceabilty_no_html(self):
        """Test GET /traceability"""
        # Simulate a call (HTTP GET).
        response = self.app.get("/traceability")

        # Validate the response.
        self.assertIn("<title>Traceability</title>", response.text)
        self.assertGreater(len(response.text), 3000)

    def test_get_traceabilty_slash(self):
        """Test GET /traceability/"""
        # Simulate a call (HTTP GET).
        response = self.app.get("/traceability/")

        # Validate the response.
        self.assertIn("<title>Traceability</title>", response.text)
        self.assertGreater(len(response.text), 3000)

    def test_get_documents(self):
        """Test GET /documents/"""
        # Simulate a call (HTTP GET).
        response = self.app.get("/documents/")

        # Validate the response.
        self.assertIn("<title>Documents</title>", response.text)
        self.assertGreater(len(response.text), 500)

    def test_get_documents_all(self):
        """Test GET /documents/all"""
        # Simulate a call (HTTP GET).
        response = self.app.get("/documents/all")

        # Validate the response.
        self.assertIn("<title>Documents</title>", response.text)
        self.assertGreater(len(response.text), 500)

    def test_get_documents_req(self):
        """Test GET /documents/REQ"""
        # Simulate a call (HTTP GET).
        response = self.app.get("/documents/REQ")

        # Validate the response.
        self.assertIn("<title>Requirements</title>", response.text)
        self.assertGreater(len(response.text), 5000)

    def test_get_req_items(self):
        """Test GET /documents/REQ/items"""
        # Simulate a call (HTTP GET).
        response = self.app.get("/documents/REQ/items")

        # Validate the response.
        self.assertIn("<title>Items</title>", response.text)
        self.assertGreater(len(response.text), 500)

    def test_get_req_single_item(self):
        """Test GET /documents/REQ/items/req001"""
        # Simulate a call (HTTP GET).
        response = self.app.get("/documents/REQ/items/req001")

        # Validate the response.
        self.assertIn(
            "Doorstop <strong>shall</strong> support the storage of external requirements assets.",
            response.text,
        )

    def test_get_item_attributes(self):
        """Test GET /documents/REQ/items/req001/attrs"""
        # Simulate a call (HTTP GET).
        response = self.app.get("/documents/REQ/items/req001/attrs")

        # Validate the response.
        self.assertIn("reviewed", response.text)

    def test_get_item_attribute_reviewed(self):
        """Test GET /documents/REQ/items/req001/attrs/reviewed"""
        # Simulate a call (HTTP GET).
        response = self.app.get("/documents/REQ/items/req001/attrs/reviewed")

        # Validate the response.
        self.assertEqual(len(response.text), 44)

    def test_create_next_item(self):
        """Test POST /documents/REQ/numbers"""
        # Simulate a call (HTTP POST).
        response = self.app.post("/documents/REQ/numbers")

        # Validate the response. (Hard coded to 20 as currently REQ019 is the last one.)
        self.assertEqual("20", response.text)

    def test_get_template_file(self):
        """Test GET /template/doorstop.css"""
        # Simulate a call (HTTP GET).
        response = self.app.get("/template/doorstop.css")

        # Validate the response.
        self.assertIn("/* Doorstop.css file. */", response.text)
        self.assertGreater(len(response.text), 50)

    def test_get_assets_file(self):
        """Test GET /documents/assets/logo-black-white.png"""
        # Simulate a call (HTTP GET).
        response = self.app.get("/documents/assets/logo-black-white.png")

        # Validate that the response is binary.
        self.assertIsInstance(response.body, bytes)

    def test_get_template_file_error(self):
        """Test bad files returns a 404."""
        # Simulate a call (HTTP GET).
        with self.assertRaises(Exception):
            self.app.get("/template/DUMMY.css")

    def test_get_assets_file_error(self):
        """Test bad files returns a 404."""
        # Simulate a call (HTTP GET).
        with self.assertRaises(Exception) as context:
            self.app.get("/documents/assets/DUMMY.png")
            self.assertEqual("404 Not Found", str(context.exception))


class TestAPIjson(unittest.TestCase):
    """Test the server API calls, including the Bottle decorators with json responses."""

    def setUp(self):
        """Test setup."""
        # Wrap the real app in a TestApp object.
        self.app = TestApp(app)

        # Create a standard argument list.
        # Set as wsgi so that the server doesn't try to launch.
        self.args = ["--wsgi"]

        # Initialize the server.
        main(self.args)

    def test_get_traceabilty(self):
        """Test GET /traceability.html"""
        # Simulate a call (HTTP GET).
        response = self.app.get("/traceability.html", {"format": "json"})

        # Validate the response.
        self.assertIsInstance(response.json, dict)
        self.assertIsInstance(response.json["traceability"], list)
        self.assertGreater(len(response.json["traceability"]), 30)

    def test_get_documents(self):
        """Test GET /documents/"""
        # Simulate a call (HTTP GET).
        response = self.app.get("/documents/", {"format": "json"})

        # Validate the response.
        self.assertIsInstance(response.json, dict)
        self.assertIsInstance(response.json["prefixes"], list)
        self.assertIn("REQ", response.json["prefixes"])
        self.assertIn("TUT", response.json["prefixes"])
        self.assertIn("HLT", response.json["prefixes"])
        self.assertIn("LLT", response.json["prefixes"])

    def test_get_documents_all(self):
        """Test GET /documents/all"""
        # Simulate a call (HTTP GET).
        response = self.app.get("/documents/all", {"format": "json"})

        # Validate the response.
        self.assertIsInstance(response.json, dict)
        self.assertIn("REQ", response.json)
        self.assertIn("TUT", response.json)
        self.assertIn("HLT", response.json)
        self.assertIn("LLT", response.json)

    def test_get_documents_req(self):
        """Test GET /documents/REQ"""
        # Simulate a call (HTTP GET).
        response = self.app.get("/documents/REQ", {"format": "json"})

        # Validate the response.
        self.assertIsInstance(response.json, dict)
        self.assertIsInstance(response.json["REQ008"], dict)
        self.assertEqual(3.2, response.json["REQ008"]["level"])

    def test_get_req_items(self):
        """Test GET /documents/REQ/items"""
        # Simulate a call (HTTP GET).
        response = self.app.get("/documents/REQ/items", {"format": "json"})

        # Validate the response.
        self.assertIsInstance(response.json, dict)
        self.assertIsInstance(response.json["uids"], list)
        self.assertIn("REQ001", response.json["uids"])

    def test_get_req_single_item(self):
        """Test GET /documents/REQ/items/req001"""
        # Simulate a call (HTTP GET).
        response = self.app.get("/documents/REQ/items/req001", {"format": "json"})

        # Validate the response.
        self.assertIsInstance(response.json, dict)
        self.assertIn(
            response.json["data"]["text"],
            "Doorstop **shall** support the storage of external requirements assets.\n",
        )

    def test_get_item_attributes(self):
        """Test GET /documents/REQ/items/req001/attrs"""
        # Simulate a call (HTTP GET).
        response = self.app.get("/documents/REQ/items/req001/attrs", {"format": "json"})

        # Validate the response.
        self.assertIsInstance(response.json, dict)
        self.assertIn("reviewed", response.text)

    def test_get_item_attribute_reviewed(self):
        """Test GET /documents/REQ/items/req001/attrs/reviewed"""
        # Simulate a call (HTTP GET).
        response = self.app.get(
            "/documents/REQ/items/req001/attrs/reviewed", {"format": "json"}
        )

        # Validate the response.
        self.assertIsInstance(response.json, dict)
        self.assertEqual(len(response.json["value"]), 44)

    def test_create_next_item(self):
        """Test POST /documents/TUT/numbers"""
        # Simulate a call (HTTP POST).
        response = self.app.post_json("/documents/TUT/numbers", {"format": "json"})

        # Validate the response. (Hard coded to 26 as currently TUT025 is the last one.)
        self.assertIsInstance(response.json, dict)
        self.assertEqual('{"next": 26}', response.text)

    def test_create_next_item_not_json(self):
        """Test POST /documents/LLT/numbers with a misspelled json request. Should return html."""
        # Simulate a call (HTTP POST).
        response = self.app.post_json(
            "/documents/LLT/numbers", {"format": "json_spelling_mistake"}
        )

        # Validate the response. (Hard coded to 11 as currently LLT010 is the last one.)
        self.assertEqual("11", response.text)
