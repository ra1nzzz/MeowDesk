"""Tests for ``meowdesk.core.file_handler.FileHandler``."""

import os
from datetime import datetime

import pytest

from meowdesk.core.file_handler import FileHandler


@pytest.fixture
def handler(tmp_path):
    archive = tmp_path / "archive"
    temp = tmp_path / "temp"
    return FileHandler(str(archive), str(temp))


def test_creates_archive_and_temp_dirs(handler):
    assert os.path.isdir(handler.archive_dir)
    assert os.path.isdir(handler.temp_dir)


def test_archive_file_moves_into_month_folder(handler, tmp_path):
    src = tmp_path / "src" / "note.txt"
    src.parent.mkdir()
    src.write_text("hello", encoding="utf-8")

    result = handler.archive_file(str(src), "文档")

    assert result.success is True
    assert result.destination.endswith(f"文档{os.sep}{datetime.now():%Y-%m}{os.sep}note.txt")
    assert os.path.exists(result.destination)
    assert not src.exists()


def test_archive_file_renames_duplicates(handler, tmp_path):
    base = tmp_path / "dup.txt"
    base.write_text("first", encoding="utf-8")

    first = handler.archive_file(str(base), "文档")
    assert first.success is True

    second_src = tmp_path / "dup.txt"
    second_src.write_text("second", encoding="utf-8")
    second = handler.archive_file(str(second_src), "文档")
    assert second.success is True
    assert second.destination != first.destination
    assert os.path.basename(second.destination) == "dup_1.txt"


def test_archive_file_reports_failure_on_missing_source(handler):
    result = handler.archive_file("/no/such/path/missing.txt", "文档")
    assert result.success is False
    assert result.error


def test_archive_failure_does_not_leave_empty_category_dir(handler, tmp_path):
    """A failed archive should not leave an empty
    ``<archive>/<category>/<YYYY-MM>/`` behind."""

    src = tmp_path / "src.txt"
    src.write_text("data", encoding="utf-8")

    result = handler.archive_file(str(src), "文档")
    assert result.success is True
    # The successful case *should* create the directory
    assert os.path.isdir(os.path.join(handler.archive_dir, "文档"))

    # Now simulate a failure: ask the handler to archive a missing
    # file. The category directory was created on the previous call
    # and is no longer empty, so cleanup must not touch it.
    fail_result = handler.archive_file("/no/such/missing.txt", "文档")
    assert fail_result.success is False
    assert os.path.isdir(os.path.join(handler.archive_dir, "文档"))


def test_archive_failure_cleans_up_fresh_category_dir(handler, tmp_path):
    """If the move fails and the category dir is otherwise empty,
    it should be removed (best-effort cleanup)."""

    src = tmp_path / "src.txt"
    src.write_text("data", encoding="utf-8")

    # Pre-condition: no 文档/ directory yet
    assert not os.path.exists(os.path.join(handler.archive_dir, "文档"))

    fail_result = handler.archive_file("/no/such/missing.txt", "文档")
    assert fail_result.success is False
    # Best-effort: we don't require this to pass if the OS rmdir is
    # restricted, but on tmp_path it should succeed.
    assert not os.path.exists(os.path.join(handler.archive_dir, "文档"))


def test_calculate_md5_matches_known_value(handler, tmp_path):
    f = tmp_path / "checksum.txt"
    f.write_text("abc", encoding="utf-8")
    import hashlib
    expected = hashlib.md5(b"abc").hexdigest()
    assert FileHandler.calculate_md5(str(f)) == expected


def test_calculate_md5_returns_empty_for_missing_file(handler):
    assert FileHandler.calculate_md5("/no/such/file") == ""


def test_get_file_size_returns_zero_for_missing(handler):
    assert FileHandler.get_file_size("/no/such/file") == 0


def test_create_record_populates_metadata(handler, tmp_path):
    f = tmp_path / "meta.txt"
    f.write_text("hello", encoding="utf-8")
    record = handler.create_record(str(f), "文档", "archive", str(f))
    assert record.original_name == "meta.txt"
    assert record.category == "文档"
    assert record.action == "archive"
    assert record.file_size == 5
    assert record.md5
    assert record.timestamp
    assert record.date == datetime.now().strftime("%Y-%m-%d")
