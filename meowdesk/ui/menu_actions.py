"""Menu actions and context menu definition for MeowDesk.

The macOS and Windows platforms use different mechanisms to show
a context menu, but the menu structure and actions are shared.
This module extracts that shared logic.
"""

import os
import subprocess
import sys
import webbrowser
from typing import TYPE_CHECKING, Callable, List, Optional, Tuple

from ..agent import CommandRegistry
from ..index_gen import write_html_index
from .animation import AnimationManager

if TYPE_CHECKING:
    from .window import MeowWindow


MenuItem = Tuple[str, Callable[[], None]]
Separator = None
MenuSpec = List[Optional[MenuItem]]


def build_menu_items(window: "MeowWindow") -> MenuSpec:
    """Build the context menu item list.

    Returns a list of (label, callback) pairs and None separators.
    Platform-specific menus (macOS native vs tkinter) can consume
    this structure and render appropriately.
    """

    return [
        ("打开导航页", lambda: action_open_html(window)),
        ("打开归档目录", lambda: action_open_archive_dir(window)),
        None,
        ("清理磁盘", lambda: action_clean_disk(window)),
        ("查看日期", lambda: action_check_date(window)),
        ("定期提醒", lambda: action_check_reminders(window)),
        ("系统信息", lambda: action_system_info(window)),
        None,
        ("设置", lambda: action_open_settings(window)),
        ("关于", lambda: action_show_about(window)),
        None,
        ("退出", window.quit),
    ]


def action_open_html(window: "MeowWindow") -> None:
    """Open the HTML index in the default browser."""

    archive_dir = window.config.archive_dir
    if not _ensure_archive_dir_writable(window, archive_dir):
        return
    html_file = os.path.join(archive_dir, "index.html")
    if not os.path.exists(html_file):
        window._update_html()
    if os.path.exists(html_file):
        webbrowser.open(f"file://{html_file}")
    else:
        window.state.show_bubble("导航页生成失败", 60)


def action_open_archive_dir(window: "MeowWindow") -> None:
    """Open the archive directory in the system file manager."""

    archive_dir = window.config.archive_dir
    if os.path.exists(archive_dir):
        if sys.platform == "darwin":
            subprocess.Popen(["open", archive_dir])
        elif sys.platform == "win32":
            os.startfile(archive_dir)
        else:
            subprocess.Popen(["xdg-open", archive_dir])
    else:
        from ..utils import get_logger
        get_logger(__name__).warning("archive dir missing: %s", archive_dir)


def action_clean_disk(window: "MeowWindow") -> None:
    """Run the clean_disk command and show a bubble."""

    registry = CommandRegistry()
    result = registry.execute("clean_disk")
    if result["success"]:
        data = result["result"]
        window.state.show_bubble(
            f"清理：{data['cleaned_files']} 文件，{data['cleaned_size_mb']} MB", 80
        )
    else:
        window.state.show_bubble("清理失败", 40)


def action_check_date(window: "MeowWindow") -> None:
    """Run the check_date command and show a bubble."""

    registry = CommandRegistry()
    result = registry.execute("check_date")
    if result["success"]:
        data = result["result"]
        window.state.show_bubble(
            f"{data['weekday']} 距周末{data['days_to_weekend']}天", 80
        )


def action_check_reminders(window: "MeowWindow") -> None:
    """Show the next scheduled reminder."""

    if not window._reminder_checker:
        window.state.show_bubble("暂无提醒，在设置中添加", 80)
        return
    next_reminder = window._reminder_checker.trigger_immediate()
    if next_reminder:
        window.state.show_bubble(
            f"下一提醒：{next_reminder['name']} ({next_reminder['time']})", 80
        )
    else:
        count = len(window.config.reminders)
        window.state.show_bubble(
            f"今日 {count} 个提醒已完成" if count else "暂无提醒，在设置中添加", 80
        )


def action_system_info(window: "MeowWindow") -> None:
    """Run the system_info command and show a bubble."""

    registry = CommandRegistry()
    result = registry.execute("system_info")
    if result["success"]:
        data = result["result"]
        window.state.show_bubble(
            f"CPU {data['cpu_count']}核 {data['cpu_percent']}% | 内存 {data['memory_percent']}%",
            80,
        )


def action_open_settings(window: "MeowWindow") -> None:
    """Open the settings file or macOS settings panel."""

    if sys.platform == "darwin":
        _open_macos_settings(window)
        return
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.getcwd()
    config_file = os.path.join(base, "config.json")
    if os.path.exists(config_file) and sys.platform == "win32":
        os.startfile(config_file)


def action_show_about(window: "MeowWindow") -> None:
    """Show the about bubble."""

    from .. import __version__
    window.state.show_bubble(f"妙喵桌宠 v{__version__}", 80)


def _ensure_archive_dir_writable(window: "MeowWindow", archive_dir: str) -> bool:
    """Check archive dir writability, handling macOS TCC if needed."""

    if sys.platform == "darwin" and hasattr(window.platform_window, "check_directory_writable"):
        if not window.platform_window.check_directory_writable(archive_dir):
            granted = window.platform_window.request_directory_access(archive_dir)
            if not granted:
                window.state.show_bubble("请将 Python.app 添加到完全磁盘访问权限", 120)
                return False
            if not window.platform_window.check_directory_writable(archive_dir):
                window.state.show_bubble("授权未生效，请重启应用后重试", 120)
                return False
        return True
    if not os.path.exists(archive_dir):
        try:
            os.makedirs(archive_dir, exist_ok=True)
        except OSError as e:
            window.state.show_bubble(f"归档目录无法创建：{e}", 120)
            return False
    if not os.access(archive_dir, os.W_OK):
        window.state.show_bubble(f"归档目录不可写：{archive_dir}", 120)
        return False
    return True


def _open_macos_settings(window: "MeowWindow") -> None:
    """Open the macOS settings panel via applescript."""

    try:
        from .macos_settings import open_settings
        open_settings(window.config.config_path)
    except Exception as e:
        from ..utils import get_logger
        get_logger(__name__).exception("open macos settings failed: %s", e)
        window.state.show_bubble("打开设置失败", 60)
