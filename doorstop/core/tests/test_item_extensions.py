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
