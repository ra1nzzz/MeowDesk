"""
UI 模块
兼容 macOS / Windows
"""

from .window import MeowWindow
from .animation import AnimationManager

__all__ = ['MeowWindow', 'AnimationManager', 'ContextMenu', 'SystemTray', 'SettingsPanel', 'ChatWindow']


def __getattr__(name):
    """Lazy-load optional UI modules so that environments without
    tkinter / AppKit can still import :mod:`meowdesk.ui` and run the
    non-platform-specific parts (e.g. tests)."""

    if name == "ContextMenu":
        from .menu import ContextMenu
        return ContextMenu
    if name == "SystemTray":
        from .tray import SystemTray
        return SystemTray
    if name == "SettingsPanel":
        from .settings import SettingsPanel
        return SettingsPanel
    if name == "ChatWindow":
        from .chat import ChatWindow
        return ChatWindow
    raise AttributeError(f"module 'meowdesk.ui' has no attribute {name!r}")
