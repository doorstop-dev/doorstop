# SPDX-License-Identifier: LGPL-3.0-only
# pylint: disable=C0302

"""Unit tests for the doorstop.core.document module."""

# pylint: disable=unused-argument,protected-access

import logging
import os
import unittest
from unittest import mock
from unittest.mock import MagicMock, Mock, call, patch

from doorstop import common
from doorstop.common import DoorstopError, DoorstopInfo, DoorstopWarning
from doorstop.core.document import Document
from doorstop.core.tests import EMPTY, FILES, NEW, ROOT, MockDocument, MockItem
from doorstop.core.types import UID, Level

YAML_DEFAULT = """
settings:
  digits: 3
  itemformat: yaml
  prefix: REQ
  sep: ''
""".lstrip()

YAML_MARKDOWN = """
settings:
  digits: 4
  itemformat: markdown
  prefix: CUSTOM_MD
  sep: '-'
""".lstrip()


YAML_CUSTOM = """
settings:
  digits: 4
  prefix: CUSTOM
  sep: '-'
""".lstrip()

YAML_CUSTOM_PARENT = """
settings:
  digits: 4
  parent: PARENT
  prefix: CUSTOM
  sep: '-'
""".lstrip()

YAML_INVALID = """
settings:
  digits: oops
""".lstrip()

YAML_UNKNOWN = """
settings:
  John: 'Doe'
""".lstrip()

YAML_UNKNOWN_ATTRIBUTES = """
settings:
  digits: 3
  prefix: REQ
  sep: ''
attributes:
  unknown: empty
""".lstrip()

YAML_EXTENDED_REVIEWED = """
settings:
  digits: 3
  prefix: REQ
  sep: ''
attributes:
  reviewed:
  - type
  - verification-method
""".lstrip()

YAML_CUSTOM_DEFAULTS = """
settings:
  digits: 3
  prefix: REQ
  sep: ''
attributes:
  defaults:
    a:
    - b
    - c
    d:
      e: f
      g: h
    i: j
    k: null
""".lstrip()

YAML_INCLUDE_DEFAULTS = """
settings:
  digits: 3
  prefix: REQ
  sep: ''
attributes: !include a/template.yml
""".lstrip()

YAML_INCLUDE_NO_SUCH_FILE = """
settings:
  digits: 3
  prefix: REQ
  sep: ''
attributes: !include no/such/file.yml
""".lstrip()


@patch("doorstop.settings.REORDER", False)
@patch("doorstop.core.item.Item", MockItem)
class TestDocument(unittest.TestCase):
    """Unit tests for the Document class."""

    # pylint: disable=no-value-for-parameter

    def setUp(self):
        self.document = MockDocument(FILES, root=ROOT)

    def test_init_invalid(self):
        """Verify a document cannot be initialized from an invalid path."""
        self.assertRaises(DoorstopError, Document, "not/a/path")

    def test_object_references(self):
        """Verify a standalone document does not have object references."""
        self.assertIs(None, self.document.tree)

    def test_load_empty(self):
        """Verify loading calls read."""
        self.document.load()
        self.document._read.assert_called_once_with(self.document.config)

    def test_load_error(self):
        """Verify an exception is raised with invalid YAML."""
        self.document._file = "invalid: -"
        self.assertRaises(DoorstopError, self.document.load)

    def test_load_unexpected(self):
        """Verify an exception is raised for unexpected file contents."""
        self.document._file = "unexpected"
        self.assertRaises(DoorstopError, self.document.load)

    def test_load(self):
        """Verify the document config can be loaded from file."""
        self.document._file = YAML_CUSTOM
        self.document.load(reload=True)
        self.assertEqual("yaml", self.document.itemformat)
        self.assertEqual("CUSTOM", self.document.prefix)
        self.assertEqual("-", self.document.sep)
        self.assertEqual(4, self.document.digits)

    def test_load_markdown(self):
        """Verify the document config can be loaded from file."""
        self.document._file = YAML_MARKDOWN
        self.document.load(reload=True)
        self.assertEqual("markdown", self.document.itemformat)
        self.assertEqual("CUSTOM_MD", self.document.prefix)
        self.assertEqual("-", self.document.sep)
        self.assertEqual(4, self.document.digits)

    def test_load_parent(self):
        """Verify the document config can be loaded from file with a parent."""
        self.document._file = YAML_CUSTOM_PARENT
        self.document.load()
        self.assertEqual("PARENT", self.document.parent)

    def test_load_invalid(self):
        """Verify that an invalid document config raises an exception."""
        self.document._file = YAML_INVALID
        msg = "^invalid value for 'digits' in: .*\\.doorstop.yml$"
        self.assertRaisesRegex(DoorstopError, msg, self.document.load)

    def test_load_unknown(self):
        """Verify loading a document config with an unknown key fails."""
        self.document._file = YAML_UNKNOWN
        msg = "^unexpected document setting 'John' in: .*\\.doorstop.yml$"
        self.assertRaisesRegex(DoorstopError, msg, self.document.load)

    def test_load_unknown_attributes(self):
        """Verify loading a document config with unknown attributes fails."""
        self.document._file = YAML_UNKNOWN_ATTRIBUTES
        msg = "^unexpected attributes configuration 'unknown' in: .*\\.doorstop.yml$"
        self.assertRaisesRegex(DoorstopError, msg, self.document.load)

    def test_load_with_non_existing_include(self):
        """Verify include of non-existing file fails."""
        self.document._file = YAML_INCLUDE_NO_SUCH_FILE
        msg = "^include in '.*\\.doorstop.yml' failed: .*$"
        self.assertRaisesRegex(DoorstopError, msg, self.document.load)

    def test_load_extended_reviewed(self):
        """Verify loaded extended reviewed attribute keys of a document."""
        self.document._file = YAML_EXTENDED_REVIEWED
        self.document.load()
        self.assertEqual(
            self.document.extended_reviewed, ["type", "verification-method"]
        )

    def test_load_custom_defaults(self):
        """Verify loaded custom defaults for attributes of a document."""
        self.document._file = YAML_CUSTOM_DEFAULTS
        self.document.load()
        self.assertEqual(
            self.document._attribute_defaults,
            {"a": ["b", "c"], "d": {"e": "f", "g": "h"}, "i": "j", "k": None},
        )

    def test_load_defaults_via_include(self):
        """Verify loaded defaults for attributes via includes."""
        self.document._file = YAML_INCLUDE_DEFAULTS
        self.document.load()
        self.assertEqual(self.document._attribute_defaults, {"text": "Some text"})

    def test_save_empty(self):
        """Verify saving calls write."""
        self.document.tree = Mock()
        self.document.save()
        self.document._write.assert_called_once_with(YAML_DEFAULT, self.document.config)
        self.document.tree.vcs.edit.assert_called_once_with(self.document.config)

    def test_save_parent(self):
        """Verify a document can be saved with a parent."""
        self.document.parent = "SYS"
        self.document.save()
        self.assertIn("parent: SYS", self.document._file)

    def test_save_custom(self):
        """Verify a document can be saved with a custom attribute."""
        self.document._data["custom"] = "this"
        self.document.save()
        self.assertIn("custom: this", self.document._file)

    def test_save_extended_reviewed(self):
        """Verify saving of extended reviewed attribute keys."""
        self.document._extended_reviewed = ["type", "verification-method"]
        self.document.save()
        self.assertIn("attributes:", self.document._file)
        self.assertIn("  reviewed:", self.document._file)
        self.assertIn("  - type", self.document._file)
        self.assertIn("  - verification-method", self.document._file)

    def test_no_save_empty_extended_reviewed(self):
        """Verify not saving of empty extended reviewed attribute keys."""
        self.document._extended_reviewed = []
        self.document.save()
        self.assertNotIn("attributes:", self.document._file)
        self.assertNotIn("  reviewed:", self.document._file)

    def test_save_custom_defaults(self):
        """Verify saving of custom default attributes."""
        self.document._attribute_defaults = {"key": "value"}
        self.document.save()
        self.assertIn("attributes:", self.document._file)
        self.assertIn("  defaults:", self.document._file)
        self.assertIn("    key: value", self.document._file)

    def test_no_save_missing_custom_defaults(self):
        """Verify not saving of missing custom default attributes."""
        self.document.save()
        self.assertNotIn("attributes:", self.document._file)
        self.assertNotIn("  defaults:", self.document._file)

    @patch("doorstop.common.verbosity", 2)
    def test_str(self):
        """Verify a document can be converted to a string."""
        self.assertEqual("REQ", str(self.document))

    @patch("doorstop.common.verbosity", 3)
    def test_str_verbose(self):
        """Verify a document can be converted to a string (verbose)."""
        relpath = os.path.relpath(self.document.path, self.document.root)
        text = "REQ (@{}{})".format(os.sep, relpath)
        self.assertEqual(text, str(self.document))

    def test_ne(self):
        """Verify document non-equality is correct."""
        self.assertNotEqual(self.document, None)

    def test_hash(self):
        """Verify documents can be hashed."""
        document1 = MockDocument("path/to/fake1")
        document2 = MockDocument("path/to/fake2")
        document3 = MockDocument("path/to/fake2")
        my_set = set()
        # Act
        my_set.add(document1)
        my_set.add(document2)
        my_set.add(document3)
        # Assert
        self.assertEqual(2, len(my_set))

    def test_len(self):
        """Verify a document has a length."""
        self.assertEqual(6, len(self.document))

    def test_items(self):
        """Verify the items in a document can be accessed."""
        items = self.document.items
        self.assertEqual(6, len(items))
        for item in self.document:
            logging.debug("item: {}".format(item))
            self.assertIs(self.document, item.document)
            self.assertIs(self.document.tree, item.tree)

    def test_items_cache(self):
        """Verify the items in a document get cached."""
        self.document.tree = Mock()
        self.document.tree._item_cache = {}
        print(self.document.items)
        self.assertEqual(7, len(self.document.tree._item_cache))

    @patch("doorstop.core.document.Document", MockDocument)
    def test_new(self):
        """Verify a new document can be created with defaults."""
        MockDocument._create.reset_mock()
        path = os.path.join(EMPTY, ".doorstop.yml")
        document = MockDocument.new(None, EMPTY, root=FILES, prefix="NEW", digits=2)
        self.assertEqual("NEW", document.prefix)
        self.assertEqual(2, document.digits)
        self.assertEqual(None, document._attribute_defaults)
        self.assertEqual([], document.extended_reviewed)
        MockDocument._create.assert_called_once_with(path, name="document")

    def test_new_existing(self):
        """Verify an exception is raised if the document already exists."""
        self.assertRaises(DoorstopError, Document.new, None, FILES, ROOT, prefix="DUPL")

    def test_new_invalid_sep(self):
        """Verify an exception is raised if the separator is invalid."""
        msg = "invalid UID separator 'X'"
        self.assertRaisesRegex(
            DoorstopError, msg, Document.new, None, FILES, ROOT, prefix="NEW", sep="X"
        )

    @patch("doorstop.core.document.Document", MockDocument)
    def test_new_cache(self):
        """Verify a new documents are cached."""
        mock_tree = Mock()
        mock_tree._document_cache = {}
        document = MockDocument.new(
            mock_tree, EMPTY, root=FILES, prefix="NEW", digits=2
        )
        mock_tree.vcs.add.assert_called_once_with(document.config)
        self.assertEqual(document, mock_tree._document_cache[document.prefix])

    def test_invalid(self):
        """Verify an exception is raised on an invalid document."""
        self.assertRaises(DoorstopError, Document, EMPTY)

    def test_relpath(self):
        """Verify the document's relative path string can be determined."""
        relpath = os.path.relpath(self.document.path, self.document.root)
        text = "@{}{}".format(os.sep, relpath)
        self.assertEqual(text, self.document.relpath)

    def test_sep(self):
        """Verify an documents's separator can be set and read."""
        self.document.sep = "_"
        self.assertIn("sep: _\n", self.document._write.call_args[0][0])
        self.assertEqual("_", self.document.sep)

    def test_sep_invalid(self):
        """Verify an invalid separator is rejected."""
        self.assertRaises(AssertionError, setattr, self.document, "sep", "?")

    def test_digits(self):
        """Verify an documents's digits can be set and read."""
        self.document.digits = 42
        self.assertIn("digits: 42\n", self.document._write.call_args[0][0])
        self.assertEqual(42, self.document.digits)

    def test_depth(self):
        """Verify the maximum item level depth can be determined."""
        self.assertEqual(3, self.document.depth)

    def test_next_number(self):
        """Verify the next item number can be determined."""
        self.assertEqual(7, self.document.next_number)

    def test_next_number_server(self):
        """Verify the next item number can be determined with a server."""
        self.document.tree = MagicMock()
        self.document.tree.request_next_number = Mock(side_effect=[1, 42])
        self.assertEqual(42, self.document.next_number)

    def test_index_get(self):
        """Verify a document's index can be retrieved."""
        self.assertIs(None, self.document.index)
        with patch("os.path.isfile", Mock(return_value=True)):
            path = os.path.join(self.document.path, self.document.INDEX)
            self.assertEqual(path, self.document.index)

    @patch("doorstop.common.write_lines")
    @patch("doorstop.settings.MAX_LINE_LENGTH", 40)
    def test_index_set(self, mock_write_lines):
        """Verify an document's index can be created."""
        lines = [
            "initial: 1.2.3",
            "outline:",
            "            - REQ001: # Lorem ipsum d...",
            "        - REQ003: # Unicode: -40° ±1%",
            "        - REQ006: # Hello, world!",
            "        - REQ004: # Hello, world!",
            "        - REQ002: # Hello, world!",
            "        - REQ2-001: # Hello, world!",
        ]
        # Act
        self.document.index = True  # create index
        # Assert
        gen, path = mock_write_lines.call_args[0]
        lines2 = list(gen)[8:]  # skip lines of info comments
        self.assertListEqual(lines, lines2)
        self.assertEqual(os.path.join(FILES, "index.yml"), path)

    @patch("doorstop.common.write_lines")
    @patch("doorstop.settings.MAX_LINE_LENGTH", 40)
    def test_read_index(self, mock_write_lines):
        """Verify a document index can be read."""
        lines = """initial: 1.2.3
outline:
        - REQ001: # Lorem ipsum d...
        - REQ003: # Unicode: -40° ±1%
        - REQ004: # Hello, world! !['..
        - REQ002: # Hello, world! !["...
        - REQ2-001: # Hello, world!"""

        expected = {
            "initial": "1.2.3",
            "outline": [
                {"REQ001": [{"text": "Lorem ipsum d..."}]},
                {"REQ003": [{"text": "Unicode: -40° ±1%"}]},
                {"REQ004": [{"text": "Hello, world! !['.."}]},
                {"REQ002": [{"text": 'Hello, world! !["...'}]},
                {"REQ2-001": [{"text": "Hello, world!"}]},
            ],
        }
        # Act
        with patch("builtins.open") as mock_open:
            mock_open.side_effect = lambda *args, **kw: mock.mock_open(
                read_data=lines
            ).return_value
            actual = self.document._read_index("mock_path")
            # Check string can be parsed as yaml
        # Assert
        self.assertEqual(expected, actual)

    @patch("doorstop.common.delete")
    def test_index_del(self, mock_delete):
        """Verify a document's index can be deleted."""
        del self.document.index
        mock_delete.assert_called_once_with(None)

    @patch("doorstop.core.document.Document._reorder_automatic")
    @patch("doorstop.core.item.Item.new")
    def test_add_item(self, mock_new, mock_reorder):
        """Verify an item can be added to a document."""
        with patch("doorstop.settings.REORDER", True):
            self.document.add_item()
        mock_new.assert_called_once_with(
            None, self.document, FILES, ROOT, "REQ007", level=Level("2.2")
        )
        self.assertEqual(0, mock_reorder.call_count)

    @patch("doorstop.core.document.Document.reorder")
    @patch("doorstop.core.item.Item.new")
    def test_add_item_with_level(self, mock_new, mock_reorder):
        """Verify an item can be added to a document with a level."""
        with patch("doorstop.settings.REORDER", True):
            item = self.document.add_item(level="4.2")
        mock_new.assert_called_once_with(
            None, self.document, FILES, ROOT, "REQ007", level="4.2"
        )
        mock_reorder.assert_called_once_with(keep=item)

    @patch("doorstop.core.item.Item.new")
    def test_add_item_with_number(self, mock_new):
        """Verify an item can be added to a document with a number."""
        self.document.add_item(number=999)
        mock_new.assert_called_once_with(
            None, self.document, FILES, ROOT, "REQ999", level=Level("2.2")
        )

    def test_add_item_with_no_sep(self):
        """Verify an item cannot be added to a document without a separator with a name."""
        msg = "cannot add item with name 'ABC' to document 'REQ' without a separator"
        self.assertRaisesRegex(DoorstopError, msg, self.document.add_item, name="ABC")

    def test_add_item_with_invalid_sep(self):
        """Verify an item cannot be added to a document with an invalid separator with a name."""
        self.document._data["sep"] = "X"
        msg = "cannot add item with name 'ABC' to document 'REQ' with an invalid separator 'X'"
        self.assertRaisesRegex(DoorstopError, msg, self.document.add_item, name="ABC")

    def test_add_item_with_invalid_name(self):
        """Verify an item cannot be added to a document with an invalid name."""
        self.document.sep = "-"
        msg = "invalid item name 'A-B'"
        self.assertRaisesRegex(DoorstopError, msg, self.document.add_item, name="A-B")
        msg = "invalid item name 'A_B'"
        self.assertRaisesRegex(DoorstopError, msg, self.document.add_item, name="A_B")
        msg = "invalid item name 'A.B'"
        self.assertRaisesRegex(DoorstopError, msg, self.document.add_item, name="A.B")
        msg = "invalid item name 'X/Y'"
        self.assertRaisesRegex(DoorstopError, msg, self.document.add_item, name="X/Y")

    @patch("doorstop.core.item.Item.new")
    def test_add_item_with_name(self, mock_new):
        """Verify an item can be added to a document with a name."""
        self.document.sep = "-"
        self.document.add_item(name="ABC")
        mock_new.assert_called_once_with(
            None, self.document, FILES, ROOT, "REQ-ABC", level=Level("2.2")
        )

    @patch("doorstop.core.item.Item.new")
    def test_add_item_with_number_name(self, mock_new):
        """Verify an item can be added to a document with a number as name."""
        self.document.sep = "-"
        self.document.add_item(name="99")
        mock_new.assert_called_once_with(
            None, self.document, FILES, ROOT, "REQ-099", level=Level("2.2")
        )

    @patch("doorstop.core.item.Item.set_attributes")
    def test_add_item_with_defaults(self, mock_set_attributes):
        """Verify an item can be added to a document with defaults."""
        self.document._file = "text: 'abc'"
        self.document.add_item(defaults="mock.yml")
        mock_set_attributes.assert_called_once_with({"text": "abc"})

    @patch("doorstop.core.item.Item.new")
    def test_add_item_empty(self, mock_new):
        """Verify an item can be added to an new document."""
        document = MockDocument(NEW, ROOT)
        document.prefix = "NEW"  # type: ignore
        self.assertIsNot(None, document.add_item(reorder=False))
        mock_new.assert_called_once_with(
            None, document, NEW, ROOT, "NEW001", level=None
        )

    @patch("doorstop.core.item.Item.new")
    def test_add_item_after_header(self, mock_new):
        """Verify the next item after a header is indented."""
        mock_item = Mock()
        mock_item.uid = UID("REQ001")
        mock_item.level = Level("1.0")
        self.document._iter = Mock(return_value=[mock_item])
        self.document.add_item()
        mock_new.assert_called_once_with(
            None, self.document, FILES, ROOT, "REQ002", level=Level("1.1")
        )

    def test_add_item_contains(self):
        """Verify an added item is contained in the document."""
        item = self.document.items[0]
        self.assertIn(item, self.document)
        item2 = self.document.add_item(reorder=False)
        self.assertIn(item2, self.document)

    def test_add_item_cache(self):
        """Verify an added item is cached."""
        self.document.tree = Mock()
        self.document.tree._item_cache = {}
        self.document.tree.request_next_number = None
        item = self.document.add_item(reorder=False)
        self.assertEqual(item, self.document.tree._item_cache[item.uid])

    @patch("doorstop.core.document.Document._reorder_automatic")
    @patch("os.remove")
    def test_remove_item(self, mock_remove, mock_reorder):
        """Verify an item can be removed."""
        with patch("doorstop.settings.REORDER", True):
            item = self.document.remove_item("REQ001")
        mock_reorder.assert_called_once_with(self.document.items, keep=None, start=None)
        mock_remove.assert_called_once_with(item.path)

    @patch("os.remove")
    def test_remove_item_contains(self, mock_remove):
        """Verify a removed item is not contained in the document."""
        item = self.document.items[0]
        self.assertIn(item, self.document)
        removed_item = self.document.remove_item(item.uid, reorder=False)
        self.assertEqual(item, removed_item)
        self.assertNotIn(item, self.document)
        mock_remove.assert_called_once_with(item.path)

    @patch("os.remove")
    def test_remove_item_by_item(self, mock_remove):
        """Verify an item can be removed (by item)."""
        item = self.document.items[0]
        self.assertIn(item, self.document)
        removed_item = self.document.remove_item(item, reorder=False)
        self.assertEqual(item, removed_item)
        mock_remove.assert_called_once_with(item.path)

    @patch("os.remove", Mock())
    def test_remove_item_cache(self):
        """Verify a removed item is expunged."""
        self.document.tree = Mock()
        self.document.tree._item_cache = {}
        item = self.document.items[0]
        removed_item = self.document.remove_item(item.uid, reorder=False)
        self.assertIs(None, self.document.tree._item_cache[removed_item.uid])

    @patch("doorstop.core.document.Document._reorder_automatic")
    @patch("doorstop.core.document.Document._reorder_from_index")
    def test_reorder(self, mock_index, mock_auto):
        """Verify items can be reordered."""
        path = os.path.join(self.document.path, "index.yml")
        common.touch(path)
        # Act
        self.document.reorder()
        # Assert
        mock_index.assert_called_once_with(self.document, path)
        mock_auto.assert_called_once_with(self.document.items, start=None, keep=None)

    def test_reorder_automatic(self):
        """Verify items can be reordered automatically."""
        mock_items = [
            Mock(level=Level("2.3")),
            Mock(level=Level("2.3")),
            Mock(level=Level("2.7")),
            Mock(level=Level("3.2.2")),
            Mock(level=Level("3.4.2")),
            Mock(level=Level("3.5.0")),
            Mock(level=Level("3.5.0")),
            Mock(level=Level("3.6")),
            Mock(level=Level("5.0")),
            Mock(level=Level("5.9")),
        ]
        expected = [
            Level("2.3"),
            Level("2.4"),
            Level("2.5"),
            Level("3.1.1"),
            Level("3.2.1"),
            Level("3.3.0"),
            Level("3.4.0"),
            Level("3.5"),
            Level("4.0"),
            Level("4.1"),
        ]
        Document._reorder_automatic(mock_items)
        actual = [item.level for item in mock_items]
        self.assertListEqual(expected, actual)

    def test_reorder_automatic_no_change(self):
        """Verify already ordered items can be reordered."""
        mock_items = [
            Mock(level=Level("1.1")),
            Mock(level=Level("1.1.1.1")),
            Mock(level=Level("2")),
            Mock(level=Level("3")),
            Mock(level=Level("4.1.1")),
        ]
        expected = [
            Level("1.1"),
            Level("1.1.1.1"),
            Level("2"),
            Level("3"),
            Level("4.1.1"),
        ]
        Document._reorder_automatic(mock_items)
        actual = [item.level for item in mock_items]
        self.assertListEqual(expected, actual)

    def test_reorder_automatic_with_start(self):
        """Verify items can be reordered with a given start."""
        mock_item = Mock(level=Level("2.3"))
        mock_items = [
            Mock(level=Level("2.2")),
            mock_item,
            Mock(level=Level("2.3")),
            Mock(level=Level("2.7")),
            Mock(level=Level("3.2.2")),
            Mock(level=Level("3.4.2")),
            Mock(level=Level("3.5.0")),
            Mock(level=Level("3.5.0")),
            Mock(level=Level("3.6")),
            Mock(level=Level("5.0")),
            Mock(level=Level("5.9")),
        ]
        expected = [
            Level("1.2"),
            Level("1.3"),
            Level("1.4"),
            Level("1.5"),
            Level("2.1.1"),
            Level("2.2.1"),
            Level("2.3.0"),
            Level("2.4.0"),
            Level("2.5"),
            Level("3.0"),
            Level("3.1"),
        ]
        Document._reorder_automatic(mock_items, start=(1, 2), keep=mock_item)
        actual = [item.level for item in mock_items]
        self.assertListEqual(expected, actual)

    def test_find_item(self):
        """Verify an item can be found by UID."""
        item = self.document.find_item("req2")
        self.assertIsNot(None, item)

    def test_find_item_exact(self):
        """Verify an item can be found by its exact UID."""
        item = self.document.find_item("req2-001")
        self.assertIsNot(None, item)

    def test_find_item_unknown_number(self):
        """Verify an exception is raised on an unknown number."""
        self.assertRaises(DoorstopError, self.document.find_item, "req99")

    def test_find_item_unknown_uid(self):
        """Verify an exception is raised on an unknown UID."""
        self.assertRaises(DoorstopError, self.document.find_item, "unknown99")

    @patch("doorstop.core.validators.item_validator.ItemValidator.get_issues")
    @patch("doorstop.core.document.Document.reorder")
    def test_validate(self, mock_reorder, mock_get_issues):
        """Verify a document can be validated."""
        mock_get_issues.return_value = [DoorstopInfo("i")]
        with patch("doorstop.settings.REORDER", True):
            self.assertTrue(self.document.validate())
        mock_reorder.assert_called_once_with(_items=self.document.items)
        self.assertEqual(6, mock_get_issues.call_count)

    @patch(
        "doorstop.core.validators.item_validator.ItemValidator.get_issues",
        Mock(
            return_value=[
                DoorstopError("error"),
                DoorstopWarning("warning"),
                DoorstopInfo("info"),
            ]
        ),
    )
    def test_validate_item(self):
        """Verify an item error fails the document check."""
        self.assertFalse(self.document.validate())

    @patch(
        "doorstop.core.validators.item_validator.ItemValidator.get_issues",
        Mock(return_value=[]),
    )
    def test_validate_hook(self):
        """Verify an item hook can be called."""
        mock_hook = MagicMock()
        self.document.validate(item_hook=mock_hook)
        self.assertEqual(6, mock_hook.call_count)

    @patch("doorstop.core.item.Item.delete")
    @patch("os.rmdir")
    def test_delete(self, mock_delete, mock_item_delete):
        """Verify a document can be deleted."""
        self.document.delete()
        self.assertEqual(7, mock_item_delete.call_count)
        self.assertEqual(1, mock_delete.call_count)
        self.document.delete()  # ensure a second delete is ignored

    @patch("doorstop.core.item.Item.delete")
    @patch("os.rmdir")
    def test_delete_with_assets(self, mock_delete, mock_item_delete):
        """Verify a document's assets aren't deleted."""
        mock_delete.side_effect = OSError
        self.document.delete()
        self.assertEqual(7, mock_item_delete.call_count)
        self.assertEqual(1, mock_delete.call_count)
        self.document.delete()  # ensure a second delete is ignored

    @patch("doorstop.core.item.Item.delete", Mock())
    @patch("doorstop.common.delete", Mock())
    def test_delete_cache(self):
        """Verify a deleted document is expunged."""
        self.document.tree = Mock()
        self.document.tree._item_cache = {}
        self.document.tree._document_cache = {}
        self.document.delete()
        self.document.tree.vcs.delete.assert_called_once_with(self.document.config)
        self.assertIs(None, self.document.tree._document_cache[self.document.prefix])

    @patch("doorstop.core.document.Document.get_issues", Mock(return_value=[]))
    def test_issues(self):
        """Verify an document's issues convenience property can be accessed."""
        self.assertEqual(0, len(self.document.issues))

    def test_issues_duplicate_level(self):
        """Verify duplicate item levels are detected."""
        mock_item1 = Mock()
        mock_item1.uid = "HLT001"
        mock_item1.level = Level("4.2")
        mock_item2 = Mock()
        mock_item2.uid = "HLT002"
        mock_item2.level = Level("4.2")
        mock_items = [mock_item1, mock_item2]
        expected = DoorstopWarning("duplicate level: 4.2 (HLT001, HLT002)")
        issue = list(self.document._get_issues_level(mock_items))[0]
        self.assertIsInstance(issue, type(expected))
        self.assertEqual(expected.args, issue.args)

    def test_issues_skipped_level_over(self):
        """Verify skipped (over) item levels are detected."""
        mock_item1 = Mock()
        mock_item1.uid = "HLT001"
        mock_item1.level = Level("1.1")
        mock_item2 = Mock()
        mock_item2.uid = "HLT002"
        mock_item2.level = Level("1.3")
        mock_items = [mock_item1, mock_item2]
        expected = DoorstopWarning("skipped level: 1.1 (HLT001), 1.3 (HLT002)")
        issues = list(self.document._get_issues_level(mock_items))
        self.assertEqual(1, len(issues))
        self.assertIsInstance(issues[0], type(expected))
        self.assertEqual(expected.args, issues[0].args)

    def test_issues_skipped_level_out(self):
        """Verify skipped (out) item levels are detected."""
        mock_item1 = Mock()
        mock_item1.uid = "HLT001"
        mock_item1.level = Level("1.1")
        mock_item2 = Mock()
        mock_item2.uid = "HLT002"
        mock_item2.level = Level("3.0")
        mock_items = [mock_item1, mock_item2]
        expected = DoorstopWarning("skipped level: 1.1 (HLT001), 3.0 (HLT002)")
        issues = list(self.document._get_issues_level(mock_items))
        self.assertEqual(1, len(issues))
        self.assertIsInstance(issues[0], type(expected))
        self.assertEqual(expected.args, issues[0].args)

    def test_issues_skipped_level_out_over(self):
        """Verify skipped (out and over) item levels are detected."""
        mock_item1 = Mock()
        mock_item1.uid = "HLT001"
        mock_item1.level = Level("1.1")
        mock_item2 = Mock()
        mock_item2.uid = "HLT002"
        mock_item2.level = Level("2.2")
        mock_items = [mock_item1, mock_item2]
        expected = DoorstopWarning("skipped level: 1.1 (HLT001), 2.2 (HLT002)")
        issues = list(self.document._get_issues_level(mock_items))
        self.assertEqual(1, len(issues))
        self.assertIsInstance(issues[0], type(expected))
        self.assertEqual(expected.args, issues[0].args)

    @patch("os.path.isdir", Mock(return_value=True))
    def test_assets_exist(self):
        """Verify a document can report the existence of the assets folder."""
        path = os.path.join(self.document.path, self.document.ASSETS)
        self.assertEqual(path, self.document.assets)

    @patch("os.path.isdir", Mock(return_value=False))
    def test_assets_missing(self):
        """Verify a document can report the existence of the assets folder."""
        self.assertEqual(None, self.document.assets)

    @patch("os.path.isdir", Mock(return_value=True))
    @patch("glob.glob")
    @patch("shutil.copytree")
    def test_copy_assets(self, mock_copytree, mock_glob):
        """Verify a document can copy its assets"""
        assets = ["css", "logo.png"]
        assets_full_path = [
            os.path.join(self.document.path, self.document.ASSETS, dir)
            for dir in assets
        ]
        mock_glob.return_value = assets_full_path
        dst = os.path.join("publishdir", "assets")
        expected_calls = [
            call(assets_full_path[0], os.path.join(dst, assets[0])),
            call(assets_full_path[1], os.path.join(dst, assets[1])),
        ]
        # Act]
        self.document.copy_assets(dst)
        # Assert
        self.assertEqual(expected_calls, mock_copytree.call_args_list)

    @patch("os.path.exists", Mock(return_value=True))
    @patch("os.path.isdir", Mock(return_value=True))
    @patch("glob.glob")
    @patch("shutil.copytree")
    def test_copy_assets_skipping(self, mock_copytree, mock_glob):
        """Verify duplicate file or directory names are skipped"""
        assets = ["doorstop"]
        mock_glob.return_value = assets
        mock_copytree.side_effect = FileExistsError
        dst = os.path.join("publishdir", "assets")
        # Act]
        self.document.copy_assets(dst)
        # Assert
        self.assertEqual([], mock_copytree.call_args_list)


@patch("doorstop.core.item.Item", MockItem)
class TestDocumentReorder(unittest.TestCase):
    """Unit tests for the Document class."""

    def setUp(self):
        def mock_find_item(uid):
            """Return a mock item and store it."""
            if uid == "bb":
                mock_item = self.document.add_item(level=Level("3.2"), uid=uid)
            elif uid == "new":
                raise DoorstopError("unknown UID: bab")
            else:
                mock_item = self.document.add_item(uid=uid)
            return mock_item

        def mock_add_item(level=None, reorder=False, uid=None):
            """Return a mock item and store it."""
            mock_item = MagicMock()
            mock_item.level = level
            mock_item.text = ""
            if uid:
                mock_item.uid = uid
            else:
                mock_item.uid = self.next_uid
                self.next_uid += 1
            self.document.items.append(mock_item)
            return mock_item

        self.next_uid = 1
        self.document = MagicMock()
        self.document.items = []
        self.document.find_item = mock_find_item
        self.document.add_item = mock_add_item

    def test_add_item(self):
        self.assertEqual(self.document.items, [])
        item = self.document.add_item(Level("1"), False)
        self.assertEqual(item.level, Level("1"))
        self.assertEqual(self.document.items, [item])

    def test_find_missing_item(self):
        self.assertRaises(DoorstopError, self.document.find_item, "new")

    def test_find_item(self):
        item = self.document.find_item("c")
        self.assertEqual(self.document.items, [item])

    def test_reorder_from_index(self):
        """Verify items can be reordered from an index."""
        data = {
            "initial": 2.0,
            "outline": [
                {"a": None},
                {
                    "b": [
                        {"ba": [{"baa": None}, {"bac": None}]},
                        {"bb": [{"new": None}]},
                    ]
                },
                {"c": None},
            ],
        }
        expected = [
            Level("2"),
            Level("3.0"),
            Level("3.1.0"),
            Level("3.1.1"),
            Level("3.1.2"),
            Level("3.2.0"),
            Level("3.2.1"),
            Level("4"),
        ]

        # Act
        self.document._read_index = MagicMock(return_value=data)
        Document._reorder_from_index(self.document, "mock_path")

        # Assert
        self.document._read_index.assert_called_once_with("mock_path")
        actual = [item.level for item in self.document.items]
        self.assertListEqual(expected, actual)
        self.assertEqual(self.document.items[-2].text, "")

    def test_reorder_from_index_add(self):
        """Verify items can be added when reordering from an index."""
        data = {
            "initial": 2.0,
            "outline": [
                {"a": None},
                {
                    "b": [
                        {"ba": [{"baa": None}, {"new": None}, {"bac": None}]},
                        {"bb": [{"new": [{"text": "item_text"}]}]},
                    ]
                },
                {"c": None},
            ],
        }
        expected = [
            Level("2"),
            Level("3.0"),
            Level("3.1.0"),
            Level("3.1.1"),
            Level("3.1.2"),
            Level("3.1.3"),
            Level("3.2.0"),
            Level("3.2.1"),
            Level("4"),
        ]
        # Act
        self.document._read_index = MagicMock(return_value=data)
        Document._reorder_from_index(self.document, "mock_path")

        # Assert
        self.document._read_index.assert_called_once_with("mock_path")
        actual = [item.level for item in self.document.items]
        self.assertListEqual(expected, actual)
        self.assertEqual(self.document.items[-2].text, "item_text")

    def test_reorder_from_index_delete(self):
        """Verify items can be deleted when reordering from an index."""
        data = {
            "initial": 2.0,
            "outline": [
                {"a": None},
                {
                    "b": [
                        {"ba": [{"baa": None}, {"bab": None}, {"bac": None}]},
                        {"bb": [{"bba": None}]},
                    ]
                },
                {"c": None},
            ],
        }
        expected = [
            Level("2"),
            Level("3.0"),
            Level("3.1.0"),
            Level("3.1.1"),
            Level("3.1.2"),
            Level("3.1.3"),
            Level("3.2.0"),
            Level("3.2.1"),
            Level("4"),
        ]

        mock_item = self.document.add_item()
        # Act
        self.document._read_index = MagicMock(return_value=data)
        Document._reorder_from_index(self.document, "mock_path")

        # Assert
        self.document._read_index.assert_called_once_with("mock_path")
        items = []
        for item in self.document.items:
            if item is not mock_item:
                items.append(item)
        actual = [item.level for item in items]
        self.assertListEqual(expected, actual)
        self.assertEqual(mock_item.method_calls, [call.delete()])
