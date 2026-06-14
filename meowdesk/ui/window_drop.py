"""File-drop handling: receive paths, classify, archive/recycle, persist.

This is the "user dropped files onto the cat" pipeline.  It runs the
expensive work on a background thread so the UI stays responsive;
the platform window is poked only via callbacks supplied by the
owner.
"""

import os
import random
import shutil
import threading
from typing import List, Optional

from ..core import (
    ConfigManager,
    FileClassifier,
    FileDatabase,
    FileHandler,
)
from ..utils import get_logger
from .animation import AnimationManager


_log = get_logger(__name__)


class FileDropHandler:
    """Owns the drop-files pipeline.

    The owning :class:`MeowWindow` calls :meth:`receive` when the
    platform layer hands us a list of paths.  We expand folders,
    bubble a status update, switch to a receiving animation and start
    a background thread for the heavy lifting.
    """

    BIG_BATCH_THRESHOLD = 10

    def __init__(
        self,
        config: ConfigManager,
        db: FileDatabase,
        classifier: FileClassifier,
        file_handler: FileHandler,
        state,
        show_bubble,
        on_finished=None,
        check_archive_writable: Optional[callable] = None,
    ):
        self._config = config
        self._db = db
        self._classifier = classifier
        self._file_handler = file_handler
        self._state = state
        self._show_bubble = show_bubble
        self._on_finished = on_finished
        self._check_archive_writable = check_archive_writable

    def receive(self, files: List[str]) -> None:
        """Top-level entry point invoked by the platform window drop callback."""

        if not self._ensure_archive_writable():
            return

        all_files: List[str] = []
        folders_to_remove: List[str] = []

        for item in files:
            if os.path.isfile(item):
                all_files.append(item)
            elif os.path.isdir(item):
                folders_to_remove.append(item)
                for root, _, filenames in os.walk(item):
                    for filename in filenames:
                        fp = os.path.join(root, filename)
                        if os.path.isfile(fp):
                            all_files.append(fp)

        if not all_files:
            return

        count = len(all_files)
        big_batch = count >= self.BIG_BATCH_THRESHOLD
        self._state.enter_state(
            AnimationManager.SURPRISED, timer=10
        )
        if big_batch:
            self._show_bubble(f"收到 {count} 个文件，正在处理...", 120)
        else:
            self._show_bubble(f"收到 {count} 个文件", 40)
        _log.info("drop received: %d files (big_batch=%s)", count, big_batch)

        threading.Thread(
            target=self._process_async,
            args=(all_files, folders_to_remove, big_batch),
            daemon=True,
        ).start()

    def process_inline(self, files: List[str], folders_to_remove: List[str], big_batch: bool) -> None:
        """Synchronous variant used by tests.

        Returns the final summary message so tests can assert on it
        without going through the bubble layer.
        """

        return self._process(files, folders_to_remove, big_batch)

    def _process_async(self, files, folders_to_remove, big_batch) -> None:
        try:
            self._process(files, folders_to_remove, big_batch)
        except Exception as e:
            self._state.set_processing(False)
            _log.exception("file processing crashed: %s", e)

    def _process(self, files, folders_to_remove, big_batch) -> str:
        self._state.set_processing(True)
        self._state.enter_state(
            AnimationManager.RECEIVING if big_batch else AnimationManager.CARRYING
        )

        recycled = archived = duplicated = errors = 0
        for filepath in files:
            try:
                outcome = self._process_one(filepath)
                if outcome == "recycle":
                    recycled += 1
                elif outcome == "duplicate":
                    duplicated += 1
                elif outcome == "error":
                    errors += 1
                else:
                    archived += 1
            except Exception as e:
                errors += 1
                _log.error("process %s failed: %s", os.path.basename(filepath), e)

        for folder in folders_to_remove:
            if os.path.exists(folder):
                try:
                    shutil.rmtree(folder)
                except Exception as e:
                    _log.error("rmtree %s failed: %s", folder, e)

        self._state.set_processing(False)
        if self._on_finished:
            try:
                self._on_finished()
            except Exception as e:
                _log.error("on_finished callback failed: %s", e)

        message = self._format_summary(recycled, archived, duplicated, errors)
        _log.info("drop finished: %s", message)
        self._state.enter_state(
            AnimationManager.SHY, timer=50
        ) if random.random() < 0.25 else self._state.enter_state(
            AnimationManager.HAPPY, timer=80
        )
        self._show_bubble(message, 80)
        return message

    def _process_one(self, filepath: str) -> str:
        filename = os.path.basename(filepath)
        file_size = self._file_handler.get_file_size(filepath)
        md5 = self._file_handler.calculate_md5(filepath)

        for record in self._db.search():
            record_md5 = getattr(record, "md5", "")
            record_action = getattr(record, "action", "")
            if (
                record_md5 == md5
                and record_action != "recycle"
            ):
                dest = getattr(record, "destination", "")
                if dest and dest != "(已回收)" and os.path.exists(dest):
                    _log.info("skip duplicate: %s", filename)
                    try:
                        os.remove(filepath)
                    except OSError:
                        pass
                    return "duplicate"

        classify_result = self._classifier.classify(filepath)
        category = classify_result.category
        action_value = (
            classify_result.action.value
            if hasattr(classify_result.action, "value")
            else str(classify_result.action)
        )
        now = datetime_now()
        record = {
            "timestamp": now.isoformat(),
            "original_name": filename,
            "original_path": filepath,
            "category": category,
            "action": action_value,
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "file_size": file_size,
            "md5": md5,
        }

        if action_value == "recycle":
            result = self._file_handler.recycle_file(filepath)
            if result.success:
                record["destination"] = result.destination
                self._db.add_record_dict(record)
                _log.info("recycled %s", filename)
                return "recycle"
            _log.error("recycle %s failed: %s", filename, result.error)
            return "error"

        result = self._file_handler.archive_file(filepath, category)
        if result.success:
            record["destination"] = result.destination
            self._db.add_record_dict(record)
            _log.info("archived %s -> %s/", filename, category)
            return "archive"
        _log.error("archive %s failed: %s", filename, result.error)
        return "error"

    def _ensure_archive_writable(self) -> bool:
        """Delegate to the owner so platform-specific quirks (e.g. macOS
        TCC permissions) can be honoured by :class:`MeowWindow`."""

        if self._check_archive_writable is None:
            return True
        return self._check_archive_writable()

    @staticmethod
    def _format_summary(recycled, archived, duplicated, errors) -> str:
        parts = []
        if recycled:
            parts.append(f"{recycled} 截图回收")
        if archived:
            parts.append(f"{archived} 已归档")
        if duplicated:
            parts.append(f"{duplicated} 重复跳过")
        if errors:
            parts.append(f"{errors} 失败")
        return " · ".join(parts) if parts else "完成"


def datetime_now():
    """Helper indirection so tests can monkeypatch the clock."""

    from datetime import datetime
    return datetime.now()
