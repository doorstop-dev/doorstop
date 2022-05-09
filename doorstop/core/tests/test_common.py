# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.common module """

import unittest

from doorstop import common

MARKDOW_DEFAULT = """
---
active: true
derived: false
header: ''
level: 1.0
links: []
normative: true
ref: ''
reviewed: null
---

# Markdown Header

text text text

* one
* two

text text text
""".lstrip()

MARKDOW_INVALID = """
---
invalid 
  something
---

# Markdown Header

text text text
""".lstrip()

MARKDOW_MISSING_YAML = """
# Markdown Header

text text text
""".lstrip()


class TestMarkdownIO(unittest.TestCase):
    """Unit tests for the Markdown IO operations."""

    def test_load_markdown_without_header(self):
        # Arrange
        keys = ["text"]
        text = MARKDOW_DEFAULT
        path = "path/to/req.md"

        # Act
        data = common.load_markdown(text, path, keys)

        # Assert

        self.assertIn("header", data)
        self.assertEqual(data["header"], "")
        self.assertEqual(
            data["text"],
            """# Markdown Header

text text text

* one
* two

text text text""",
        )

    def test_load_markdown_with_header(self):
        # Arrange
        keys = ["text", "header"]
        text = MARKDOW_DEFAULT
        path = "path/to/req.md"

        # Act
        data = common.load_markdown(text, path, keys)

        # Assert

        self.assertIn("header", data)
        self.assertEqual(data["header"], "Markdown Header")
        self.assertEqual(
            data["text"],
            """text text text

* one
* two

text text text""",
        )

    def test_load_markdown_invalid_yaml(self):
        # Arrange
        keys = []
        text = MARKDOW_INVALID
        path = "path/to/req.md"

        # Act
        data = common.load_markdown(text, path, keys)

        # Assert
        self.assertEqual(data, {})

    def test_load_markdown_missing_yaml(self):
        # Arrange
        keys = []
        text = MARKDOW_MISSING_YAML
        path = "path/to/req.md"

        # Act
        data = common.load_markdown(text, path, keys)

        # Assert
        self.assertEqual(data, {})

    def test_dump_markdown(self):
        # Arrange
        data = {
            "key1": "text1",
            "key2": "text2",
            "list": ["a", "b", "c"],
        }
        textattr = {
            "text": """
text text text 
""".lstrip(),
            "header": "header",
        }
        # Act
        text = common.dump_markdown(data, textattr)

        # Assert
        self.assertEqual(
            text,
            """
---
key1: text1
key2: text2
list:
- a
- b
- c
---

# header

text text text""".lstrip(),
        )
