"""Filesystem helpers: atomic writes and JSON with backup recovery."""

import json
import os
import shutil
import tempfile
from typing import Any


def atomic_write_text(path: str, content: str, encoding: str = "utf-8") -> None:
    """Write ``content`` to ``path`` atomically.

    Writes to a sibling temp file first, fsyncs, then renames over the
    destination.  On Windows where ``os.replace`` already replaces the
    target atomically when both paths are on the same volume, this
    avoids half-written files when the process is killed mid-write.
    """

    directory = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp_path = tempfile.mkstemp(
        prefix=f".{os.path.basename(path)}.", suffix=".tmp", dir=directory
    )
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(content)
            f.flush()
            try:
                os.fsync(f.fileno())
            except (AttributeError, OSError):
                # fsync isn't critical for correctness; failures are best-effort
                pass
        os.replace(tmp_path, path)
    except Exception:
        # Best-effort cleanup of the temp file on failure
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise


def atomic_write_json(path: str, data: Any, **json_kwargs) -> None:
    """Serialise ``data`` as JSON and write atomically."""

    json_kwargs.setdefault("ensure_ascii", False)
    json_kwargs.setdefault("indent", 2)
    content = json.dumps(data, **json_kwargs)
    atomic_write_text(path, content)


def load_json_with_backup(
    path: str,
    backup_suffix: str = ".bak",
    max_backups: int = 3,
) -> Any:
    """Load JSON from ``path``, falling back to a backup if the main file is corrupt.

    Behaviour:

    1. If ``path`` exists and parses, return its contents.
    2. If parsing fails, rotate the corrupt file to ``path + backup_suffix``
       and try the previous backup (up to ``max_backups`` files).  The
       first valid backup is loaded.
    3. If everything fails, return ``None``.

    This keeps the next run from crashing on a half-written config or
    database, while preserving the broken copy for forensic inspection.
    """

    if not os.path.exists(path):
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        pass

    # Rotate the corrupt primary out of the way so the next write succeeds.
    # First, shift any existing backup chain aside so we don't clobber it
    # when we move the corrupt primary onto ``path + backup_suffix``.
    primary_backup = path + backup_suffix
    if os.path.exists(primary_backup):
        _rotate_backups(path, backup_suffix, max_backups)
    try:
        shutil.move(path, primary_backup)
    except OSError:
        pass

    for i in range(max_backups):
        candidate = path + f"{backup_suffix}.{i}" if i > 0 else primary_backup
        if not os.path.exists(candidate):
            continue
        try:
            with open(candidate, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

    return None


def _rotate_backups(path: str, suffix: str, max_backups: int) -> None:
    """Shift ``path + suffix.{i}`` aside by one when adding a new backup.

    Called with a corrupt primary about to land at ``path + suffix``;
    this moves the existing ``path + suffix`` to ``path + suffix.1``,
    ``path + suffix.1`` to ``path + suffix.2``, and so on, up to
    ``max_backups``.  The oldest is dropped.
    """

    if max_backups <= 1:
        return

    # Drop the oldest if it's already at the cap.
    oldest = f"{path}{suffix}.{max_backups - 1}"
    if os.path.exists(oldest):
        try:
            os.remove(oldest)
        except OSError:
            pass

    # Walk from the second-newest down, shifting to make room.
    for i in range(max_backups - 2, 0, -1):
        src = f"{path}{suffix}.{i}"
        dst = f"{path}{suffix}.{i + 1}"
        if os.path.exists(src):
            try:
                shutil.move(src, dst)
            except OSError:
                pass

    # Finally, move the current primary backup to .1
    primary_backup = f"{path}{suffix}"
    if os.path.exists(primary_backup):
        try:
            shutil.move(primary_backup, f"{path}{suffix}.1")
        except OSError:
            pass
