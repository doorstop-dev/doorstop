# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.vcs plugin modules."""

import subprocess
import unittest
from unittest.mock import Mock, call, patch

from doorstop.common import DoorstopError
from doorstop.core.vcs import load


class BaseTestCase:
    """Base TestCase for tests that need a working copy."""

    DIRECTORY = ""

    path = "path/to/mock/file.txt"
    dirpath = "path/to/mock/directory/"
    message = "A commit message"

    def setUp(self):
        with patch("os.listdir", Mock(return_value=[self.DIRECTORY])):
            self.wc = load(".")

    def lock(self):
        """Lock a file in the working copy."""
        self.wc.lock(self.path)

    def edit(self):
        """Edit a file in the working copy."""
        self.wc.edit(self.path)

    def add(self):
        """Add a file to the working copy."""
        self.wc.add(self.path)

    def delete(self):
        """Remove a file in the working copy."""
        self.wc.delete(self.path)

    def commit(self):
        """Save all files in the working copy."""
        self.wc.commit(self.message)

    def test_missing_command(self, mock_call):
        """Verify that a missing command raises a DoorstopError."""
        mock_call.side_effect = FileNotFoundError
        self.assertRaises(DoorstopError, self.add)


@patch("subprocess.call")
class TestGit(BaseTestCase, unittest.TestCase):
    """Tests for the Git plugin."""

    DIRECTORY = ".git"

    def test_lock(self, mock_call):
        """Verify Git can (fake) lock files."""
        self.lock()
        calls = [call(("git", "pull"))]
        mock_call.assert_has_calls(calls)

    def test_edit(self, mock_call):
        """Verify Git can edit files."""
        self.edit()
        calls = [call(("git", "add", self.path))]
        mock_call.assert_has_calls(calls)

    def test_add(self, mock_call):
        """Verify Git can add files."""
        self.add()
        calls = [call(("git", "add", self.path))]
        mock_call.assert_has_calls(calls)

    def test_delete(self, mock_call):
        """Verify Git can delete files."""
        self.delete()
        calls = [call(("git", "rm", self.path, "--force", "--quiet"))]
        mock_call.assert_has_calls(calls)

    def test_commit(self, mock_call):
        """Verify Git can commit files."""
        self.commit()
        calls = [
            call(("git", "commit", "--all", "--message", self.message)),
            call(("git", "push")),
        ]
        mock_call.assert_has_calls(calls)

    def test_edit_many(self, mock_call):
        """Verify Git stages many edited files with one command."""
        self.wc.edit_many(["a.yml", "b.yml"])
        mock_call.assert_called_once_with(("git", "add", "--", "a.yml", "b.yml"))

    def test_edit_many_short_paths_one_call(self, mock_call):
        """Verify Git stages many short paths with a single command."""
        paths = ["dir/item{:05d}.yml".format(i) for i in range(450)]
        self.wc.edit_many(iter(paths))
        mock_call.assert_called_once_with(("git", "add", "--", *paths))

    def test_edit_many_deep_paths_chunks(self, mock_call):
        """Verify Git splits deep paths by command-line length, in order."""
        # 297 characters + 3 = 300 per path, so 100 paths fill MAX_CHARS
        paths = ["{}/item{:05d}.yml".format("d" * 283, i) for i in range(250)]
        self.wc.edit_many(paths)
        self.assertEqual(
            [
                call(("git", "add", "--", *paths[:100])),
                call(("git", "add", "--", *paths[100:200])),
                call(("git", "add", "--", *paths[200:])),
            ],
            mock_call.call_args_list,
        )
        for args, _ in mock_call.call_args_list:
            self.assertLess(len(subprocess.list2cmdline(args[0])), 32767)

    def test_edit_many_path_longer_than_limit(self, mock_call):
        """Verify a single path above the budget is still staged on its own."""
        paths = ["a.yml", "d" * 30000 + ".yml", "b.yml"]
        self.wc.edit_many(paths)
        self.assertEqual(
            [
                call(("git", "add", "--", "a.yml")),
                call(("git", "add", "--", paths[1])),
                call(("git", "add", "--", "b.yml")),
            ],
            mock_call.call_args_list,
        )

    def test_edit_many_empty(self, mock_call):
        """Verify Git does nothing for an empty path list."""
        self.wc.edit_many([])
        mock_call.assert_not_called()


@patch("subprocess.call")
class TestSubversion(BaseTestCase, unittest.TestCase):
    """Tests for the Subversion plugin."""

    DIRECTORY = ".svn"

    def test_lock(self, mock_call):
        """Verify Subversion can lock files."""
        self.lock()
        calls = [call(("svn", "update")), call(("svn", "lock", self.path))]
        mock_call.assert_has_calls(calls)

    def test_edit(self, mock_call):
        """Verify Subversion can (fake) edit files."""
        self.edit()
        mock_call.assert_has_calls([])

    def test_add(self, mock_call):
        """Verify Subversion can add files."""
        self.add()
        calls = [call(("svn", "add", self.path))]
        mock_call.assert_has_calls(calls)

    def test_delete(self, mock_call):
        """Verify Subversion can delete files."""
        self.delete()
        calls = [call(("svn", "delete", self.path))]
        mock_call.assert_has_calls(calls)

    def test_commit(self, mock_call):
        """Verify Subversion can commit files."""
        self.commit()
        calls = [call(("svn", "commit", "--message", self.message))]
        mock_call.assert_has_calls(calls)


@patch("subprocess.call")
class TestMercurial(BaseTestCase, unittest.TestCase):
    """Tests for the Mercurial plugin."""

    DIRECTORY = ".hg"

    def test_lock(self, mock_call):
        """Verify Mercurial can (fake) lock files."""
        self.lock()
        calls = [call(("hg", "pull", "-u"))]
        mock_call.assert_has_calls(calls)

    def test_edit(self, mock_call):
        """Verify Mercurial can edit files."""
        self.edit()
        calls = [call(("hg", "add", self.path))]
        mock_call.assert_has_calls(calls)

    def test_add(self, mock_call):
        """Verify Mercurial can add files."""
        self.add()
        calls = [call(("hg", "add", self.path))]
        mock_call.assert_has_calls(calls)

    def test_delete(self, mock_call):
        """Verify Mercurial can delete files."""
        self.delete()
        calls = [call(("hg", "remove", self.path, "--force"))]
        mock_call.assert_has_calls(calls)

    def test_commit(self, mock_call):
        """Verify Mercurial can commit files."""
        self.commit()
        calls = [
            call(("hg", "commit", "--message", self.message)),
            call(("hg", "push")),
        ]
        mock_call.assert_has_calls(calls)
