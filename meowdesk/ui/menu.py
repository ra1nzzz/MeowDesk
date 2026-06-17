"""
右键菜单模块 — Windows Tkinter 实现

使用 menu_actions 模块的 MenuSpec 定义菜单结构，
与 macOS 共享相同的菜单项和动作逻辑。
"""

import sys
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Theme palettes (shared with settings.py)
# ---------------------------------------------------------------------------
DARK_COLORS = {
    'bg': '#121218',
    'fg': '#F0EDE8',
    'entry_bg': '#22222E',
    'accent': '#F4845F',
    'accent_hover': '#F69B7D',
    'border': '#2D2D3D',
    'text_muted': '#6B6880',
}

LIGHT_COLORS = {
    'bg': '#FAF7F2',
    'fg': '#2D2A33',
    'entry_bg': '#EDE8E0',
    'accent': '#E8734E',
    'accent_hover': '#D4613B',
    'border': '#D5CFC7',
    'text_muted': '#8A8490',
}


def _is_windows_dark_mode() -> bool:
    """Detect Windows 10/11 dark mode preference from the registry."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return int(value) == 0          # 0 = dark, 1 = light
    except Exception:
        return True                      # fallback to dark


def resolve_colors(config=None) -> dict:
    """Return the correct palette based on config.color_mode."""
    color_mode = "dark"
    if config is not None:
        try:
            color_mode = getattr(config, "color_mode", "dark")
        except Exception:
            pass
    if color_mode == "light":
        return LIGHT_COLORS
    if color_mode == "system":
        return DARK_COLORS if _is_windows_dark_mode() else LIGHT_COLORS
    return DARK_COLORS


class _MenuWindowAdapter:
    """Expose the small MeowWindow surface used by shared menu actions."""

    config: Any
    parent: Any
    state: Any
    agent_gateway: Any
    _update_html: Any
    _on_settings_saved: Any

    def __init__(
        self,
        config,
        parent,
        agent_gateway=None,
        on_quit_callback=None,
        on_settings_saved=None,
    ):
        self.config = config
        self.parent = parent
        self.agent_gateway = agent_gateway
        self._on_quit_callback = on_quit_callback
        self.state = type("FakeState", (), {"show_bubble": lambda s, t, d: None})()
        self._update_html = lambda: None
        self._on_settings_saved = on_settings_saved

    def quit(self):
        if self._on_quit_callback:
            self._on_quit_callback()


class ContextMenu:
    """右键菜单（Tkinter 实现）"""

    def __init__(self, parent, config, window=None, agent_gateway=None,
                 on_quit_callback=None, on_settings_saved=None):
        from tkinter import Menu
        self._Menu = Menu
        self.parent = parent
        self.config = config
        self.window = window
        self.agent_gateway = agent_gateway
        self.on_quit_callback = on_quit_callback
        self.on_settings_saved = on_settings_saved

        self.menu: Optional[Any] = None
        self._create_menu()

    def _create_menu(self):
        """创建菜单（带主题配色）"""
        c = resolve_colors(getattr(self.config, 'config', self.config))

        self.menu = self._Menu(
            self.parent,
            tearoff=0,
            bg=c['entry_bg'],
            fg=c['fg'],
            activebackground=c['accent'],
            activeforeground='#FFFFFF',
            relief='flat',
            borderwidth=0,
            font=("Microsoft YaHei", 10),
        )

        from .menu_actions import build_menu_items

        menu_window = self.window or _MenuWindowAdapter(
            self.config,
            self.parent,
            agent_gateway=self.agent_gateway,
            on_quit_callback=self._quit,
            on_settings_saved=self._on_settings_saved,
        )
        menu_items = build_menu_items(menu_window)

        for item in menu_items:
            if item is None:
                self.menu.add_separator()
            else:
                label, callback = item
                self.menu.add_command(label=label, command=callback)

    def show(self, x: int, y: int):
        """显示菜单"""
        try:
            self.menu.tk_popup(x, y)
        finally:
            self.menu.grab_release()

    def _on_settings_saved(self):
        """设置保存回调"""
        if self.on_settings_saved:
            self.on_settings_saved()

    def _quit(self):
        """退出"""
        if self.on_quit_callback:
            self.on_quit_callback()
