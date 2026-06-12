"""Tests for the file-drop archive pipeline."""

import os
import sys

from meowdesk.core import ConfigManager, FileClassifier, FileDatabase, FileHandler
from meowdesk.ui.animation import AnimationManager
from meowdesk.ui.window_drop import FileDropHandler


class _DummyState:
    def __init__(self):
        self.processing = False
        self.states = []

    def enter_state(self, state, timer=0):
        self.states.append((state, timer))

    def set_processing(self, value):
        self.processing = value


def _make_handler(tmp_path, bubbles=None, finished=None):
    config = ConfigManager(str(tmp_path / "config.json"))
    config.config.archive_dir = str(tmp_path / "archive")
    config.config.temp_dir = str(tmp_path / "temp")
    config.save()

    db = FileDatabase(str(tmp_path / "filedb.json"))
    state = _DummyState()
    bubbles = bubbles if bubbles is not None else []
    finished = finished if finished is not None else []

    handler = FileDropHandler(
        config=config,
        db=db,
        classifier=FileClassifier(config.config),
        file_handler=FileHandler(config.archive_dir, config.temp_dir),
        state=state,
        show_bubble=lambda text, duration: bubbles.append((text, duration)),
        on_finished=lambda: finished.append(True),
        check_archive_writable=lambda: True,
    )
    return handler, config, db, state, bubbles, finished


def test_drop_pipeline_archives_file_and_records_it(tmp_path):
    handler, config, db, state, bubbles, finished = _make_handler(tmp_path)
    src = tmp_path / "incoming.txt"
    src.write_text("hello", encoding="utf-8")

    result = handler.process_inline([str(src)], [], big_batch=False)

    assert "已归档" in result
    assert not src.exists()
    assert len(db.records) == 1
    record = db.records[0]
    assert record.original_name == "incoming.txt"
    assert record.action == "archive"
    assert os.path.exists(record.destination)
    assert record.destination.startswith(config.archive_dir)
    assert finished == [True]
    assert bubbles
    assert state.processing is False
    assert any(item[0] == AnimationManager.CARRYING for item in state.states)


def test_windows_drop_internal_decodes_bytes(monkeypatch):
    if sys.platform != "win32":
        return

    from meowdesk.platform.windows import WindowsWindow

    window = WindowsWindow(100, 100)
    received = []
    window.on_drop(lambda files: received.extend(files))

    window._on_drop_internal(["C:/tmp/a.txt".encode("utf-8")])

    assert received == ["C:/tmp/a.txt"]
