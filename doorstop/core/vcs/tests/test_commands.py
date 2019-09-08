# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the doorstop.vcs plugin modules."""

import unittest
from unittest.mock import Mock, call, patch

from doorstop.common import DoorstopError
from doorstop.core.vcs import load


class BaseTestCase:
    """Base TestCase for tests that need a working copy."""

    DIRECTORY = ''

    path = "path/to/mock/file.txt"
    dirpath = "path/to/mock/directory/"
    message = "A commit message"

    def setUp(self):
        with patch('os.listdir', Mock(return_value=[self.DIRECTORY])):
            self.wc = load('.')

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


@patch('subprocess.call')
class TestGit(BaseTestCase, unittest.TestCase):
    """Tests for the Git plugin."""

    DIRECTORY = '.git'

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


@patch('subprocess.call')
class TestSubversion(BaseTestCase, unittest.TestCase):
    """Tests for the Subversion plugin."""

    DIRECTORY = '.svn'

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


@patch('subprocess.call')
class TestVeracity(BaseTestCase, unittest.TestCase):
    """Tests for the Veracity plugin."""

    DIRECTORY = '.sgdrawer'

    def test_lock(self, mock_call):
        """Verify Veracity can lock files."""
        self.lock()
        calls = [call(("vv", "pull")), call(("vv", "update"))]
        mock_call.assert_has_calls(calls)

    def test_edit(self, mock_call):
        """Verify Veracity can (fake) edit files."""
        self.edit()
        mock_call.assert_has_calls([])

    def test_add(self, mock_call):
        """Verify Veracity can add files."""
        self.add()
        calls = [call(("vv", "add", self.path))]
        mock_call.assert_has_calls(calls)

    def test_delete(self, mock_call):
        """Verify Veracity can delete files."""
        self.delete()
        calls = [call(("vv", "remove", self.path))]
        mock_call.assert_has_calls(calls)

    def test_commit(self, mock_call):
        """Verify Veracity can commit files."""
        self.commit()
        calls = [
            call(("vv", "commit", "--message", self.message)),
            call(("vv", "push")),
        ]
        mock_call.assert_has_calls(calls)


@patch('subprocess.call')
class TestMercurial(BaseTestCase, unittest.TestCase):
    """Tests for the Mercurial plugin."""

    DIRECTORY = '.hg'

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
