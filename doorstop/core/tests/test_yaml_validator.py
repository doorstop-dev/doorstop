# SPDX-License-Identifier: LGPL-3.0-only
# pylint: disable=C0302

"""Unit tests for the doorstop.core.item module."""

import unittest
from typing import Any, Dict

from doorstop.core.yaml_validator import YamlValidator


class TestItem(unittest.TestCase):
    """Unit tests for the Item class."""

    # pylint: disable=protected-access,no-value-for-parameter

    def setUp(self):
        self.validator = YamlValidator()

    def test_empty_item(self):
        item_dict: Dict[str, Any] = {}

        valid = self.validator.validate_item_yaml(item_dict)

        self.assertTrue(valid)

    def test_references_are_none(self):
        item_dict: Dict[str, Any] = {"references": None}

        with self.assertRaises(AttributeError) as context:
            self.validator.validate_item_yaml(item_dict)

        self.assertTrue(
            "'references' must be an array with at least one reference element"
            in str(context.exception)
        )

    def test_references_missing_type(self):
        item_dict: Dict[str, Any] = {"references": [{}]}

        with self.assertRaises(AttributeError) as context:
            self.validator.validate_item_yaml(item_dict)

        self.assertEqual(
            "'references' member must have a 'type' key", str(context.exception)
        )

    def test_reference_with_a_nonfile_type(self):
        item_dict = {
            "references": [
                {
                    "type": "incorrect-type",
                    "path": "some/path",
                    "keyword": "some keyword",
                }
            ]
        }

        with self.assertRaises(AttributeError) as context:
            self.validator.validate_item_yaml(item_dict)

        self.assertEqual(
            "'references' member's 'type' value must be a 'file'",
            str(context.exception),
        )

    def test_reference_with_a_string_keyword(self):
        item_dict = {
            "references": [
                {"type": "file", "path": "some/path", "keyword": "some keyword"}
            ]
        }

        valid = self.validator.validate_item_yaml(item_dict)

        self.assertTrue(valid)

    def test_reference_with_a_non_string_keyword(self):
        item_dict = {
            "references": [
                {
                    "type": "file",
                    "path": "some/path",
                    "keyword": ["keyword must be a string"],
                }
            ]
        }

        with self.assertRaises(AttributeError) as context:
            self.validator.validate_item_yaml(item_dict)

        self.assertTrue(
            "'references' member's 'keyword' must be a string value"
            in str(context.exception)
        )
