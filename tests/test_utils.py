"""Tests for ``meowdesk.utils`` helpers."""

import json

import pytest

from meowdesk.utils.io import (
    atomic_write_json,
    atomic_write_text,
    load_json_with_backup,
)


def test_atomic_write_text_creates_target(tmp_path):
    target = tmp_path / "out.txt"
    atomic_write_text(str(target), "hello")
    assert target.read_text(encoding="utf-8") == "hello"


def test_atomic_write_text_overwrites_existing(tmp_path):
    target = tmp_path / "out.txt"
    target.write_text("old", encoding="utf-8")
    atomic_write_text(str(target), "new")
    assert target.read_text(encoding="utf-8") == "new"


def test_atomic_write_text_leaves_no_temp_files_on_success(tmp_path):
    target = tmp_path / "out.txt"
    atomic_write_text(str(target), "x")
    # No leftover temp siblings
    siblings = [p.name for p in tmp_path.iterdir()]
    assert siblings == ["out.txt"]


def test_atomic_write_text_cleans_up_on_failure(tmp_path, monkeypatch):
    target = tmp_path / "out.txt"

    def boom(*_args, **_kwargs):
        raise RuntimeError("simulated disk error")

    monkeypatch.setattr("os.replace", boom)
    with pytest.raises(RuntimeError):
        atomic_write_text(str(target), "x")

    # Primary file shouldn't be created, temp file should be cleaned up
    siblings = list(tmp_path.iterdir())
    assert siblings == []


def test_atomic_write_json_serializes(tmp_path):
    target = tmp_path / "data.json"
    atomic_write_json(str(target), {"a": 1, "b": [1, 2, 3]})
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data == {"a": 1, "b": [1, 2, 3]}


def test_load_json_returns_none_when_missing(tmp_path):
    assert load_json_with_backup(str(tmp_path / "missing.json")) is None


def test_load_json_reads_valid_file(tmp_path):
    target = tmp_path / "ok.json"
    target.write_text(json.dumps({"x": 1}), encoding="utf-8")
    assert load_json_with_backup(str(target)) == {"x": 1}


def test_load_json_falls_back_to_backup_when_primary_corrupt(tmp_path):
    primary = tmp_path / "data.json"
    backup = tmp_path / "data.json.bak"
    primary.write_text("{not valid", encoding="utf-8")
    backup.write_text(json.dumps({"from": "backup"}), encoding="utf-8")

    result = load_json_with_backup(str(primary))

    assert result == {"from": "backup"}
    # Corrupt primary is rotated aside as the new backup
    assert not primary.exists()
    assert backup.exists()
    assert backup.read_text(encoding="utf-8") == "{not valid"


def test_load_json_returns_none_when_everything_corrupt(tmp_path):
    primary = tmp_path / "data.json"
    backup = tmp_path / "data.json.bak"
    primary.write_text("garbage", encoding="utf-8")
    backup.write_text("also garbage", encoding="utf-8")

    assert load_json_with_backup(str(primary)) is None


def test_load_json_uses_older_backup_after_rotation(tmp_path):
    primary = tmp_path / "data.json"
    backup0 = tmp_path / "data.json.bak"
    backup1 = tmp_path / "data.json.bak.1"
    primary.write_text("corrupt", encoding="utf-8")
    backup0.write_text("corrupt", encoding="utf-8")
    backup1.write_text(json.dumps({"v": 1}), encoding="utf-8")

    assert load_json_with_backup(str(primary)) == {"v": 1}
