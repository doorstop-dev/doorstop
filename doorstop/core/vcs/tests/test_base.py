# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.vcs.base module."""

import os
import unittest
from unittest.mock import call, patch

from doorstop.core.tests import ROOT
from doorstop.core.vcs.base import BaseWorkingCopy


class SampleWorkingCopy(BaseWorkingCopy):
    """Sample WorkingCopy implementation."""

    def __init__(self, path):
        super().__init__(path)
        self._ignores_cache = ["*build*", "ignored.*", "*published*"]

    def lock(self, path):
        print(path)

    def edit(self, path):
        print(path)

    def add(self, path):
        print(path)

    def delete(self, path):
        print(path)

    def commit(self, message=None):
        print(message)


class TestSampleWorkingCopy(unittest.TestCase):
    """Tests for the doorstop.vcs.base module."""

    def setUp(self):
        self.wc = SampleWorkingCopy(None)

    @patch("os.environ", {})
    def test_ignored(self):
        """Verify ignored paths are detected."""
        self.assertTrue(self.wc.ignored("ignored.txt"))
        self.assertFalse(self.wc.ignored("not_ignored.txt"))
        self.assertTrue(self.wc.ignored("path/to/published.html"))
        self.assertTrue(self.wc.ignored("build/path/to/anything"))

    @patch("os.environ", {})
    def test_paths(self):
        """Verify that paths are cached correctly."""
        wc = SampleWorkingCopy(ROOT)
        paths = [relpath for path, _, relpath in wc.paths]
        self.assertEqual([], [x for x in paths if x.startswith(".git/")])
        self.assertNotEqual(
            [], [x for x in paths if x.startswith(os.path.join("doorstop", ""))]
        )


class TestBatchEdits(unittest.TestCase):
    """Tests for batching edits in the doorstop.vcs.base module."""

    def setUp(self):
        self.wc = SampleWorkingCopy(None)

    @patch.object(SampleWorkingCopy, "edit")
    def test_mark_edited_without_batch(self, mock_edit):
        """Verify an edit outside a batch is passed on at once."""
        self.wc.mark_edited("a.yml")
        mock_edit.assert_called_once_with("a.yml")

    @patch.object(SampleWorkingCopy, "edit_many")
    @patch.object(SampleWorkingCopy, "edit")
    def test_batch_edits(self, mock_edit, mock_edit_many):
        """Verify edits in a batch are flushed once, in order, without duplicates."""
        with self.wc.batch_edits():
            self.wc.mark_edited("b.yml")
            self.wc.mark_edited("a.yml")
            self.wc.mark_edited("b.yml")
            mock_edit_many.assert_not_called()
        mock_edit.assert_not_called()
        mock_edit_many.assert_called_once_with(["b.yml", "a.yml"])
        self.wc.mark_edited("c.yml")
        mock_edit.assert_called_once_with("c.yml")

    @patch.object(SampleWorkingCopy, "edit_many")
    @patch.object(SampleWorkingCopy, "edit")
    def test_nested_batch_joins_outer(self, mock_edit, mock_edit_many):
        """Verify an inner batch is flushed together with the outer one."""
        with self.wc.batch_edits():
            self.wc.mark_edited("a.yml")
            with self.wc.batch_edits():
                self.wc.mark_edited("b.yml")
            self.wc.mark_edited("c.yml")
            mock_edit_many.assert_not_called()
        mock_edit.assert_not_called()
        mock_edit_many.assert_called_once_with(["a.yml", "b.yml", "c.yml"])

    @patch.object(SampleWorkingCopy, "edit_many")
    def test_batch_edits_flushes_on_error(self, mock_edit_many):
        """Verify a batch is flushed when the block raises."""
        with self.assertRaises(ValueError):
            with self.wc.batch_edits():
                self.wc.mark_edited("a.yml")
                raise ValueError
        mock_edit_many.assert_called_once_with(["a.yml"])

    @patch.object(SampleWorkingCopy, "edit_many")
    def test_batch_edits_empty(self, mock_edit_many):
        """Verify an empty batch does not call the working copy."""
        with self.wc.batch_edits():
            pass
        mock_edit_many.assert_not_called()

    @patch.object(SampleWorkingCopy, "edit")
    def test_edit_many_default(self, mock_edit):
        """Verify the default edit_many edits each path in order."""
        self.wc.edit_many(["a.yml", "b.yml"])
        self.assertEqual([call("a.yml"), call("b.yml")], mock_edit.call_args_list)
