# SPDX-License-Identifier: LGPL-3.0-only

"""Unit tests for the Doorstop GUI application."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from doorstop.gui.application import Application


def application_for(path: Path) -> Application:
    """Create the portion of an application needed for file-state tests."""
    application = object.__new__(Application)
    application.item = SimpleNamespace(path=str(path))
    application.item_file_fingerprint = None
    return application


def test_item_file_fingerprint_changes_with_content(tmp_path):
    """Verify item fingerprints reflect the complete on-disk content."""
    path = tmp_path / "REQ001.yml"
    path.write_text("text: original\n", encoding="utf-8")
    application = application_for(path)

    original = application._item_file_fingerprint()
    path.write_text("text: external update\n", encoding="utf-8")

    assert original != application._item_file_fingerprint()


def test_item_changed_on_disk(tmp_path):
    """Verify an external item edit is detected after display."""
    path = tmp_path / "REQ001.yml"
    path.write_text("text: original\n", encoding="utf-8")
    application = application_for(path)
    application.item_file_fingerprint = application._item_file_fingerprint()

    assert not application._item_changed_on_disk()

    path.write_text("text: external update\n", encoding="utf-8")

    assert application._item_changed_on_disk()


def test_missing_item_file_has_no_fingerprint(tmp_path):
    """Verify a missing item file does not raise an exception."""
    application = application_for(tmp_path / "REQ001.yml")

    assert application._item_file_fingerprint() is None


@patch("doorstop.gui.application.messagebox.showwarning")
def test_external_change_blocks_save(showwarning, tmp_path):
    """Verify a stale GUI item cannot overwrite an external edit."""
    path = tmp_path / "REQ001.yml"
    path.write_text("text: original\n", encoding="utf-8")
    application = application_for(path)
    application.ignore = False
    application.item = Mock(path=str(path))
    application.item_file_fingerprint = b"stale"
    application.display_item = Mock()

    application.update_item()

    showwarning.assert_called_once()
    application.item.load.assert_called_once_with(reload=True)
    application.item.save.assert_not_called()
    application.display_item.assert_called_once_with()
