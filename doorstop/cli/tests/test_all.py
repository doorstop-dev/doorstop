# SPDX-License-Identifier: LGPL-3.0-only

"""Integration tests for the doorstop.cli package."""

import os
import shutil
import tempfile
import unittest
from unittest.mock import Mock, patch

from doorstop import common, settings
from doorstop.cli.main import main
from doorstop.cli.tests import (
    ENV,
    FILES,
    REASON,
    REQS,
    ROOT,
    TUTORIAL,
    SettingsTestCase,
)
from doorstop.core.builder import _clear_tree
from doorstop.core.document import Document

REQ_COUNT = 23
ALL_COUNT = 55


class TempTestCase(unittest.TestCase):
    """Base test case class with a temporary directory."""

    def setUp(self):
        self.cwd = os.getcwd()
        self.temp = tempfile.mkdtemp()

    def tearDown(self):
        os.chdir(self.cwd)
        if os.path.exists(self.temp):
            shutil.rmtree(self.temp)


class MockTestCase(TempTestCase):
    """Base test case class for a temporary mock working copy."""

    def setUp(self):
        super().setUp()
        os.chdir(self.temp)
        common.touch(".mockvcs")
        _clear_tree()


@unittest.skipUnless(os.getenv(ENV), REASON)
@patch("doorstop.settings.ADDREMOVE_FILES", False)
class TestMain(SettingsTestCase):
    """Integration tests for the 'doorstop' command."""

    def setUp(self):
        super().setUp()
        self.cwd = os.getcwd()
        self.temp = tempfile.mkdtemp()

    def tearDown(self):
        super().tearDown()
        os.chdir(self.cwd)
        shutil.rmtree(self.temp)

    def test_main(self):
        """Verify 'doorstop' can be called."""
        self.assertIs(None, main([]))

    def test_main_error(self):
        """Verify 'doorstop' returns an error in an empty directory."""
        os.chdir(self.temp)
        self.assertRaises(SystemExit, main, [])

    def test_main_custom_root(self):
        """Verify 'doorstop' can be provided a custom root path."""
        os.chdir(self.temp)
        self.assertIs(None, main(["--project", "."]))


@unittest.skipUnless(os.getenv(ENV), REASON)
class TestCreate(TempTestCase):
    """Integration tests for the 'doorstop create' command."""

    @patch("subprocess.call", Mock())
    def test_create(self):
        """Verify 'doorstop create' can be called."""
        self.assertIs(None, main(["create", "_TEMP", self.temp, "-p", "REQ"]))

    @patch("subprocess.call", Mock())
    def test_create_error_unknwon_parent(self):
        """Verify 'doorstop create' returns an error with an unknown parent."""
        self.assertRaises(
            SystemExit, main, ["create", "_TEMP", self.temp, "-p", "UNKNOWN"]
        )

    def test_create_error_reserved_prefix(self):
        """Verify 'doorstop create' returns an error with a reserved prefix."""
        self.assertRaises(SystemExit, main, ["create", "ALL", self.temp, "-p", "REQ"])

    def test_create_error_duplicate_name(self):
        """Verify 'doorstop create' returns an error with an already existing document name."""
        self.assertRaises(SystemExit, main, ["create", "TUT", self.temp, "-p", "REQ"])


@unittest.skipUnless(os.getenv(ENV), REASON)
class TestDelete(MockTestCase):
    """Integration tests for the 'doorstop delete' command."""

    def test_delete(self):
        """Verify 'doorstop delete' can be called."""
        main(["create", "PREFIX", "prefix"])
        self.assertIs(None, main(["delete", "PREFIX"]))

    def test_delete_error(self):
        """Verify 'doorstop delete' returns an error on unknown document."""
        self.assertRaises(SystemExit, main, ["delete", "UNKNOWN"])


def get_next_number():
    """Helper function to get the next document number."""
    last = None
    for last in sorted(os.listdir(TUTORIAL), reverse=True):
        if last.endswith(".yml"):
            break
    assert last, "Unable to find last item"
    number = int(last.replace("TUT", "").replace(".yml", "")) + 1
    return number


@unittest.skipUnless(os.getenv(ENV), REASON)
@patch("doorstop.settings.SERVER_HOST", None)
@patch("doorstop.settings.ADDREMOVE_FILES", False)
class TestAdd(unittest.TestCase):
    """Integration tests for the 'doorstop add' command."""

    @classmethod
    def setUpClass(cls):
        number = get_next_number()
        filename = "TUT{}.yml".format(str(number).zfill(3))
        cls.path = os.path.join(TUTORIAL, filename)

    def tearDown(self):
        common.delete(self.path)

    def test_add(self):
        """Verify 'doorstop add' can be called."""
        self.assertIs(None, main(["add", "TUT"]))
        self.assertTrue(os.path.isfile(self.path))

    def test_add_multiple(self):
        """Verify 'doorstop add' can be called with a given positive count"""
        number = get_next_number()
        numbers = (number, number + 1, number + 2)
        self.assertIs(None, main(["add", "TUT", "--count", "3"]))
        filenames = ("TUT{}.yml".format(str(x).zfill(3)) for x in numbers)
        paths = [os.path.join(TUTORIAL, f) for f in filenames]
        self.assertTrue(os.path.isfile(paths[0]))
        self.assertTrue(os.path.isfile(paths[1]))
        self.assertTrue(os.path.isfile(paths[2]))
        os.remove(paths[1])
        os.remove(paths[2])

    def test_add_multiple_non_positive(self):
        """Verify 'doorstop add' rejects non-positive integers for counts."""
        self.assertRaises(SystemExit, main, ["add", "TUT", "--count", "-1"])

    def test_add_specific_level(self):
        """Verify 'doorstop add' can be called with a specific level."""
        self.assertIs(None, main(["add", "TUT", "--level", "1.42"]))
        self.assertTrue(os.path.isfile(self.path))

    def test_add_error(self):
        """Verify 'doorstop add' returns an error with an unknown prefix."""
        self.assertRaises(SystemExit, main, ["add", "UNKNOWN"])


@unittest.skipUnless(os.getenv(ENV), REASON)
@patch("doorstop.settings.ADDREMOVE_FILES", False)
class TestAddServer(unittest.TestCase):
    """Integration tests for the 'doorstop add' command using a server."""

    @classmethod
    def setUpClass(cls):
        number = get_next_number()
        filename = "TUT{}.yml".format(str(number).zfill(3))
        cls.path = os.path.join(TUTORIAL, filename)

    def tearDown(self):
        common.delete(self.path)

    @patch("doorstop.settings.SERVER_HOST", "")
    def test_add(self):
        """Verify 'doorstop add' expects a server."""
        self.assertRaises(SystemExit, main, ["add", "TUT"])

    @patch("doorstop.settings.SERVER_HOST", None)
    def test_add_no_server(self):
        """Verify 'doorstop add' can be called if there is no server."""
        self.assertIs(None, main(["add", "TUT"]))

    @patch("doorstop.server.check", Mock())
    @patch("doorstop.core.document.Document.add_item")
    def test_add_custom_server(self, mock_add_item):
        """Verify 'doorstop add' can be called with a custom server."""
        self.assertIs(None, main(["add", "TUT", "--server", "1.2.3.4"]))
        mock_add_item.assert_called_once_with(defaults=None, level=None, name=None)

    def test_add_force(self):
        """Verify 'doorstop add' can be called with a missing server."""
        self.assertIs(None, main(["add", "TUT", "--force"]))


@unittest.skipUnless(os.getenv(ENV), REASON)
@patch("doorstop.settings.ADDREMOVE_FILES", False)
class TestRemove(unittest.TestCase):
    """Integration tests for the 'doorstop remove' command."""

    ITEM = os.path.join(TUTORIAL, "TUT003.yml")

    def setUp(self):
        self.backup = common.read_text(self.ITEM)

    def tearDown(self):
        common.write_text(self.backup, self.ITEM)

    def test_remove(self):
        """Verify 'doorstop remove' can be called."""
        self.assertIs(None, main(["remove", "tut3"]))
        self.assertFalse(os.path.exists(self.ITEM))

    def test_remove_error(self):
        """Verify 'doorstop remove' returns an error on unknown item UIDs."""
        self.assertRaises(SystemExit, main, ["remove", "tut9999"])


@unittest.skipUnless(os.getenv(ENV), REASON)
@patch("doorstop.settings.ADDREMOVE_FILES", False)
class TestReorder(unittest.TestCase):
    """Integration tests for the 'doorstop reorder' command."""

    @classmethod
    def setUpClass(cls):
        cls.prefix = "tut"
        cls.path = os.path.join("reqs", "tutorial", "index.yml")

    def tearDown(self):
        common.delete(self.path)

    @patch("doorstop.core.editor.launch")
    @patch("builtins.input", Mock(return_value="yes"))
    def test_reorder_document_yes(self, mock_launch):
        """Verify 'doorstop reorder' can be called with a document (yes)."""
        self.assertIs(None, main(["reorder", self.prefix]))
        mock_launch.assert_called_once_with(self.path, tool=os.getenv("EDITOR"))
        self.assertFalse(os.path.exists(self.path))

    @patch("doorstop.core.editor.launch")
    @patch("builtins.input", Mock(return_value="no"))
    def test_reorder_document_no(self, mock_launch):
        """Verify 'doorstop reorder' can be called with a document (no)."""
        self.assertIs(None, main(["reorder", self.prefix]))
        mock_launch.assert_called_once_with(self.path, tool=os.getenv("EDITOR"))
        self.assertFalse(os.path.exists(self.path))

    @patch("doorstop.core.editor.launch")
    def test_reorder_document_auto(self, mock_launch):
        """Verify 'doorstop reorder' can be called with a document (auto)."""
        self.assertIs(None, main(["reorder", self.prefix, "--auto"]))
        self.assertEqual(0, mock_launch.call_count)

    @patch("doorstop.core.document.Document._reorder_automatic")
    @patch("doorstop.core.editor.launch")
    @patch("builtins.input", Mock(return_value="no"))
    def test_reorder_document_manual(self, mock_launch, mock_reorder_auto):
        """Verify 'doorstop reorder' can be called with a document (manual)."""
        self.assertIs(None, main(["reorder", self.prefix, "--manual"]))
        mock_launch.assert_called_once_with(self.path, tool=os.getenv("EDITOR"))
        self.assertEqual(0, mock_reorder_auto.call_count)
        self.assertFalse(os.path.exists(self.path))

    @patch("builtins.input", Mock(return_value="yes"))
    def test_reorder_document_error(self):
        """Verify 'doorstop reorder' can handle invalid YAML."""

        def bad_yaml_edit(path, **_):
            """Simulate adding invalid YAML to the index."""
            common.write_text("%bad", path)

        with patch("doorstop.core.editor.launch", bad_yaml_edit):
            self.assertRaises(SystemExit, main, ["reorder", self.prefix])

        self.assertTrue(os.path.exists(self.path))

    def test_reorder_document_unknown(self):
        """Verify 'doorstop reorder' returns an error on an unknown prefix."""
        self.assertRaises(SystemExit, main, ["reorder", "FAKE"])

    def test_reorder_with_backslashes_in_text(self):
        """Verify 'doorstop reorder' can handle text with backslashes."""
        number = get_next_number()
        filename = "TUT{}.yml".format(str(number).zfill(3))
        path = os.path.join(TUTORIAL, filename)
        with open(path, "w") as f:
            f.write(
                """active: true\nderived: false\nheader: ''\nlevel: 2.4\nlinks: []\n"""
                """normative: true\nref: ''\nreviewed: null\ntext: |\n  Equation """
                """$Eqn = \\frac{a}{b} * \\sigma$"""
            )
            self.addCleanup(os.remove, path)
        self.assertIs(None, main(["reorder", self.prefix, "--auto"]))


@unittest.skipUnless(os.getenv(ENV), REASON)
@patch("doorstop.settings.SERVER_HOST", None)
@patch("doorstop.settings.ADDREMOVE_FILES", False)
class TestEdit(unittest.TestCase):
    """Integration tests for the 'doorstop edit' command."""

    @patch("subprocess.call", Mock())
    @patch("doorstop.core.editor.launch")
    def test_edit_item(self, mock_launch):
        """Verify 'doorstop edit' can be called with an item (all)."""
        self.assertIs(None, main(["edit", "tut2", "-T", "my_editor", "--all"]))
        path = os.path.join(TUTORIAL, "TUT002.yml")
        mock_launch.assert_called_once_with(os.path.normpath(path), tool="my_editor")

    def test_edit_item_unknown(self):
        """Verify 'doorstop edit' returns an error on an unknown item."""
        self.assertRaises(SystemExit, main, ["edit", "--item", "FAKE001"])

    @patch("time.time", Mock(return_value=123))
    @patch("doorstop.core.editor.launch")
    @patch("builtins.input", Mock(return_value="yes"))
    def test_edit_document_yes_yes(self, mock_launch):
        """Verify 'doorstop edit' can be called with a document (yes, yes)."""
        path = "TUT-123.yml"
        self.assertIs(None, main(["edit", "tut", "-T", "my_editor"]))
        mock_launch.assert_called_once_with(os.path.normpath(path), tool="my_editor")

    @patch("time.time", Mock(return_value=456))
    @patch("doorstop.core.editor.launch")
    @patch("builtins.input", Mock(return_value="no"))
    def test_edit_document_no_no(self, mock_launch):
        """Verify 'doorstop edit' can be called with a document (no, no)."""
        path = "TUT-456.yml"
        self.assertIs(None, main(["edit", "tut", "-T", "my_editor"]))
        common.delete(path)
        mock_launch.assert_called_once_with(os.path.normpath(path), tool="my_editor")

    @patch("time.time", Mock(return_value=789))
    @patch("doorstop.core.editor.launch")
    @patch("builtins.input", Mock(side_effect=["no", "yes"]))
    def test_edit_document_no_yes(self, mock_launch):
        """Verify 'doorstop edit' can be called with a document (no, yes)."""
        path = "TUT-789.yml"
        self.assertIs(None, main(["edit", "tut", "-T", "my_editor"]))
        mock_launch.assert_called_once_with(os.path.normpath(path), tool="my_editor")

    def test_edit_document_unknown(self):
        """Verify 'doorstop edit' returns an error on an unknown document."""
        self.assertRaises(SystemExit, main, ["edit", "--document", "FAKE"])

    def test_edit_error(self):
        """Verify 'doorstop edit' returns an error with an unknown UID."""
        self.assertRaises(SystemExit, main, ["edit", "req9999"])


@unittest.skipUnless(os.getenv(ENV), REASON)
@patch("doorstop.settings.ADDREMOVE_FILES", False)
class TestLink(unittest.TestCase):
    """Integration tests for the 'doorstop link' command."""

    ITEM = os.path.join(TUTORIAL, "TUT003.yml")

    def setUp(self):
        self.backup = common.read_text(self.ITEM)

    def tearDown(self):
        common.write_text(self.backup, self.ITEM)

    def test_link(self):
        """Verify 'doorstop link' can be called."""
        self.assertIs(None, main(["link", "tut3", "req2"]))

    def test_link_unknown_child(self):
        """Verify 'doorstop link' returns an error with an unknown child."""
        self.assertRaises(SystemExit, main, ["link", "unknown3", "req2"])
        self.assertRaises(SystemExit, main, ["link", "tut9999", "req2"])

    def test_link_unknown_parent(self):
        """Verify 'doorstop link' returns an error with an unknown parent."""
        self.assertRaises(SystemExit, main, ["link", "tut3", "unknown2"])
        self.assertRaises(SystemExit, main, ["link", "tut3", "req9999"])


@unittest.skipUnless(os.getenv(ENV), REASON)
@patch("doorstop.settings.ADDREMOVE_FILES", False)
class TestUnlink(unittest.TestCase):
    """Integration tests for the 'doorstop unlink' command."""

    ITEM = os.path.join(TUTORIAL, "TUT003.yml")

    def setUp(self):
        self.backup = common.read_text(self.ITEM)
        with patch("doorstop.settings.ADDREMOVE_FILES", False):
            main(["link", "tut3", "req2"])  # create a temporary link

    def tearDown(self):
        common.write_text(self.backup, self.ITEM)

    def test_unlink(self):
        """Verify 'doorstop unlink' can be called."""
        self.assertIs(None, main(["unlink", "tut3", "req2"]))

    def test_unlink_unknown_child(self):
        """Verify 'doorstop unlink' returns an error with an unknown child."""
        self.assertRaises(SystemExit, main, ["unlink", "unknown3", "req2"])
        self.assertRaises(SystemExit, main, ["link", "tut9999", "req2"])

    def test_unlink_unknown_parent(self):
        """Verify 'doorstop unlink' returns an error with an unknown parent."""
        self.assertRaises(SystemExit, main, ["unlink", "tut3", "unknown2"])
        self.assertRaises(SystemExit, main, ["unlink", "tut3", "req9999"])


@unittest.skipUnless(os.getenv(ENV), REASON)
class TestClear(unittest.TestCase):
    """Integration tests for the 'doorstop clear' command."""

    @patch("doorstop.core.item.Item.clear")
    def test_clear_item(self, mock_clear):
        """Verify 'doorstop clear' can be called with an item."""
        self.assertIs(None, main(["clear", "tut2"]))
        self.assertEqual(1, mock_clear.call_count)

    @patch("doorstop.core.item.Item.clear")
    def test_clear_item_parent(self, mock_clear):
        """Verify 'doorstop clear' can be called with an item and parent."""
        self.assertIs(None, main(["clear", "tut2", "req2"]))
        self.assertEqual(1, mock_clear.call_count)

    def test_clear_item_unknown(self):
        """Verify 'doorstop clear' returns an error on an unknown item."""
        self.assertRaises(SystemExit, main, ["clear", "--item", "FAKE001"])

    @patch("doorstop.core.item.Item.clear")
    def test_clear_document(self, mock_clear):
        """Verify 'doorstop clear' can be called with a document"""
        self.assertIs(None, main(["clear", "tut"]))
        self.assertEqual(REQ_COUNT, mock_clear.call_count)

    def test_clear_document_unknown(self):
        """Verify 'doorstop clear' returns an error on an unknown document."""
        self.assertRaises(SystemExit, main, ["clear", "--document", "FAKE"])

    @patch("doorstop.core.item.Item.clear")
    def test_clear_tree(self, mock_clear):
        """Verify 'doorstop clear' can be called with a tree"""
        self.assertIs(None, main(["clear", "all"]))
        self.assertEqual(ALL_COUNT, mock_clear.call_count)

    def test_clear_tree_item(self):
        """Verify 'doorstop clear' returns an error with tree and item."""
        self.assertRaises(SystemExit, main, ["clear", "--item", "all"])

    def test_clear_tree_document(self):
        """Verify 'doorstop clear' returns an error with tree and document."""
        self.assertRaises(SystemExit, main, ["clear", "--document", "all"])

    def test_clear_error(self):
        """Verify 'doorstop clear' returns an error with an unknown UID."""
        self.assertRaises(SystemExit, main, ["clear", "req9999"])


@unittest.skipUnless(os.getenv(ENV), REASON)
class TestReview(unittest.TestCase):
    """Integration tests for the 'doorstop review' command."""

    @patch("doorstop.core.item.Item.review")
    def test_review_item(self, mock_review):
        """Verify 'doorstop review' can be called with an item."""
        self.assertIs(None, main(["review", "tut2"]))
        self.assertEqual(1, mock_review.call_count)

    def test_review_item_unknown(self):
        """Verify 'doorstop review' returns an error on an unknown item."""
        self.assertRaises(SystemExit, main, ["review", "--item", "FAKE001"])

    @patch("doorstop.core.item.Item.review")
    def test_review_document(self, mock_review):
        """Verify 'doorstop review' can be called with a document"""
        self.assertIs(None, main(["review", "tut"]))
        self.assertEqual(REQ_COUNT, mock_review.call_count)

    def test_review_document_unknown(self):
        """Verify 'doorstop review' returns an error on an unknown document."""
        self.assertRaises(SystemExit, main, ["review", "--document", "FAKE"])

    @patch("doorstop.core.item.Item.review")
    def test_review_tree(self, mock_review):
        """Verify 'doorstop review' can be called with a tree"""
        self.assertIs(None, main(["review", "all"]))
        self.assertEqual(ALL_COUNT, mock_review.call_count)

    def test_review_tree_item(self):
        """Verify 'doorstop review' returns an error with tree and item."""
        self.assertRaises(SystemExit, main, ["review", "--item", "all"])

    def test_review_tree_document(self):
        """Verify 'doorstop review' returns an error with tree and document."""
        self.assertRaises(SystemExit, main, ["review", "--document", "all"])

    def test_review_error(self):
        """Verify 'doorstop review' returns an error with an unknown UID."""
        self.assertRaises(SystemExit, main, ["review", "req9999"])


@unittest.skipUnless(os.getenv(ENV), REASON)
@patch("doorstop.settings.SERVER_HOST", None)
@patch("doorstop.settings.ADDREMOVE_FILES", False)
class TestImport(unittest.TestCase):
    """Integration tests for the 'doorstop import' command."""

    def tearDown(self):
        common.delete(os.path.join(ROOT, "tmp"))
        common.delete(os.path.join(REQS, "REQ099.yml"))

    def test_import_document(self):
        """Verify 'doorstop import' can import a document."""
        self.assertRaises(SystemExit, main, ["import", "--document", "TMP", "tmp"])

    def test_import_document_with_parent(self):
        """Verify 'doorstop import' can import a document with a parent."""
        self.assertIs(
            None, main(["import", "--document", "TMP", "tmp", "--parent", "REQ"])
        )

    def test_import_item(self):
        """Verify 'doorstop import' can import an item.."""
        self.assertIs(None, main(["import", "--item", "REQ", "REQ099"]))

    def test_import_item_with_attrs(self):
        """Verify 'doorstop import' can import an item with attributes."""
        self.assertIs(
            None,
            main(
                [
                    "import",
                    "--item",
                    "REQ",
                    "REQ099",
                    "--attrs",
                    "{'text': 'The item text.'}",
                ]
            ),
        )

    def test_import_error(self):
        """Verify 'doorstop import' requires a document or item."""
        self.assertRaises(SystemExit, main, ["import", "--attr", "{}"])


@unittest.skipUnless(os.getenv(ENV), REASON)
@patch("doorstop.settings.SERVER_HOST", None)
class TestImportFile(MockTestCase):
    """Integration tests for the 'doorstop import' command."""

    def test_import_file_missing_prefix(self):
        """Verify 'doorstop import' returns an error with a missing prefix."""
        path = os.path.join(FILES, "exported.xlsx")
        self.assertRaises(SystemExit, main, ["import", path])

    def test_import_file_extra_flags(self):
        """Verify 'doorstop import' returns an error with extra flags."""
        path = os.path.join(FILES, "exported.xlsx")
        self.assertRaises(SystemExit, main, ["import", path, "PREFIX", "-d", "_", "_"])
        self.assertRaises(SystemExit, main, ["import", path, "PREFIX", "-i", "_", "_"])

    def test_import_file_to_document_unknown(self):
        """Verify 'doorstop import' returns an error for unknown documents."""
        path = os.path.join(FILES, "exported.xlsx")
        self.assertRaises(SystemExit, main, ["import", path, "PREFIX"])

    def test_import_file_with_map(self):
        """Verify 'doorstop import' can import a file using a custom map."""
        path = os.path.join(FILES, "exported-map.csv")
        dirpath = os.path.join(self.temp, "imported", "prefix")
        main(["create", "PREFIX", dirpath])
        # Act
        self.assertIs(
            None, main(["import", path, "PREFIX", "--map", "{'mylevel': 'level'}"])
        )
        # Assert
        path = os.path.join(dirpath, "REQ001.yml")
        self.assertTrue(os.path.isfile(path))
        text = common.read_text(path)
        self.assertIn("\nlevel: 1.2.3", text)

    def test_import_file_with_map_invalid(self):
        """Verify 'doorstop import' returns an error with an invalid map."""
        path = os.path.join(FILES, "exported.csv")
        self.assertRaises(SystemExit, main, ["import", path, "PREFIX", "--map", "{'my"])

    def test_import_csv_to_document_existing(self):
        """Verify 'doorstop import' can import CSV to an existing document."""
        path = os.path.join(FILES, "exported.csv")
        dirpath = os.path.join(self.temp, "imported", "prefix")
        main(["create", "PREFIX", dirpath])
        # Act
        self.assertIs(None, main(["import", path, "PREFIX"]))
        # Assert
        path = os.path.join(dirpath, "REQ001.yml")
        self.assertTrue(os.path.isfile(path))

    def test_import_tsv_to_document_existing(self):
        """Verify 'doorstop import' can import TSV to an existing document."""
        path = os.path.join(FILES, "exported.tsv")
        dirpath = os.path.join(self.temp, "imported", "prefix")
        main(["create", "PREFIX", dirpath])
        # Act
        self.assertIs(None, main(["import", path, "PREFIX"]))
        # Assert
        path = os.path.join(dirpath, "REQ001.yml")
        self.assertTrue(os.path.isfile(path))

    def test_import_xlsx_to_document_existing(self):
        """Verify 'doorstop import' can import XLSX to an existing document."""
        path = os.path.join(FILES, "exported.xlsx")
        dirpath = os.path.join(self.temp, "imported", "prefix")
        main(["create", "PREFIX", dirpath])
        # Act
        self.assertIs(None, main(["import", path, "PREFIX"]))
        # Assert
        path = os.path.join(dirpath, "REQ001.yml")
        self.assertTrue(os.path.isfile(path))


@unittest.skipUnless(os.getenv(ENV), REASON)
@patch("doorstop.settings.ADDREMOVE_FILES", False)
class TestImportServer(unittest.TestCase):
    """Integration tests for the 'doorstop import' command using a server."""

    def tearDown(self):
        common.delete(os.path.join(ROOT, "tmp"))
        common.delete(os.path.join(REQS, "REQ099.yml"))

    def test_import_item_force(self):
        """Verify 'doorstop import' can import an item without a server."""
        self.assertIs(None, main(["import", "--item", "REQ", "REQ099", "--force"]))


@unittest.skipUnless(os.getenv(ENV), REASON)
class TestExport(TempTestCase):
    """Integration tests for the 'doorstop export' command."""

    def test_export_document_error_unknown(self):
        """Verify 'doorstop export' returns an error for an unknown format."""
        self.assertRaises(SystemExit, main, ["export", "req", "req.fake"])

    def test_export_document_error_directory(self):
        """Verify 'doorstop publish' returns an error with a directory."""
        self.assertRaises(SystemExit, main, ["export", "req", self.temp])

    def test_export_document_error_no_extension(self):
        """Verify 'doorstop publish' returns an error with no extension."""
        path = os.path.join(self.temp, "req")
        self.assertRaises(SystemExit, main, ["export", "req", path])

    def test_export_document_stdout(self):
        """Verify 'doorstop export' can create output."""
        self.assertIs(None, main(["export", "tut"]))

    def test_export_document_stdout_width(self):
        """Verify 'doorstop export' can create output."""
        self.assertIs(None, main(["export", "tut", "--width", "72"]))

    def test_export_document_yaml(self):
        """Verify 'doorstop export' can create a YAML file."""
        path = os.path.join(self.temp, "tut.yml")
        self.assertIs(None, main(["export", "tut", path]))
        self.assertTrue(os.path.isfile(path))

    def test_export_document_xlsx(self):
        """Verify 'doorstop export' can create an XLSX file."""
        path = os.path.join(self.temp, "tut.xlsx")
        self.assertIs(None, main(["export", "tut", path]))
        self.assertTrue(os.path.isfile(path))

    @patch("openpyxl.Workbook.save", Mock(side_effect=PermissionError))
    def test_export_document_xlsx_error(self):
        """Verify 'doorstop export' can handle IO errors."""
        path = os.path.join(self.temp, "tut.xlsx")
        self.assertRaises(SystemExit, main, ["export", "tut", path])
        self.assertFalse(os.path.isfile(path))

    def test_export_tree_xlsx(self):
        """Verify 'doorstop export' can create an XLSX directory."""
        path = os.path.join(self.temp, "all")
        self.assertIs(None, main(["export", "all", path, "--xlsx"]))
        self.assertTrue(os.path.isdir(path))

    def test_export_tree_no_path(self):
        """Verify 'doorstop export' returns an error with no path."""
        self.assertRaises(SystemExit, main, ["export", "all"])


@unittest.skipUnless(os.getenv(ENV), REASON)
class TestPublish(TempTestCase):
    """Integration tests for the 'doorstop publish' command."""

    def setUp(self):
        super().setUp()
        self.backup = (settings.PUBLISH_CHILD_LINKS, settings.PUBLISH_BODY_LEVELS)

    def tearDown(self):
        super().tearDown()
        (settings.PUBLISH_CHILD_LINKS, settings.PUBLISH_BODY_LEVELS) = self.backup

    def test_publish_unknown(self):
        """Verify 'doorstop publish' returns an error for an unknown format."""
        self.assertRaises(SystemExit, main, ["publish", "req", "req.fake"])

    def test_publish_document(self):
        """Verify 'doorstop publish' can create output."""
        self.assertIs(None, main(["publish", "tut"]))
        self.assertTrue(settings.PUBLISH_CHILD_LINKS)

    def test_publish_document_with_child_links(self):
        """Verify 'doorstop publish' can create output with child links."""
        self.assertIs(None, main(["publish", "tut"]))
        self.assertTrue(settings.PUBLISH_CHILD_LINKS)

    def test_publish_document_without_child_links(self):
        """Verify 'doorstop publish' can create output without child links."""
        self.assertIs(None, main(["publish", "tut", "--no-child-links"]))
        self.assertFalse(settings.PUBLISH_CHILD_LINKS)

    def test_publish_document_no_body_levels(self):
        """Verify 'doorstop publish' can create output without body levels."""
        self.assertIs(None, main(["publish", "tut", "--no-levels=body"]))
        self.assertFalse(settings.PUBLISH_BODY_LEVELS)

    def test_publish_document_no_body_or_heading_levels(self):
        """Verify 'doorstop publish' can create output without heading or body levels."""
        self.assertIs(None, main(["publish", "tut", "--no-levels=all"]))
        self.assertFalse(settings.PUBLISH_BODY_LEVELS)
        self.assertFalse(settings.PUBLISH_HEADING_LEVELS)

    def test_publish_document_error_empty(self):
        """Verify 'doorstop publish' returns an error in an empty folder."""
        os.chdir(self.temp)
        self.assertRaises(SystemExit, main, ["publish", "req"])

    def test_publish_document_error_directory(self):
        """Verify 'doorstop publish' returns an error with a directory."""
        self.assertRaises(SystemExit, main, ["publish", "req", self.temp])

    def test_publish_document_error_no_extension(self):
        """Verify 'doorstop publish' returns an error with no extension."""
        path = os.path.join(self.temp, "req")
        self.assertRaises(SystemExit, main, ["publish", "req", path])

    def test_publish_document_text(self):
        """Verify 'doorstop publish' can create text output."""
        self.assertIs(None, main(["publish", "tut", "--width", "75"]))

    def test_publish_document_text_file(self):
        """Verify 'doorstop publish' can create a text file."""
        path = os.path.join(self.temp, "req.txt")
        self.assertIs(None, main(["publish", "req", path]))
        self.assertTrue(os.path.isfile(path))

    def test_publish_document_markdown(self):
        """Verify 'doorstop publish' can create Markdown output."""
        self.assertIs(None, main(["publish", "req", "--markdown"]))

    def test_publish_document_markdown_file(self):
        """Verify 'doorstop publish' can create a Markdown file."""
        path = os.path.join(self.temp, "req.md")
        self.assertIs(None, main(["publish", "req", path]))
        self.assertTrue(os.path.isfile(path))

    def test_publish_document_html_file(self):
        """Verify 'doorstop publish' can create an HTML file."""
        path = os.path.join(self.temp, "req.html")
        self.assertIs(None, main(["publish", "req", path]))
        filePath = os.path.join(self.temp, "documents", "req.html")
        self.assertTrue(os.path.isfile(filePath))

    def test_publish_tree_html(self):
        """Verify 'doorstop publish' can create an HTML directory."""
        path = os.path.join(self.temp, "all")
        self.assertIs(None, main(["publish", "all", path]))
        self.assertTrue(os.path.isdir(path))
        self.assertTrue(os.path.isfile(os.path.join(path, "index.html")))

    def test_publish_tree_text(self):
        """Verify 'doorstop publish' can create a text directory."""
        path = os.path.join(self.temp, "all")
        self.assertIs(None, main(["publish", "all", path, "--text"]))
        self.assertTrue(os.path.isdir(path))
        self.assertFalse(os.path.isfile(os.path.join(path, "index.html")))

    def test_publish_tree_no_path(self):
        """Verify 'doorstop publish' returns an error with no path."""
        self.assertRaises(SystemExit, main, ["publish", "all"])


class TestPublishCommand(TempTestCase):
    """Tests 'doorstop publish' options toc and template"""

    @patch("doorstop.core.publisher.publish")
    def test_publish_document_template(self, mock_publish):
        """Verify 'doorstop publish' is called with template."""
        path = os.path.join(self.temp, "req.html")
        self.assertIs(
            None, main(["publish", "--template", "my_template.html", "req", path])
        )
        mock_publish.assert_called_once_with(
            Document(os.path.abspath(REQS)), path, ".html", template="my_template.html"
        )

    @patch("doorstop.core.publisher.publish_lines")
    def test_publish_document_to_stdout(self, mock_publish_lines):
        """Verify 'doorstop publish_lines' is called when no output path specified"""
        self.assertIs(None, main(["publish", "req"]))
        mock_publish_lines.assert_called_once_with(
            Document(os.path.abspath(REQS)), ".txt"
        )


@patch("doorstop.cli.commands.run", Mock(return_value=True))
class TestLogging(unittest.TestCase):
    """Integration tests for the Doorstop CLI logging."""

    def test_verbose_0(self):
        """Verify verbose level 0 can be set."""
        self.assertIs(None, main([]))

    def test_verbose_1(self):
        """Verify verbose level 1 can be set."""
        self.assertIs(None, main(["-v"]))

    def test_verbose_2(self):
        """Verify verbose level 2 can be set."""
        self.assertIs(None, main(["-vv"]))

    def test_verbose_3(self):
        """Verify verbose level 3 can be set."""
        self.assertIs(None, main(["-vvv"]))

    def test_verbose_4(self):
        """Verify verbose level 4 can be set."""
        self.assertIs(None, main(["-vvvv"]))

    def test_verbose_5(self):
        """Verify verbose level 5 cannot be set."""
        self.assertIs(None, main(["-vvvvv"]))
        self.assertEqual(4, common.verbosity)

    def test_verbose_quiet(self):
        """Verify verbose level -1 can be set."""
        self.assertIs(None, main(["-q"]))
        self.assertEqual(-1, common.verbosity)
