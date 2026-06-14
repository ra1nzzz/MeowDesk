import json
from pathlib import Path

from meowdesk.core import ConfigManager


def test_config_roundtrips_launch_at_startup(tmp_path):
    path = tmp_path / "config.json"
    config = ConfigManager(str(path))

    assert config.config.launch_at_startup is False
    config.config.launch_at_startup = True
    assert config.save() is True

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["launch_at_startup"] is True

    reloaded = ConfigManager(str(path))
    assert reloaded.config.launch_at_startup is True


def test_config_missing_field_defaults_false(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"archive_dir": "/tmp"}), encoding="utf-8")

    config = ConfigManager(str(path))
    assert config.config.launch_at_startup is False
