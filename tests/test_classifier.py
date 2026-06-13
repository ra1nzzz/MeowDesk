"""Tests for ``meowdesk.core.classifier.FileClassifier``.

The classifier imports ``PIL`` at module import time, so Pillow must be
installed (declared in ``requirements.txt``).  Platform-specific screen
resolution lookups are exercised through monkeypatching.
"""

import sys
import types
from unittest.mock import patch

import pytest
from PIL import Image

from meowdesk.core.classifier import FileClassifier
from meowdesk.core.types import (
    AppConfig,
    FileAction,
)


@pytest.fixture
def classifier():
    return FileClassifier(AppConfig.get_default())


def _make_png(path, size=(1920, 1080)):
    Image.new("RGB", size, color="white").save(path, format="PNG")


def _build_fake_appkit(screen_w=1920, screen_h=1080):
    """Build a stand-in for the ``AppKit`` module.

    The classifier does ``AppKit.NSScreen.mainScreen().frame().size`` on
    macOS, so the fake provides a class with ``NSScreen`` exposing
    ``mainScreen()`` and the returned object exposes ``frame()``.
    """

    fake_size = type("Size", (), {"width": screen_w, "height": screen_h})()
    fake_frame = type("Frame", (), {"size": fake_size})()
    # Object returned by NSScreen.mainScreen(); has .frame() returning a frame
    fake_screen_instance = type(
        "ScreenInstance",
        (),
        {"frame": staticmethod(lambda: fake_frame)},
    )()
    # NSScreen class with mainScreen() returning the instance above
    fake_ns_screen_cls = type(
        "NSScreen",
        (),
        {"mainScreen": staticmethod(lambda: fake_screen_instance)},
    )
    return types.SimpleNamespace(NSScreen=fake_ns_screen_cls)


def test_classifies_by_extension_into_matching_category(classifier, tmp_path):
    f = tmp_path / "report.pdf"
    f.write_bytes(b"x")

    result = classifier.classify(str(f))
    assert result.category == "文档"
    assert result.action == FileAction.ARCHIVE
    assert result.is_screenshot is False


def test_unmatched_extension_falls_back_to_other(classifier, tmp_path):
    f = tmp_path / "weird.xyz"
    f.write_bytes(b"x")
    result = classifier.classify(str(f))
    assert result.category == "其他"
    assert result.action == FileAction.ARCHIVE


def test_filename_screenshot_keyword_is_detected(classifier, tmp_path):
    f = tmp_path / "微信截图_20260102.png"
    _make_png(f)
    result = classifier.classify(str(f))
    assert result.is_screenshot is True
    assert result.category == "截图"
    assert result.action == FileAction.RECYCLE


def test_non_image_with_screenshot_keyword_is_not_treated_as_screenshot(classifier, tmp_path):
    f = tmp_path / "screenshot_notes.txt"
    f.write_text("hello")
    result = classifier.classify(str(f))
    # extension is .txt, not an image type, so screenshot path is skipped
    assert result.is_screenshot is False
    assert result.category == "文档"


def test_path_in_temp_dir_marks_screenshot(classifier, tmp_path):
    f = tmp_path / "AppData" / "Local" / "Temp" / "clip.png"
    f.parent.mkdir(parents=True)
    _make_png(f, size=(640, 480))
    result = classifier.classify(str(f))
    assert result.is_screenshot is True


def test_resolution_match_marks_screenshot(tmp_path, monkeypatch):
    # Override TEMP_DIRS at the class level so path-based detection
    # does not trip on "tmp" inside pytest's tmp_path.
    monkeypatch.setattr(FileClassifier, "TEMP_DIRS", [])

    f = tmp_path / "desktop.png"
    _make_png(f, size=(1920, 1080))

    fake_appkit = _build_fake_appkit(1920, 1080)

    # Pretend we are on macOS so the resolution branch picks the AppKit path
    monkeypatch.setattr(sys, "platform", "darwin")
    classifier = FileClassifier(AppConfig.get_default())
    with patch.dict(sys.modules, {"AppKit": fake_appkit}):
        result = classifier.classify(str(f))
    assert result.is_screenshot is True


def test_resolution_mismatch_does_not_mark_screenshot(tmp_path, monkeypatch):
    # Override TEMP_DIRS at the class level so path-based detection
    # does not trip on "tmp" inside pytest's tmp_path.
    monkeypatch.setattr(FileClassifier, "TEMP_DIRS", [])

    f = tmp_path / "small.svg"
    # Write a minimal valid SVG so the file exists and has a real image
    # extension.  SVG is in the "图片" category but not "截图", so the
    # extension-match step can settle on a non-screenshot category.
    f.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"/>',
        encoding="utf-8",
    )

    fake_appkit = _build_fake_appkit(1920, 1080)
    monkeypatch.setattr(sys, "platform", "darwin")
    classifier = FileClassifier(AppConfig.get_default())
    with patch.dict(sys.modules, {"AppKit": fake_appkit}):
        result = classifier.classify(str(f))
    assert result.is_screenshot is False
    # Falls through to extension match -> 图片
    assert result.category == "图片"
    assert result.action == FileAction.ARCHIVE


def test_classifier_uses_screenshot_action_from_config(classifier, tmp_path):
    f = tmp_path / "微信截图_xx.png"
    _make_png(f)

    # Switch the screenshot action to archive
    classifier.config.screenshot_action = FileAction.ARCHIVE
    result = classifier.classify(str(f))
    assert result.is_screenshot is True
    assert result.action == FileAction.ARCHIVE
