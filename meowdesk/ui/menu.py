"""
右键菜单模块 — Windows Tkinter 实现

使用 menu_actions 模块的 MenuSpec 定义菜单结构，
与 macOS 共享相同的菜单项和动作逻辑。
"""

import os
import sys
import tkinter as tk
from tkinter import Menu, messagebox, filedialog
from typing import Any, Optional, List

from .settings import SettingsPanel


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
        self.parent = parent
        self.config = config
        self.window = window
        self.agent_gateway = agent_gateway
        self.on_quit_callback = on_quit_callback
        self.on_settings_saved = on_settings_saved
        
        self.menu: Optional[Menu] = None
        self._create_menu()
    
    def _create_menu(self):
        """创建菜单"""
        self.menu = Menu(self.parent, tearoff=0)
        
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
