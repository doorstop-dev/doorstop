# SPDX-License-Identifier: LGPL-3.0-only
# pylint: disable=C0302

"""Unit tests for the doorstop.core.item with extensions enabled."""

import os
import unittest
from types import ModuleType
from unittest.mock import patch

from doorstop.common import import_path_as_module
from doorstop.core.tests import TESTS_ROOT, MockItem, MockSimpleDocumentExtensions


class TestItem(unittest.TestCase):
    """Unit tests for the Item class."""

    # pylint: disable=protected-access,no-value-for-parameter

    def setUp(self):
        path = os.path.join("path", "to", "RQ001.yml")
        self.item = MockItem(MockSimpleDocumentExtensions(), path)

    @patch("doorstop.settings.CACHE_PATHS", False)
    def test_load_custom_validator_per_folder(self):
        """Load a valid custom validator per folder."""
        path = os.path.join("path", "to", "RQ001.yml")
        self.item = MockItem(
            MockSimpleDocumentExtensions(
                item_validator=f"{TESTS_ROOT}/validators/validator_dummy.py"
            ),
            path,
        )
        document = self.item.document
        validator = import_path_as_module(document.extensions["item_validator"])

        self.assertEqual(isinstance(validator, ModuleType), True)

    @patch("doorstop.settings.CACHE_PATHS", False)
    def test_load_custom_validator_per_folder_and_fails(self):
        """Load a invalid custom validator per folder and fails with FileNotFoundError."""
        path = os.path.join("path", "to", "RQ001.yml")
        self.item = MockItem(
            MockSimpleDocumentExtensions(
                item_validator=f"{TESTS_ROOT}/files/validator_dummy2.py"
            ),
            path,
        )
        document = self.item.document
        try:
            validator = import_path_as_module(document.extensions["item_validator"])
        except FileNotFoundError:
            validator = FileNotFoundError

        self.assertEqual(FileNotFoundError, validator)

    @patch("doorstop.settings.CACHE_PATHS", False)
    def test_find_references_and_get_sha(self):
        """Verify an item's references can be found."""
        path = os.path.join("path", "to", "RQ001.yml")
        self.item = MockItem(MockSimpleDocumentExtensions(item_sha_required=True), path)
        self.item.root = TESTS_ROOT

        self.item.references = [
            {"path": "files/REQ001.yml", "type": "file"},
            {"path": "files/REQ002.yml", "type": "file"},
        ]
        # Generate sha through review
        self.item.review()
        refs = self.item.references

        self.assertIn("sha", refs[0])
        self.assertIn("sha", refs[1])

    @patch("doorstop.settings.CACHE_PATHS", False)
    def test_no_sha_ref(self):
        """Verify sha is not obtained if extension is not enabled."""
        path = os.path.join("path", "to", "RQ001.yml")
        self.item = MockItem(
            MockSimpleDocumentExtensions(),
            path,
        )

        self.item.root = TESTS_ROOT

        self.item.references = [
            {"path": "files/REQ001.yml", "type": "file"},
            {"path": "files/REQ002.yml", "type": "file"},
        ]
        # without item_sha_required, sha must return None
        self.item.review()
        refs = self.item.references
        sha = self.item._hash_reference(refs[0]["path"])
        self.assertNotIn("sha", refs[0].keys())
        self.assertIsNone(sha)
