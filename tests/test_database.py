"""Tests for ``meowdesk.core.database.FileDatabase``."""

import json
import os

import pytest

from meowdesk.core.database import FileDatabase
from meowdesk.core.types import FileRecord


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "filedb.json"


def _make_record(name, category="文档", action="archive", ts="2026-01-01T00:00:00"):
    return FileRecord(
        original_name=name,
        original_path=f"/tmp/{name}",
        category=category,
        action=action,
        destination=f"/dst/{name}",
        file_size=123,
        md5="deadbeef",
        timestamp=ts,
        date="2026-01-01",
        time="00:00:00",
    )


def test_load_returns_empty_when_missing(db_path):
    db = FileDatabase(str(db_path))
    assert db.records == []
    assert db.get_stats()["total_files"] == 0


def test_add_record_persists_to_disk(db_path):
    db = FileDatabase(str(db_path))
    assert db.add_record(_make_record("a.txt")) is True

    assert os.path.exists(db_path)
    raw = json.loads(db_path.read_text(encoding="utf-8"))
    assert len(raw) == 1
    assert raw[0]["original_name"] == "a.txt"


def test_add_record_dict_accepts_plain_dict(db_path):
    db = FileDatabase(str(db_path))
    ok = db.add_record_dict({
        "original_name": "dict.txt",
        "original_path": "/tmp/dict.txt",
        "category": "文档",
        "action": "archive",
    })
    assert ok is True
    assert len(db.records) == 1
    assert db.records[0].timestamp  # auto-filled


def test_search_filters_by_keyword_category_date(db_path):
    db = FileDatabase(str(db_path))
    db.add_record(_make_record("report.pdf", category="文档", ts="2026-01-15T10:00:00"))
    db.add_record(_make_record("photo.png", category="图片", ts="2026-02-15T10:00:00"))
    db.add_record(_make_record("notes.md", category="文档", ts="2026-03-15T10:00:00"))

    # keyword
    matches = db.search(keyword="report")
    assert [r.original_name for r in matches] == ["report.pdf"]

    # category
    docs = db.search(category="文档")
    assert {r.original_name for r in docs} == {"report.pdf", "notes.md"}

    # start date
    recent = db.search(start_date="2026-02-01")
    assert {r.original_name for r in recent} == {"photo.png", "notes.md"}

    # end date
    old = db.search(end_date="2026-02-01")
    assert [r.original_name for r in old] == ["report.pdf"]

    # combined
    both = db.search(category="文档", start_date="2026-03-01")
    assert [r.original_name for r in both] == ["notes.md"]


def test_get_stats_sums_size_and_groups_by_category(db_path):
    db = FileDatabase(str(db_path))
    db.add_record(_make_record("a.pdf", category="文档"))
    db.add_record(_make_record("b.png", category="图片"))
    db.add_record(_make_record("c.png", category="图片"))

    stats = db.get_stats()
    assert stats["total_files"] == 3
    assert stats["total_size"] == 123 * 3
    assert stats["categories"]["文档"]["count"] == 1
    assert stats["categories"]["图片"]["count"] == 2
    assert stats["categories"]["文档"]["size"] == 123


def test_get_recent_returns_latest_first(db_path):
    db = FileDatabase(str(db_path))
    db.add_record(_make_record("a.txt", ts="2026-01-01T00:00:00"))
    db.add_record(_make_record("b.txt", ts="2026-01-05T00:00:00"))
    db.add_record(_make_record("c.txt", ts="2026-01-03T00:00:00"))

    recent = db.get_recent(limit=2)
    assert [r.original_name for r in recent] == ["b.txt", "c.txt"]


def test_load_handles_corrupt_json(db_path, caplog):
    db_path.write_text("{not valid", encoding="utf-8")
    import logging
    with caplog.at_level(logging.WARNING, logger="meowdesk.core.database"):
        db = FileDatabase(str(db_path))
    assert db.records == []
    assert "database" in caplog.text.lower() or "unreadable" in caplog.text.lower()
