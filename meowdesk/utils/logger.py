"""Logger utilities for MeowDesk.

Centralises logging configuration so application modules can speak
through ``logging`` rather than scattering ``print`` calls.

Two named loggers are exposed:

- ``meowdesk`` — root package logger
- ``meowdesk.user`` — user-facing messages (warnings, errors that should
  reach the operator even when the GUI is up)

Usage::

    from meowdesk.utils.logger import get_logger

    log = get_logger(__name__)
    log.info("started")
    log.error("bad thing", exc_info=True)
"""

import logging
import os
import sys
from logging import Logger
from typing import Optional


_DEFAULT_FORMAT = "%(asctime)s %(name)s [%(levelname)s] %(message)s"


_configured = False


def _has_file_handler(root: Logger, log_file: str) -> bool:
    target = os.path.abspath(log_file)
    for handler in root.handlers:
        if isinstance(handler, logging.FileHandler):
            if os.path.abspath(handler.baseFilename) == target:
                return True
    return False


def configure_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    fmt: str = _DEFAULT_FORMAT,
    propagate: bool = True,
) -> None:
    """Initialise the root ``meowdesk`` logger.

    Idempotent — calling more than once is a no-op so tests can call
    it freely without stacking handlers.

    ``propagate`` defaults to ``True`` so pytest's ``caplog`` (which
    attaches to the root logger) can capture records.  Set it to
    ``False`` in shipped binaries that want their own isolated
    handler tree.
    """

    global _configured
    root = logging.getLogger("meowdesk")
    formatter = logging.Formatter(fmt)

    if _configured:
        root.setLevel(level)
        root.propagate = propagate
        if log_file and not _has_file_handler(root, log_file):
            os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            root.addHandler(file_handler)
        return

    root.setLevel(level)
    root.propagate = propagate

    if sys.stderr is not None:
        stream = logging.StreamHandler(stream=sys.stderr)
        stream.setFormatter(formatter)
        root.addHandler(stream)

    if log_file:
        os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    _configured = True


def get_logger(name: Optional[str] = None) -> Logger:
    """Return a logger under the ``meowdesk`` namespace.

    Calling without ``name`` returns the package root logger.
    ``name`` should typically be ``__name__`` of the calling module so
    log records are easy to filter.
    """

    if not _configured:
        configure_logging()
    if name is None or name == "meowdesk":
        return logging.getLogger("meowdesk")
    if name.startswith("meowdesk."):
        return logging.getLogger(name)
    return logging.getLogger(f"meowdesk.{name}")


def user_logger() -> Logger:
    """Logger for messages that should surface to end users.

    Useful in TUI / bubble contexts where a separate handler can
    route them to a notification area.
    """

    return get_logger("meowdesk.user")
