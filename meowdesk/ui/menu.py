"""
右键菜单模块 — Windows 自定义绘制实现

使用 Toplevel + Canvas 实现圆角、悬停效果、图标和分区样式，
匹配 meowdesk-context-menu.html 原型设计。
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
    # Menu-specific
    'menu_bg': '#1A1A24',
    'menu_hover': '#2A2230',
    'separator': '#2D2D3D',
    'text_secondary': '#A8A4B8',
    'danger': '#F87171',
    'danger_hover': '#2A1A1E',
}

LIGHT_COLORS = {
    'bg': '#FAF7F2',
    'fg': '#2D2A33',
    'entry_bg': '#EDE8E0',
    'accent': '#E8734E',
    'accent_hover': '#D4613B',
    'border': '#D5CFC7',
    'text_muted': '#8A8490',
    # Menu-specific
    'menu_bg': '#FFFFFF',
    'menu_hover': '#FDF0EB',
    'separator': '#E5E0D8',
    'text_secondary': '#6B6578',
    'danger': '#D94444',
    'danger_hover': '#FDE8E8',
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


# ---------------------------------------------------------------------------
# Menu icon mapping (label -> unicode icon)
# ---------------------------------------------------------------------------
MENU_ICONS = {
    "打开导航页": "\u25CE",    # ◎ compass-like
    "打开归档目录": "\U0001F4C1",  # 📁 folder
    "自由对话": "\U0001F4AC",      # 💬 chat bubble
    "清理磁盘": "\U0001F9F9",      # 🧹 broom
    "查看日期": "\U0001F4C5",      # 📅 calendar
    "假期提醒": "\U0001F389",      # 🎉 party
    "经期提醒": "\U0001F49D",      # 💝 heart
    "系统信息": "\U0001F4BB",      # 💻 laptop
    "设置": "\u2699",              # ⚙ gear
    "关于": "\u2139",              # ℹ info
    "退出": "\u23FB",              # ⏻ power
}

# Labels that should use danger styling
DANGER_LABELS = {"退出"}

# Menu structure: reorder to match prototype
# Group 1: 打开导航页, 打开归档目录, 自由对话
# Sep
# Group 2: 清理磁盘, 系统信息, 查看日期, 假期提醒, 经期提醒
# Sep
# Group 3: 设置, 关于
# Sep
# 退出

PROTOTYPE_ORDER = [
    "打开导航页", "打开归档目录", "自由对话",
    None,
    "清理磁盘", "系统信息", "查看日期", "假期提醒", "经期提醒",
    None,
    "设置", "关于",
    None,
    "退出",
]


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
    """右键菜单（自定义绘制实现，匹配 HTML 原型）"""

    # Layout constants (from prototype CSS)
    MENU_WIDTH = 220
    ITEM_HEIGHT = 40
    RADIUS = 12
    PADDING_Y = 6
    SEPARATOR_HEIGHT = 1
    SEPARATOR_MARGIN_Y = 6
    SEPARATOR_MARGIN_X = 12
    ICON_SIZE = 18
    ITEM_GAP = 10
    ITEM_PAD_X = 14

    def __init__(self, parent, config, window=None, agent_gateway=None,
                 on_quit_callback=None, on_settings_saved=None):
        self.parent = parent
        self.config = config
        self.window = window
        self.agent_gateway = agent_gateway
        self.on_quit_callback = on_quit_callback
        self.on_settings_saved = on_settings_saved

        self._menu_window: Optional[Any] = None
        self._canvas: Optional[Any] = None
        self._item_frames: list = []
        self._dismissed = False

    def _build_items_map(self):
        """Build label->callback map from menu_actions."""
        from .menu_actions import build_menu_items

        menu_window = self.window or _MenuWindowAdapter(
            self.config,
            self.parent,
            agent_gateway=self.agent_gateway,
            on_quit_callback=self._quit,
            on_settings_saved=self._on_settings_saved,
        )
        items = build_menu_items(menu_window)
        item_map = {}
        for item in items:
            if item is not None:
                label, callback = item
                # Strip emoji prefixes from old format
                clean = label
                for prefix in ("💬 ", "🧹 ", "📅 ", "🎉 ", "💝 ", "💻 "):
                    if clean.startswith(prefix):
                        clean = clean[len(prefix):]
                        break
                item_map[clean] = callback
        return item_map

    def _create_menu(self):
        """Create the custom menu window."""
        import tkinter as tk

        c = resolve_colors(getattr(self.config, 'config', self.config))

        # Build callback map
        items_map = self._build_items_map()

        # Create borderless window
        self._menu_window = tk.Toplevel(self.parent)
        self._menu_window.overrideredirect(True)
        self._menu_window.configure(bg=c['menu_bg'])
        self._menu_window.attributes('-topmost', True)

        # Try to make the background semi-transparent on Windows
        try:
            self._menu_window.attributes('-alpha', 0.95)
        except Exception:
            pass

        # Calculate total height
        total_h = self.PADDING_Y * 2
        for item in PROTOTYPE_ORDER:
            if item is None:
                total_h += self.SEPARATOR_HEIGHT + self.SEPARATOR_MARGIN_Y * 2
            else:
                total_h += self.ITEM_HEIGHT

        w = self.MENU_WIDTH
        h = total_h
        r = self.RADIUS

        # Canvas for rounded background
        canvas = tk.Canvas(self._menu_window, width=w, height=h,
                           bg=c['menu_bg'], highlightthickness=0, bd=0)
        canvas.pack(fill='both', expand=True)
        self._canvas = canvas

        # Draw rounded rectangle background
        self._draw_rounded_rect(canvas, 0, 0, w, h, r, c['menu_bg'], c['border'])

        # Create item frames overlay
        overlay = tk.Frame(canvas, bg=c['menu_bg'])
        canvas.create_window((0, 0), window=overlay, anchor='nw', tags='overlay')

        # Update overlay size after rendering
        def _resize_overlay(event):
            canvas.itemconfigure('overlay', width=w, height=h)
        canvas.bind('<Configure>', _resize_overlay)

        self._item_frames = []
        y = self.PADDING_Y

        for item in PROTOTYPE_ORDER:
            if item is None:
                # Separator
                sep_y = y + self.SEPARATOR_MARGIN_Y
                sep_frame = tk.Frame(overlay, height=1, bg=c['separator'])
                sep_frame.place(x=self.SEPARATOR_MARGIN_X, y=sep_y,
                               width=w - self.SEPARATOR_MARGIN_X * 2, height=1)
                y += self.SEPARATOR_HEIGHT + self.SEPARATOR_MARGIN_Y * 2
            else:
                label = item
                callback = items_map.get(label)
                icon = MENU_ICONS.get(label, "")
                is_danger = label in DANGER_LABELS

                item_frame = self._create_menu_item(
                    overlay, y, label, icon, callback, is_danger, c, w)
                self._item_frames.append(item_frame)
                y += self.ITEM_HEIGHT

        # Store geometry for positioning
        self._menu_w = w
        self._menu_h = h

        # Dismiss handlers
        self._menu_window.bind('<FocusOut>', self._on_dismiss)
        self._menu_window.bind('<Escape>', lambda e: self._dismiss())
        # Bind click on canvas (empty areas) to dismiss; items handle their own clicks
        canvas.bind('<Button-1>', lambda e: self._dismiss())

    def _draw_rounded_rect(self, canvas, x1, y1, x2, y2, r, fill, outline):
        """Draw a rounded rectangle on a canvas."""
        # 4 corner ovals
        canvas.create_oval(x1, y1, x1 + r*2, y1 + r*2,
                           fill=fill, outline='', tags='bg')
        canvas.create_oval(x2 - r*2, y1, x2, y1 + r*2,
                           fill=fill, outline='', tags='bg')
        canvas.create_oval(x1, y2 - r*2, x1 + r*2, y2,
                           fill=fill, outline='', tags='bg')
        canvas.create_oval(x2 - r*2, y2 - r*2, x2, y2,
                           fill=fill, outline='', tags='bg')
        # 2 cross rectangles
        canvas.create_rectangle(x1 + r, y1, x2 - r, y2,
                               fill=fill, outline='', tags='bg')
        canvas.create_rectangle(x1, y1 + r, x2, y2 - r,
                               fill=fill, outline='', tags='bg')
        # Border arcs
        canvas.create_arc(x1, y1, x1 + r*2, y1 + r*2, start=90, extent=90,
                          style='arc', outline=outline, width=1, tags='bg')
        canvas.create_arc(x2 - r*2, y1, x2, y1 + r*2, start=0, extent=90,
                          style='arc', outline=outline, width=1, tags='bg')
        canvas.create_arc(x1, y2 - r*2, x1 + r*2, y2, start=180, extent=90,
                          style='arc', outline=outline, width=1, tags='bg')
        canvas.create_arc(x2 - r*2, y2 - r*2, x2, y2, start=270, extent=90,
                          style='arc', outline=outline, width=1, tags='bg')
        # Border lines
        canvas.create_line(x1 + r, y1, x2 - r, y1, fill=outline, tags='bg')
        canvas.create_line(x1 + r, y2, x2 - r, y2, fill=outline, tags='bg')
        canvas.create_line(x1, y1 + r, x1, y2 - r, fill=outline, tags='bg')
        canvas.create_line(x2, y1 + r, x2, y2 - r, fill=outline, tags='bg')

    def _create_menu_item(self, parent, y, label, icon, callback,
                           is_danger, c, width):
        """Create a single menu item row."""
        import tkinter as tk

        h = self.ITEM_HEIGHT
        pad_x = self.ITEM_PAD_X
        gap = self.ITEM_GAP

        if is_danger:
            fg = c['danger']
            hover_bg = c['danger_hover']
            icon_fg = c['danger']
        else:
            fg = c['fg']
            hover_bg = c['menu_hover']
            icon_fg = c['text_secondary']

        frame = tk.Frame(parent, bg=c['menu_bg'], height=h, cursor='hand2')
        frame.place(x=0, y=y, width=width, height=h)
        frame.pack_propagate(False)

        # Icon
        icon_label = tk.Label(frame, text=icon, bg=c['menu_bg'], fg=icon_fg,
                              font=('Segoe UI Emoji', 11), width=2)
        icon_label.place(x=pad_x, y=0, height=h)

        # Label
        text_label = tk.Label(frame, text=label, bg=c['menu_bg'], fg=fg,
                              font=('Microsoft YaHei', 10), anchor='w')
        text_label.place(x=pad_x + 28, y=0, height=h,
                         width=width - pad_x * 2 - 28)

        # Hover handlers
        def _on_enter(e):
            frame.configure(bg=hover_bg)
            icon_label.configure(bg=hover_bg, fg=c['accent'] if not is_danger else c['danger'])
            text_label.configure(bg=hover_bg,
                                fg=c['fg'] if not is_danger else c['danger'])

        def _on_leave(e):
            frame.configure(bg=c['menu_bg'])
            icon_label.configure(bg=c['menu_bg'], fg=icon_fg)
            text_label.configure(bg=c['menu_bg'], fg=fg)

        def _on_click(e):
            self._dismiss()
            if callback:
                # Delay callback slightly to let the window close first
                frame.after(50, callback)

        for widget in (frame, icon_label, text_label):
            widget.bind('<Enter>', _on_enter)
            widget.bind('<Leave>', _on_leave)
            widget.bind('<Button-1>', _on_click)

        return frame

    def show(self, x: int, y: int):
        """显示菜单 at screen coordinates (x, y)."""
        # Dismiss any existing menu first
        self._dismiss()
        self._dismissed = False

        self._create_menu()

        # Position: ensure menu stays on screen
        sw = self._menu_window.winfo_screenwidth()
        sh = self._menu_window.winfo_screenheight()

        mx = x
        my = y

        if mx + self._menu_w > sw:
            mx = sw - self._menu_w - 4
        if my + self._menu_h > sh:
            my = sh - self._menu_h - 4
        if mx < 0:
            mx = 4
        if my < 0:
            my = 4

        self._menu_window.geometry(f"+{mx}+{my}")
        self._menu_window.update_idletasks()

        # Grab focus for dismissal on outside click
        try:
            self._menu_window.grab_set()
            self._menu_window.focus_set()
        except Exception:
            pass

    def _dismiss(self):
        """Close the menu window."""
        if self._dismissed:
            return
        self._dismissed = True
        if self._menu_window:
            try:
                if self._menu_window.winfo_exists():
                    self._menu_window.grab_release()
                    self._menu_window.destroy()
            except Exception:
                pass
        self._menu_window = None
        self._canvas = None
        self._item_frames = []

    def _on_dismiss(self, event=None):
        """Handle focus out — dismiss menu."""
        if event and event.widget == self._menu_window:
            self._dismiss()

    def _on_settings_saved(self):
        """设置保存回调"""
        if self.on_settings_saved:
            self.on_settings_saved()

    def _quit(self):
        """退出"""
        if self.on_quit_callback:
            self.on_quit_callback()
