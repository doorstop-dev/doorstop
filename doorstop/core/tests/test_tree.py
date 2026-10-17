#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.core.tree module."""

import logging
import operator
import os
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock, Mock, patch

import pytest

from doorstop import common
from doorstop.common import DoorstopError, DoorstopInfo, DoorstopWarning
from doorstop.core import publisher
from doorstop.core.builder import build
from doorstop.core.document import Document
from doorstop.core.tests import (
    EMPTY,
    FILES,
    GOLDEN_MASTER_FILES,
    ROOT,
    SYS,
    TESTS_ROOT,
    MockDocumentSkip,
)
from doorstop.core.tests.helpers import on_error_with_retry
from doorstop.core.tree import Tree, _uid_key
from doorstop.core.types import UID
from doorstop.core.vcs.mockvcs import WorkingCopy as MockWorkingCopy


@pytest.fixture(autouse=True, scope="class")
def reset_fixture_files():
    """Reset only Git-tracked YAML files after each test class."""
    yield

    # Cleanup: Reset only YAML files that are in Git
    try:
        test_dir = os.path.dirname(__file__)

        # Get all git-tracked YAML files in files/
        result = subprocess.run(
            ["git", "ls-files", "files/*.yml", "files/*.yaml"],
            capture_output=True,
            text=True,
            cwd=test_dir,
            timeout=5,
            check=False,
        )

        if result.returncode == 0 and result.stdout.strip():
            yaml_files = result.stdout.strip().split("\n")

            # Exclude golden master files from reset as they are
            # intentionally updated by tests using the golden master pattern
            yaml_files = [
                f
                for f in yaml_files
                if os.path.abspath(os.path.join(test_dir, f)) not in GOLDEN_MASTER_FILES
            ]

            if not yaml_files:
                return

            # Reset those files
            subprocess.run(
                ["git", "checkout", "--"] + yaml_files,
                capture_output=True,
                cwd=test_dir,
                timeout=5,
                check=False,
            )
    except Exception:
        pass


@patch("doorstop.core.document.Document", MockDocumentSkip)
class TestTreeStrings(unittest.TestCase):
    """Unit tests for the Tree class using strings."""

    @classmethod
    def setUpClass(cls):
        a = Tree("a", root=".")
        b1 = Tree("b1", parent=a, root=".")
        d = Tree("d", parent=b1, root=".")
        e = Tree("e", parent=d, root=".")
        b2 = Tree("b2", parent=a, root=".")
        c1 = Tree("c1", parent=b2, root=".")
        c2 = Tree("c2", parent=b2, root=".")
        a.children = [b1, b2]
        b1.children = [d]
        d.children = [e]
        b2.children = [c1, c2]
        cls.tree = a

    def test_repr(self):
        """Verify trees can be represented."""
        text = "<Tree a <- [ b1 <- [ d <- [ e ] ], b2 <- [ c1, c2 ] ]>"
        self.assertEqual(text, repr(self.tree))

    def test_str(self):
        """Verify trees can be converted to strings."""
        text = "a <- [ b1 <- [ d <- [ e ] ], b2 <- [ c1, c2 ] ]"
        self.assertEqual(text, str(self.tree))

    def test_len(self):
        """Verify a tree lengths are correct."""
        self.assertEqual(7, len(self.tree))

    def test_getitem(self):
        """Verify item access is not allowed on trees."""
        self.assertRaises(IndexError, operator.getitem, self.tree, 0)

    def test_iter(self):
        """Verify a tree can be iterated over."""
        items = [d for d in self.tree]
        self.assertListEqual(["a", "b1", "d", "e", "b2", "c1", "c2"], items)

    def test_contains(self):
        """Verify a tree can be checked for contents."""
        child = self.tree.children[1].children[0]
        self.assertIn(child.document, self.tree)

    def test_draw_utf8(self):
        """Verify trees structure can be drawn (UTF-8)."""
        text = (
            "a" + "\n"
            "│   " + "\n"
            "├── b1" + "\n"
            "│   │   " + "\n"
            "│   └── d" + "\n"
            "│       │   " + "\n"
            "│       └── e" + "\n"
            "│   " + "\n"
            "└── b2" + "\n"
            "    │   " + "\n"
            "    ├── c1" + "\n"
            "    │   " + "\n"
            "    └── c2"
        )
        logging.debug("expected:\n%s", text)
        text2 = self.tree.draw(encoding="UTF-8")
        logging.debug("actual:\n%s", text2)
        self.assertEqual(text, text2)

    def test_draw_cp437(self):
        """Verify trees structure can be drawn (cp437)."""
        text = (
            "a" + "\n"
            "┬   " + "\n"
            "├── b1" + "\n"
            "│   ┬   " + "\n"
            "│   └── d" + "\n"
            "│       ┬   " + "\n"
            "│       └── e" + "\n"
            "│   " + "\n"
            "└── b2" + "\n"
            "    ┬   " + "\n"
            "    ├── c1" + "\n"
            "    │   " + "\n"
            "    └── c2"
        )
        logging.debug("expected:\n%s", text)
        text2 = self.tree.draw(encoding="cp437")
        logging.debug("actual:\n%s", text2)
        self.assertEqual(text, text2)

    def test_draw_unknown(self):
        """Verify trees structure can be drawn (unknown)."""
        text = (
            "a" + "\n"
            "|   " + "\n"
            "+-- b1" + "\n"
            "|   |   " + "\n"
            "|   +-- d" + "\n"
            "|       |   " + "\n"
            "|       +-- e" + "\n"
            "|   " + "\n"
            "+-- b2" + "\n"
            "    |   " + "\n"
            "    +-- c1" + "\n"
            "    |   " + "\n"
            "    +-- c2"
        )
        logging.debug("expected:\n%s", text)
        text2 = self.tree.draw(encoding="unknown")
        logging.debug("actual:\n%s", text2)
        self.assertEqual(text, text2)

    @patch("doorstop.settings.REORDER", False)
    def test_from_list(self):
        """Verify a tree can be created from a list."""
        a = MockDocumentSkip(EMPTY)
        a.prefix = "A"  # type: ignore
        b = MockDocumentSkip(EMPTY)
        b.prefix = "B"  # type: ignore
        b.parent = "A"  # type: ignore
        c = MockDocumentSkip(EMPTY)
        c.prefix = "C"  # type: ignore
        c.parent = "B"  # type: ignore
        docs = [a, b, c]
        tree = Tree.from_list(docs)
        self.assertEqual(3, len(tree))
        self.assertTrue(tree.validate())

    def test_from_list_no_root(self):
        """Verify an error occurs when the tree has no root."""
        a = MockDocumentSkip(EMPTY)
        a.prefix = "A"  # type: ignore
        a.parent = "B"  # type: ignore
        b = MockDocumentSkip(EMPTY)
        b.prefix = "B"  # type: ignore
        b.parent = "A"  # type: ignore
        docs = [a, b]
        self.assertRaises(DoorstopError, Tree.from_list, docs)

    def test_from_list_multiple_roots(self):
        """Verify an error occurs when the tree has multiple roots."""
        a = MockDocumentSkip(EMPTY)
        a.prefix = "A"  # type: ignore
        b = MockDocumentSkip(EMPTY)
        b.prefix = "B"  # type: ignore
        docs = [a, b]
        self.assertRaises(DoorstopError, Tree.from_list, docs)

    def test_from_list_missing_parent(self):
        """Verify an error occurs when a node has a missing parent."""
        a = MockDocumentSkip(EMPTY)
        a.prefix = "A"  # type: ignore
        b = MockDocumentSkip(EMPTY)
        b.prefix = "B"  # type: ignore
        b.parent = "A"  # type: ignore
        c = MockDocumentSkip(EMPTY)
        c.prefix = "C"  # type: ignore
        c.parent = "?"  # type: ignore
        docs = [a, b, c]
        self.assertRaises(DoorstopError, Tree.from_list, docs)

    def test_place_no_parent(self):
        """Verify an error occurs when a node is missing a parent."""
        a = MockDocumentSkip(EMPTY)
        a.prefix = "A"  # type: ignore
        b = MockDocumentSkip(EMPTY)
        b.prefix = "B"  # type: ignore
        tree = Tree(a)
        self.assertRaises(DoorstopError, tree._place, b)  # pylint: disable=W0212


@patch("doorstop.core.document.Document", MockDocumentSkip)
@patch("doorstop.core.tree.Document", MockDocumentSkip)
class TestTree(unittest.TestCase):
    """Unit tests for the Tree class."""

    def setUp(self):
        document = Document(SYS)
        self.tree = Tree(document)
        document.tree = self.tree
        document = Document(FILES)
        self.tree._place(document)  # pylint: disable=W0212
        document.tree = self.tree
        self.tree._vcs = MagicMock()  # pylint: disable=W0212

    @patch("doorstop.core.vcs.find_root", Mock(return_value=EMPTY))
    def test_place_empty(self):
        """Verify a document can be placed in an empty tree."""
        tree = build(EMPTY)
        doc = MockDocumentSkip.new(tree, os.path.join(EMPTY, "temp"), EMPTY, "TEMP")
        tree._place(doc)  # pylint: disable=W0212
        self.assertEqual(1, len(tree))

    @patch("doorstop.core.vcs.find_root", Mock(return_value=EMPTY))
    def test_place_empty_no_parent(self):
        """Verify a document with parent cannot be placed in an empty tree."""
        tree = build(EMPTY)
        doc = MockDocumentSkip.new(
            tree, os.path.join(EMPTY, "temp"), EMPTY, "TEMP", parent="REQ"
        )
        self.assertRaises(DoorstopError, tree._place, doc)  # pylint: disable=W0212

    def test_documents(self):
        """Verify the documents in a tree can be accessed."""
        documents = self.tree.documents
        self.assertEqual(2, len(documents))
        for document in self.tree:
            logging.debug("document: {}".format(document))
            self.assertIs(self.tree, document.tree)

    @patch("doorstop.core.document.Document.get_issues")
    def test_validate(self, mock_get_issues):
        """Verify trees can be checked."""
        logging.info("tree: {}".format(self.tree))
        self.assertTrue(self.tree.validate())
        self.assertEqual(2, mock_get_issues.call_count)

    def test_validate_no_documents(self):
        """Verify an empty tree can be checked."""
        tree = Tree(None, root=".")
        self.assertTrue(tree.validate())

    @patch("doorstop.settings.REORDER", False)
    @patch(
        "doorstop.core.document.Document.get_issues",
        Mock(
            return_value=[
                DoorstopError("error"),
                DoorstopWarning("warning"),
                DoorstopInfo("info"),
            ]
        ),
    )
    def test_validate_document(self):
        """Verify a document error fails the tree validation."""
        self.assertFalse(self.tree.validate())

    @patch("doorstop.core.document.Document.get_issues", Mock(return_value=[]))
    def test_validate_hook(self):
        """Verify a document hook can be called."""
        mock_hook = MagicMock()
        self.tree.validate(document_hook=mock_hook)
        self.assertEqual(2, mock_hook.call_count)

    @patch("doorstop.core.tree.Tree.get_issues", Mock(return_value=[]))
    def test_issues(self):
        """Verify an tree's issues convenience property can be accessed."""
        self.assertEqual(0, len(self.tree.issues))

    def test_get_traceability(self):
        """Verify traceability rows are correct."""
        rows = [
            (self.tree.find_item("SYS001"), self.tree.find_item("REQ001")),
            (self.tree.find_item("SYS002"), self.tree.find_item("REQ001")),
            (None, self.tree.find_item("REQ002")),
            (None, self.tree.find_item("REQ004")),
        ]
        # Act
        rows2 = self.tree.get_traceability()
        # Assert
        self.assertListEqual(rows, rows2)

    def test_new_document(self):
        """Verify a new document can be created on a tree."""
        self.tree.create_document(EMPTY, "_TEST", parent="REQ")

    def test_new_document_unknown_parent(self):
        """Verify an exception is raised for an unknown parent."""
        temp = tempfile.mkdtemp()
        self.assertRaises(
            DoorstopError, self.tree.create_document, temp, "_TEST", parent="UNKNOWN"
        )
        self.assertFalse(os.path.exists(temp))

    @patch("doorstop.core.document.Document.add_item")
    def test_add_item(self, mock_add_item):
        """Verify an item can be added to a document."""
        self.tree.add_item("REQ")
        mock_add_item.assert_called_once_with(number=None, level=None, reorder=True)

    @patch("doorstop.core.document.Document.add_item")
    def test_add_item_level(self, mock_add):
        """Verify an item can be added to a document with a level."""
        self.tree.add_item("REQ", level="1.2.3")
        mock_add.assert_called_once_with(number=None, level="1.2.3", reorder=True)

    def test_add_item_unknown_prefix(self):
        """Verify an exception is raised for an unknown prefix (item)."""
        # Cache miss
        self.assertRaises(DoorstopError, self.tree.add_item, "UNKNOWN")
        # Cache hit
        self.assertRaises(DoorstopError, self.tree.add_item, "UNKNOWN")

    @patch("doorstop.settings.REORDER", False)
    @patch("doorstop.core.item.Item.delete")
    def test_remove_item(self, mock_delete):
        """Verify an item can be removed from a document."""
        self.tree.remove_item("req1", reorder=False)
        mock_delete.assert_called_once_with()

    def test_remove_item_unknown_item(self):
        """Verify an exception is raised removing an unknown item."""
        self.assertRaises(DoorstopError, self.tree.remove_item, "req9999")

    @patch("doorstop.core.item.Item.link")
    def test_link_items(self, mock_link):
        """Verify two items can be linked."""
        self.tree.link_items("req1", "req2")
        mock_link.assert_called_once_with("REQ002")

    def test_link_items_self_reference(self):
        """Verify an exception is raised with a self reference."""
        try:
            self.tree.link_items("req1", "req1")
            self.fail()
        except DoorstopError as error:
            self.assertEqual(str(error), "link would be self reference")

    def test_link_items_cyclic_dependency(self):
        """Verify an exception is raised with a cyclic dependency."""
        self.tree.link_items("req1", "sys2")
        msg = "^link would create a cyclic dependency: SYS002 -> REQ001 -> SYS002$"
        self.assertRaisesRegex(DoorstopError, msg, self.tree.link_items, "sys2", "req1")

    def test_link_items_unknown_child_prefix(self):
        """Verify an exception is raised with an unknown child prefix."""
        self.assertRaises(DoorstopError, self.tree.link_items, "unknown1", "req2")

    def test_link_items_unknown_child_number(self):
        """Verify an exception is raised with an unknown child number."""
        self.assertRaises(DoorstopError, self.tree.link_items, "req9999", "req2")

    def test_link_items_unknown_parent_prefix(self):
        """Verify an exception is raised with an unknown parent prefix."""
        self.assertRaises(DoorstopError, self.tree.link_items, "req1", "unknown1")

    def test_link_items_unknown_parent_number(self):
        """Verify an exception is raised with an unknown parent prefix."""
        self.assertRaises(DoorstopError, self.tree.link_items, "req1", "req9999")

    @patch("doorstop.core.item.Item.unlink")
    def test_unlink_items(self, mock_unlink):
        """Verify two items can be unlinked."""
        self.tree.unlink_items("req3", "req1")
        mock_unlink.assert_called_once_with("REQ001")

    def test_unlink_items_unknown_child_prefix(self):
        """Verify an exception is raised with an unknown child prefix."""
        self.assertRaises(DoorstopError, self.tree.unlink_items, "unknown1", "req1")

    def test_unlink_items_unknown_child_number(self):
        """Verify an exception is raised with an unknown child number."""
        self.assertRaises(DoorstopError, self.tree.unlink_items, "req9999", "req1")

    def test_unlink_items_unknown_parent_prefix(self):
        """Verify an exception is raised with an unknown parent prefix."""
        # Cache miss
        self.assertRaises(DoorstopError, self.tree.unlink_items, "req3", "unknown1")
        # Cache hit
        self.assertRaises(DoorstopError, self.tree.unlink_items, "req3", "unknown1")

    def test_unlink_items_unknown_parent_number(self):
        """Verify an exception is raised with an unknown parent prefix."""
        self.assertRaises(DoorstopError, self.tree.unlink_items, "req3", "req9999")

    @patch("doorstop.core.editor.launch")
    def test_edit_item(self, mock_launch):
        """Verify an item can be edited in a tree."""
        self.tree.edit_item("req2", launch=True)
        path = os.path.join(FILES, "REQ002.yml")
        mock_launch.assert_called_once_with(path, tool=None)

    def test_edit_item_unknown_prefix(self):
        """Verify an exception is raised for an unknown prefix (document)."""
        self.assertRaises(DoorstopError, self.tree.edit_item, "unknown1")

    def test_edit_item_unknown_number(self):
        """Verify an exception is raised for an unknown number."""
        self.assertRaises(DoorstopError, self.tree.edit_item, "req9999")

    def test_find_item(self):
        """Verify an item can be found by exact UID."""
        # Cache miss
        item = self.tree.find_item("req2-001")
        self.assertIsNot(None, item)
        # Cache hit
        item2 = self.tree.find_item("req2-001")
        self.assertIs(item2, item)

    def test_find_document(self):
        """Verify an document can be found by prefix."""
        # Cache miss
        document = self.tree.find_document("req")
        self.assertIsNot(None, document)
        # Cache hit
        document2 = self.tree.find_document("req")
        self.assertIs(document2, document)

    def test_load(self):
        """Verify an a tree can be reloaded."""
        self.tree.load()
        self.tree.load()  # should return immediately

    @patch("doorstop.core.document.Document.delete")
    def test_delete(self, mock_delete):
        """Verify a tree can be deleted."""
        self.tree.delete()
        self.assertEqual(0, len(self.tree))
        self.assertEqual(2, mock_delete.call_count)
        self.tree.delete()  # ensure a second delete is ignored


def _fixture_tree(test, edge_cases=True):
    """Build copies of the repository's own trees in a temp folder, with a mock VCS.

    With `edge_cases`, LLT001 links to its parent in lower case and LLT002 is
    inactive, so both edge cases of the child-link check are covered.
    """
    temp = tempfile.mkdtemp()
    test.addCleanup(shutil.rmtree, temp, onerror=on_error_with_retry)
    shutil.copytree(os.path.join(ROOT, "reqs"), os.path.join(temp, "reqs"))
    shutil.copytree(os.path.join(TESTS_ROOT, "docs"), os.path.join(temp, "llt"))
    shutil.copytree(
        os.path.join(ROOT, "doorstop", "cli", "tests", "docs"),
        os.path.join(temp, "hlt"),
    )
    if edge_cases:
        path = os.path.join(temp, "llt", "LLT001.yml")
        text = common.read_text(path).replace("- REQ003:", "- req003:")
        common.write_text(text, path)
        path = os.path.join(temp, "llt", "LLT002.yml")
        text = common.read_text(path).replace("active: true", "active: false")
        common.write_text(text, path)
    with patch("doorstop.settings.ADDREMOVE_FILES", False):
        tree = build(cwd=temp, root=temp)
    tree._vcs = MockWorkingCopy(temp)  # pylint: disable=W0212
    return tree


class TestValidateBatching(unittest.TestCase):
    """Unit tests for batching VCS edits while a tree is checked."""

    def setUp(self):
        self.tree = _fixture_tree(self)

    def _assert_stages_every_active_item_once(self):
        expected = sorted(
            item.path for document in self.tree for item in document if item.active
        )
        with patch.object(MockWorkingCopy, "edit") as mock_edit, patch.object(
            MockWorkingCopy, "edit_many"
        ) as mock_edit_many:
            self.tree.validate()
        mock_edit.assert_not_called()
        staged = [path for args, _ in mock_edit_many.call_args_list for path in args[0]]
        self.assertEqual(expected, sorted(staged))

    @patch("doorstop.settings.REFORMAT", True)
    @patch("doorstop.settings.ADDREMOVE_FILES", True)
    def test_validate_stages_every_item_once(self):
        """Verify a check stages every active item in batched calls."""
        self._assert_stages_every_active_item_once()

    @patch("doorstop.settings.REFORMAT", True)
    @patch("doorstop.settings.ADDREMOVE_FILES", True)
    def test_closed_check_flushes(self):
        """Verify a check that is stopped early still stages what it saved."""
        with patch.object(MockWorkingCopy, "edit_many") as mock_edit_many:
            issues = self.tree.get_issues()
            next(issues)
            mock_edit_many.assert_not_called()
            issues.close()
        mock_edit_many.assert_called_once()

    @patch("doorstop.settings.REFORMAT", True)
    @patch("doorstop.settings.ADDREMOVE_FILES", False)
    def test_no_batch_without_addremove(self):
        """Verify nothing is staged when files are not added automatically."""
        with patch.object(MockWorkingCopy, "batch_edits") as mock_batch, patch.object(
            MockWorkingCopy, "edit"
        ) as mock_edit:
            self.tree.validate()
        mock_batch.assert_not_called()
        mock_edit.assert_not_called()

    @patch("doorstop.settings.REORDER", True)
    @patch("doorstop.settings.REFORMAT", True)
    @patch("doorstop.settings.ADDREMOVE_FILES", True)
    def test_validate_with_reorder_stages_every_item_once(self):
        """Verify a check that renumbers documents still stages each item once.

        The renumbering opens its own batch, which must join the check's batch.
        """
        self._assert_stages_every_active_item_once()


class TestReorderBatching(unittest.TestCase):
    """Unit tests for batching VCS edits while a document is renumbered."""

    def setUp(self):
        self.document = _fixture_tree(self).find_document("LLT")
        self.expected = [item.path for item in self.document.items]

    @patch("doorstop.settings.ADDREMOVE_FILES", True)
    def test_reorder_stages_in_one_call(self):
        """Verify renumbering stages every item of the document in one call."""
        with patch.object(MockWorkingCopy, "edit") as mock_edit, patch.object(
            MockWorkingCopy, "edit_many"
        ) as mock_edit_many:
            self.document.reorder()
        mock_edit.assert_not_called()
        mock_edit_many.assert_called_once_with(self.expected)

    @patch("doorstop.settings.ADDREMOVE_FILES", False)
    def test_reorder_without_addremove(self):
        """Verify renumbering stages nothing when files are not added automatically."""
        with patch.object(MockWorkingCopy, "batch_edits") as mock_batch, patch.object(
            MockWorkingCopy, "edit"
        ) as mock_edit:
            self.document.reorder()
        mock_batch.assert_not_called()
        mock_edit.assert_not_called()


class TestChildLinkIndex(unittest.TestCase):
    """Unit tests for finding child items through the link index."""

    @staticmethod
    def _children(tree, find_all):
        """Return the child UIDs and documents of every item, as strings."""
        result = {}
        for document in tree:
            for item in document:
                items, documents = item.find_child_items_and_documents(
                    document=document, tree=tree, find_all=find_all
                )
                result[str(item.uid)] = (
                    [str(child.uid) for child in items],
                    [str(child) for child in documents],
                )
        return result

    def test_same_children(self):
        """Verify the index finds the same children as the linear scan."""
        tree = _fixture_tree(self)
        tree._child_index_active = True  # pylint: disable=W0212
        for find_all in (True, False):
            with patch.object(Tree, "_find_linking_items", return_value=None):
                linear = self._children(tree, find_all)
            self.assertEqual(linear, self._children(tree, find_all))
        # document order follows os.walk, which differs between file systems
        for uid, child in (("REQ003", "LLT001"), ("REQ004", "LLT002")):
            items, documents = linear[uid]
            self.assertEqual(
                ([child], ["EXT", "LLT", "TUT"]), (items, sorted(documents))
            )

    @patch("doorstop.settings.ADDREMOVE_FILES", False)
    def test_same_issues(self):
        """Verify a check reports the same issues with and without the index."""

        def issues(tree):
            return [str(i).replace(tree.root, "<root>") for i in tree.get_issues()]

        indexed = issues(_fixture_tree(self))
        with patch.object(Tree, "_find_linking_items", return_value=None):
            linear = issues(_fixture_tree(self))
        self.assertEqual(linear, indexed)


def _cross_linked_tree(test):
    """Build a tree whose links skip, cross, reverse and loop around the document tree.

    Documents:

        REQ
         +-- SW
         |    +-- TST
         +-- HW

    Items and links (A ---> B means A links to B):

        REQ    || REQ003 ---> REQ001    REQ002
               ||             ^   ^       |
               ||             |   |       |
        SW, HW ||             | SW001 <---+   SW002 <--> HW001   SW003 ---> HW009
               ||             |     ^
               ||             |     |
        TST    ||         TST002  TST001

    - SW001 -> REQ001, TST001 -> SW001: follow the tree
    - TST002 -> REQ001: skips SW
    - REQ002 -> SW001: goes back up into REQ
    - SW002 <-> HW001: crosses branches and closes a cycle
    - REQ003 -> REQ001: stays in one document
    - SW003 -> HW009: links to an unknown item
    """
    temp = tempfile.mkdtemp()
    test.addCleanup(shutil.rmtree, temp, onerror=on_error_with_retry)
    links = {
        "SW001": "REQ001",
        "TST001": "SW001",
        "TST002": "REQ001",
        "SW002": "HW001",
        "REQ002": "SW001",
        "HW001": "SW002",
        "REQ003": "REQ001",
        "SW003": "HW009",
    }
    with patch("doorstop.settings.ADDREMOVE_FILES", False):
        tree = build(cwd=temp, root=temp)
        tree._vcs = MockWorkingCopy(temp)  # pylint: disable=W0212
        for prefix, parent, count in (
            ("REQ", None, 3),
            ("SW", "REQ", 3),
            ("HW", "REQ", 1),
            ("TST", "SW", 2),
        ):
            path = os.path.join(temp, prefix.lower())
            document = tree.create_document(path, prefix, parent=parent)
            for _ in range(count):
                document.add_item()
        for child, parent in links.items():
            tree.find_item(child).link(parent)
    return tree


def _uids(rows):
    """Return traceability rows as UID strings, with "" for empty cells."""
    return [[str(item.uid) if item else "" for item in row] for row in rows]


class TestFullTraceability(unittest.TestCase):
    """Unit tests for the full traceability matrix and child links."""

    def setUp(self):
        self.tree = _cross_linked_tree(self)

    def test_full_rows(self):
        """Verify every maximal path that visits each document once is a row."""
        rows = [
            ["REQ001", "SW001", "TST001", ""],
            ["REQ001", "", "TST002", ""],
            ["REQ002", "SW001", "", ""],
            ["REQ003", "", "", ""],
            ["", "SW002", "", "HW001"],
            ["", "SW003", "", ""],
        ]
        prefixes = [str(document.prefix) for document in self.tree.documents]
        self.assertEqual(["REQ", "SW", "TST", "HW"], prefixes)
        self.assertEqual(rows, _uids(self.tree.get_traceability(full=True)))

    def test_standard_rows_unchanged(self):
        """Verify the standard rows still only follow the document tree."""
        with patch("doorstop.settings.ADDREMOVE_FILES", False):
            # standard rows recurse forever on a cycle of parent links
            self.tree.find_item("HW001").unlink("SW002")
        rows = [
            ["REQ001", "SW001", "TST001", ""],
            ["", "", "", "HW001"],
        ]
        self.assertEqual(rows, _uids(self.tree.get_traceability()))

    def test_full_child_links(self):
        """Verify full child links come from every document, sorted by level."""
        children = {
            "REQ001": ["SW001", "TST002", "REQ003"],
            "REQ002": [],
            "REQ003": [],
            "SW001": ["TST001", "REQ002"],
            "SW002": ["HW001"],
            "SW003": [],
            "TST001": [],
            "TST002": [],
            "HW001": ["SW002"],
        }
        found = {
            str(item.uid): [str(uid) for uid in item.find_child_links(full=True)]
            for document in self.tree
            for item in document
        }
        self.assertEqual(children, found)
        # the child documents do not change
        item = self.tree.find_item("REQ001")
        _, documents = item.find_child_items_and_documents(full=True)
        self.assertEqual(["SW", "HW"], [str(d.prefix) for d in documents])

    @patch("doorstop.settings.PUBLISH_FULL_TRACEABILITY", True)
    def test_publish_full_matrix(self):
        """Verify the published matrix holds the full rows."""
        temp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp, onerror=on_error_with_retry)
        publisher.publish(self.tree, temp, ".html")
        text = common.read_text(os.path.join(temp, "traceability.csv"))
        expected = (
            "REQ,SW,TST,HW\n"
            "REQ001,SW001,TST001,\n"
            "REQ001,,TST002,\n"
            "REQ002,SW001,,\n"
            "REQ003,,,\n"
            ",SW002,,HW001\n"
            ",SW003,,\n"
        )
        self.assertEqual(expected, text)

    @patch("doorstop.settings.PUBLISH_FULL_TRACEABILITY", True)
    def test_publish_full_child_links(self):
        """Verify published documents list child links from every document."""
        lines = publisher.publish_lines(self.tree.find_document("REQ"), ".md")
        expected = (
            "# 1.0 REQ001 {#REQ001}\n\n"
            "*Child links: SW001, TST002, REQ003*\n\n"
            "## 1.1 REQ002 {#REQ002}\n\n"
            "*Parent links: SW001*\n\n"
            "## 1.2 REQ003 {#REQ003}\n\n"
            "*Parent links: REQ001*\n"
        )
        self.assertEqual(expected, "\n".join(lines))


class TestFullTraceabilityRepository(unittest.TestCase):
    """Unit tests for the full traceability matrix on the repository's trees."""

    def test_full_equals_standard(self):
        """Verify full rows equal standard rows when all links follow the tree."""
        tree = _fixture_tree(self, edge_cases=False)
        rows = tree.get_traceability()
        self.assertEqual(rows, tree.get_traceability(full=True))
        self.assertGreater(len(rows), 30)


class TestUidKey(unittest.TestCase):
    """Unit tests for the link index key."""

    def test_valid_uids_ignore_case_and_separator(self):
        """Verify the key matches UID equality for valid UIDs."""
        self.assertEqual(("uid", "req", 1, ""), _uid_key(UID("REQ001")))
        self.assertEqual(_uid_key(UID("REQ001")), _uid_key(UID("req001")))
        self.assertEqual(UID("REQ001"), UID("REQ-001"))
        self.assertEqual(_uid_key(UID("REQ001")), _uid_key(UID("REQ-001")))

    def test_invalid_uids_compare_by_value(self):
        """Verify the key of an invalid UID is its lower-case value."""
        self.assertEqual(("raw", "req"), _uid_key(UID("REQ")))
        self.assertEqual(_uid_key(UID("REQ")), _uid_key(UID("req")))
