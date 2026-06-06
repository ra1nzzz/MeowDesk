"""Tests for ``meowdesk.index_gen``."""

import json
import os

from meowdesk.index_gen import (
    classify_filename,
    format_size,
    generate_html,
    load_records_from_db,
    write_html_index,
)


def test_classify_filename_by_extension():
    assert classify_filename("report.pdf") == "文档"
    assert classify_filename("video.mp4") == "视频"
    assert classify_filename("song.mp3") == "音频"
    assert classify_filename("archive.zip") == "压缩包"
    assert classify_filename("code.py") == "代码"
    assert classify_filename("unknown.xyz") == "其他"


def test_classify_filename_screenshot_detection():
    assert classify_filename("2026_06_03_10_00_00.png") == "截图"
    assert classify_filename("Screenshot_2026.png") == "截图"
    assert classify_filename("微信截图_20260603.png") == "截图"
    assert classify_filename("Snipaste_2026-06-03.png") == "截图"
    assert classify_filename("屏幕截图 2026-06-03.png") == "截图"
    assert classify_filename("clip_image.png") == "截图"
    assert classify_filename("capture.png") == "截图"
    assert classify_filename("图片.png") == "图片"


def test_format_size():
    assert format_size(100) == "100 B"
    assert format_size(1025) == "1.0 KB"
    assert format_size(2048) == "2.0 KB"
    assert format_size(1048577) == "1.0 MB"
    assert format_size(1073741825) == "1.0 GB"


def test_generate_html_returns_valid_string():
    records = [
        {
            "category": "文档",
            "original_name": "test.pdf",
            "date": "2026-06-03",
            "action": "archive",
            "destination": "/archive/文档/2026-06/test.pdf",
            "file_size": 1234,
            "timestamp": "2026-06-03T10:00:00",
        }
    ]
    html = generate_html(records, "/data", "/data")
    assert "<!DOCTYPE html>" in html
    assert 'data-cat="文档"' in html
    assert "妙喵桌宠" in html


def test_generate_html_empty_records():
    html = generate_html([], "/data", "/data")
    assert "<!DOCTYPE html>" in html
    assert "妙喵桌宠 MeowDesk · 共" + "0" + "个文件" in html


def test_generate_html_recycle_badge():
    records = [
        {
            "category": "截图",
            "original_name": "shot.png",
            "date": "2026-06-03",
            "action": "recycle",
            "destination": "(已回收)",
            "file_size": 500,
            "timestamp": "2026-06-03T10:00:00",
        }
    ]
    html = generate_html(records, "/data", "/data")
    assert 'class="badge badge-recycle"' in html
    assert "已回收" in html


def test_write_html_index_creates_file(tmp_path):
    archive = tmp_path / "archive"
    archive.mkdir()
    records = [
        {
            "category": "图片",
            "original_name": "pic.jpg",
            "date": "2026-06-03",
            "action": "archive",
            "destination": str(archive / "pic.jpg"),
            "file_size": 100,
            "timestamp": "2026-06-03T10:00:00",
        }
    ]
    out = write_html_index(records, str(archive), str(archive))
    assert out is not None
    assert os.path.exists(out)
    assert os.path.basename(out) == "index.html"


def test_load_records_from_db_missing_file(tmp_path):
    missing = tmp_path / "missing.json"
    records = load_records_from_db(str(missing))
    assert records == []


def test_load_records_from_db_valid_json(tmp_path):
    db = tmp_path / "db.json"
    data = [{"original_name": "a.txt", "category": "文档"}]
    db.write_text(json.dumps(data), encoding="utf-8")
    records = load_records_from_db(str(db))
    assert len(records) == 1
    assert records[0]["original_name"] == "a.txt"


def test_load_records_from_db_corrupt_json(tmp_path, caplog):
    import logging
    db = tmp_path / "broken.json"
    db.write_text("{not valid", encoding="utf-8")
    with caplog.at_level(logging.WARNING, logger="meowdesk.index_gen"):
        records = load_records_from_db(str(db))
    assert records == []
    assert "could not load DB" in caplog.text
