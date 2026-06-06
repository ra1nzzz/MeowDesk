"""Tests for ``meowdesk.core.config.ConfigManager``."""

import json
import os

import pytest

from meowdesk.core.config import ConfigManager
from meowdesk.core.types import AppConfig, FileAction


@pytest.fixture
def config_path(tmp_path):
    return tmp_path / "config.json"


def test_creates_default_config_when_missing(config_path):
    config = ConfigManager(str(config_path))

    assert os.path.exists(config_path)
    defaults = AppConfig.get_default()
    assert config.archive_dir == defaults.archive_dir
    assert config.temp_dir == defaults.temp_dir
    assert config.config.window_opacity == defaults.window_opacity
    assert "文档" in config.categories
    assert "截图" in config.categories


def test_loads_existing_config_and_merges_with_defaults(config_path):
    payload = {
        "archive_dir": "/tmp/custom-archive",
        "temp_dir": "/tmp/custom-temp",
        "window_opacity": 0.7,
        "auto_open_html": True,
        "screenshot_action": "archive",
        "window_position": [123, 456],
        "scale": 0.9,
        "categories": {
            "日志": {"exts": [".log"], "action": "archive"},
        },
        "agent": {
            "enabled": True,
            "agent_type": "hermes",
            "endpoint": "http://example.com/",
            "api_key": "abc",
            "timeout": 15,
        },
    }
    config_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    config = ConfigManager(str(config_path))

    assert config.archive_dir == "/tmp/custom-archive"
    assert config.temp_dir == "/tmp/custom-temp"
    assert config.config.window_opacity == 0.7
    assert config.config.screenshot_action == FileAction.ARCHIVE
    assert config.config.window_position == (123, 456)
    assert config.config.scale == 0.9

    # Custom category merged in, defaults preserved
    assert "日志" in config.categories
    assert "文档" in config.categories
    assert "截图" in config.categories

    # Agent config parsed via AgentConfig.from_dict
    assert config.agent_config.enabled is True
    assert config.agent_config.agent_type.value == "hermes"
    # Trailing slash stripped by AgentConfig.from_dict
    assert config.agent_config.endpoint == "http://example.com"
    assert config.agent_config.api_key == "abc"
    assert config.agent_config.timeout == 15


def test_falls_back_to_defaults_on_invalid_json(config_path, caplog):
    config_path.write_text("not a valid json", encoding="utf-8")

    import logging
    with caplog.at_level(logging.WARNING, logger="meowdesk.core.config"):
        config = ConfigManager(str(config_path))

    assert "配置" in caplog.text or "unreadable" in caplog.text or "defaults" in caplog.text
    assert config.archive_dir == AppConfig.get_default().archive_dir


def test_save_writes_serializable_file(config_path):
    config = ConfigManager(str(config_path))
    config.set("window_opacity", 0.5)
    assert config.save() is True

    data = json.loads(config_path.read_text(encoding="utf-8"))
    assert data["window_opacity"] == 0.5
    assert "categories" in data and "截图" in data["categories"]
    assert "agent" in data


def test_set_rejects_unknown_keys(config_path):
    config = ConfigManager(str(config_path))
    assert config.set("not_a_real_field", 1) is False
    # Confirm config file is not corrupted
    assert os.path.exists(config_path)


def test_get_returns_value_or_default(config_path):
    config = ConfigManager(str(config_path))
    assert config.get("archive_dir") == config.archive_dir
    assert config.get("missing-key", "fallback") == "fallback"


def test_get_returns_none_when_value_is_explicitly_none(config_path):
    config = ConfigManager(str(config_path))
    # window_position defaults to None — get() should return None,
    # not be confused with "missing key"
    assert config.get("window_position", "fallback") is None


def test_set_unknown_key_warns_and_returns_false(config_path, caplog):
    import logging
    config = ConfigManager(str(config_path))
    with caplog.at_level(logging.WARNING, logger="meowdesk.core.config"):
        ok = config.set("typo_key", "value")
    assert ok is False
    assert "typo_key" in caplog.text


def test_set_unknown_key_does_not_persist(config_path, monkeypatch):
    config = ConfigManager(str(config_path))
    save_calls = []
    monkeypatch.setattr(config, "save", lambda: save_calls.append(1) or True)
    config.set("typo_key", "value")
    assert save_calls == []
