"""
右键菜单模块 — Windows 自定义绘制实现

使用 Toplevel + Canvas 实现圆角、悬停效果、图标和分区样式，
支持二级子菜单（AI 工具箱），匹配 meowdesk-context-menu.html 原型设计。
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
    # Menu-specific (calculated from prototype rgba values)
    'menu_bg': '#1A1A24',
    # rgba(244,132,95,0.12) blended over #1A1A24
    'menu_hover': '#2D2428',
    'separator': '#2D2D3D',
    'text_secondary': '#A8A4B8',
    'danger': '#F87171',
    # rgba(248,113,113,0.10) blended over #1A1A24
    'danger_hover': '#2C1A1F',
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
    # rgba(224,107,69,0.08) blended over #FFFFFF
    'menu_hover': '#FDF0EB',
    'separator': '#E5E0D8',
    'text_secondary': '#6B6578',
    'danger': '#D94444',
    # rgba(217,68,68,0.06) blended over #FFFFFF
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
    "\u6253\u5f00\u5bfc\u822a\u9875": "\u25CE",        # ◎  compass
    "\u6253\u5f00\u5f52\u6863\u76ee\u5f55": "\U0001F4C1",  # 📁 folder
    "\u81ea\u7531\u5bf9\u8bdd": "\U0001F4AC",            # 💬 chat
    "\u6e05\u7406\u78c1\u76d8": "\U0001F9F9",            # 🧹 broom
    "\u67e5\u770b\u65e5\u671f": "\U0001F4C5",            # 📅 calendar
    "\u5047\u671f\u63d0\u9192": "\U0001F389",            # 🎉 party
    "\u7ecf\u671f\u63d0\u9192": "\u2764",                # ❤  heart
    "\u7cfb\u7edf\u4fe1\u606f": "\U0001F4BB",            # 💻 laptop
    "\u8bbe\u7f6e": "\u2699",                            # ⚙  gear
    "\u5173\u4e8e": "\u2139",                            # ℹ  info
    "\u9000\u51fa": "\u23FB",                            # ⏻  power
    "AI \u5de5\u5177\u7bb1": "\U0001F527",              # 🔧 wrench
}

# Labels that should use danger styling
DANGER_LABELS = {"\u9000\u51fa"}  # 退出

# Right chevron for submenu trigger
SUBMENU_ARROW = "\u203A"  # ›

# Menu structure matching HTML prototype:
#   打开导航页, 打开归档目录, 自由对话
#   ───
#   AI 工具箱  ›  (submenu → 清理磁盘, 系统信息, 查看日期, 假期提醒, 经期提醒)
#   ───
#   设置, 关于
#   ───
#   退出

PROTOTYPE_ORDER = [
    "\u6253\u5f00\u5bfc\u822a\u9875",       # 打开导航页
    "\u6253\u5f00\u5f52\u6863\u76ee\u5f55",  # 打开归档目录
    "\u81ea\u7531\u5bf9\u8bdd",              # 自由对话
    None,
    "SUBMENU",
    None,
    "\u8bbe\u7f6e",                          # 设置
    "\u5173\u4e8e",                          # 关于
    None,
    "\u9000\u51fa",                          # 退出
]

SUBMENU_ITEMS = [
    "\u6e05\u7406\u78c1\u76d8",      # 清理磁盘
    "\u7cfb\u7edf\u4fe1\u606f",      # 系统信息
    "\u67e5\u770b\u65e5\u671f",      # 查看日期
    "\u5047\u671f\u63d0\u9192",      # 假期提醒
    "\u7ecf\u671f\u63d0\u9192",      # 经期提醒
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
    ITEM_GAP = 12       # gap between icon and label (prototype --item-gap)
    ITEM_PAD_X = 16     # left/right padding (prototype --item-padding)
    SUBMENU_OFFSET_X = 8  # gap between main menu and submenu panel

    def __init__(self, parent, config, window=None, agent_gateway=None,
                 on_quit_callback=None, on_settings_saved=None):
        self.parent = parent
        self.config = config
        self.window = window
        self.agent_gateway = agent_gateway
        self.on_quit_callback = on_quit_callback
        self.on_settings_saved = on_settings_saved

        self._menu_window: Optional[Any] = None
        self._submenu_window: Optional[Any] = None
        self._hide_timer = None
        self._submenu_visible = False
        self._dismissed = False
        self._colors = None
        self._items_map = {}
        self._set_expanded = None
        self._submenu_trigger_frame = None

    # ------------------------------------------------------------------
    # Build callback map from menu_actions
    # ------------------------------------------------------------------

    def _build_items_map(self):
        """Build label -> callback map from shared menu_actions module."""
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
                for prefix in ("\U0001F4AC ", "\U0001F9F9 ", "\U0001F4C5 ",
                               "\U0001F389 ", "\u2764 ", "\U0001F4BB "):
                    if clean.startswith(prefix):
                        clean = clean[len(prefix):]
                        break
                item_map[clean] = callback
        return item_map

    # ------------------------------------------------------------------
    # Height calculation
    # ------------------------------------------------------------------

    def _calc_main_height(self):
        """Calculate total height of the main menu."""
        h = self.PADDING_Y * 2
        for item in PROTOTYPE_ORDER:
            if item is None:
                h += self.SEPARATOR_HEIGHT + self.SEPARATOR_MARGIN_Y * 2
            else:
                h += self.ITEM_HEIGHT
        return h

    def _calc_submenu_height(self):
        """Calculate total height of the submenu panel."""
        h = self.PADDING_Y * 2
        for _ in SUBMENU_ITEMS:
            h += self.ITEM_HEIGHT
        return h

    # ------------------------------------------------------------------
    # Rounded rectangle drawing
    # ------------------------------------------------------------------

    @staticmethod
    def _draw_rounded_rect(canvas, x1, y1, x2, y2, r, fill, outline):
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

    # ------------------------------------------------------------------
    # Menu item creation
    # ------------------------------------------------------------------

    def _create_menu_item(self, parent, y, label, callback, is_danger, c, width):
        """Create a single menu item row with icon + label and hover effects.

        Prototype hover behavior:
          - bg changes to --hover-bg (coral-tinted)
          - icon color changes to --primary (coral)
          - label stays --text-primary
        """
        import tkinter as tk

        h = self.ITEM_HEIGHT
        pad_x = self.ITEM_PAD_X

        if is_danger:
            fg = c['danger']
            hover_bg = c['danger_hover']
            icon_fg = c['danger']
            hover_icon_fg = c['danger']
            hover_label_fg = c['danger']
        else:
            fg = c['fg']
            hover_bg = c['menu_hover']
            icon_fg = c['text_secondary']
            hover_icon_fg = c['accent']
            hover_label_fg = c['fg']

        frame = tk.Frame(parent, bg=c['menu_bg'], height=h, cursor='hand2')
        frame.place(x=0, y=y, width=width, height=h)
        frame.pack_propagate(False)

        # Icon (left aligned, 18px wide area)
        icon = MENU_ICONS.get(label, "")
        icon_label = tk.Label(frame, text=icon, bg=c['menu_bg'], fg=icon_fg,
                              font=('Segoe UI Emoji', 10), width=2, anchor='center')
        icon_label.place(x=pad_x, y=0, height=h, width=24)

        # Label (flex-1 after icon + gap)
        text_x = pad_x + 24 + self.ITEM_GAP
        text_label = tk.Label(frame, text=label, bg=c['menu_bg'], fg=fg,
                              font=('Microsoft YaHei', 10), anchor='w')
        text_label.place(x=text_x, y=0, height=h,
                         width=width - text_x - pad_x)

        # Hover handlers (matching prototype transitions)
        def _on_enter(e):
            frame.configure(bg=hover_bg)
            icon_label.configure(bg=hover_bg, fg=hover_icon_fg)
            text_label.configure(bg=hover_bg, fg=hover_label_fg)

        def _on_leave(e):
            frame.configure(bg=c['menu_bg'])
            icon_label.configure(bg=c['menu_bg'], fg=icon_fg)
            text_label.configure(bg=c['menu_bg'], fg=fg)

        def _on_click(e):
            self._dismiss_all()
            if callback:
                frame.after(50, callback)

        for widget in (frame, icon_label, text_label):
            widget.bind('<Enter>', _on_enter)
            widget.bind('<Leave>', _on_leave)
            widget.bind('<Button-1>', _on_click)

        return frame

    def _create_submenu_trigger(self, parent, y, c, width):
        """Create the 'AI 工具箱' submenu trigger item.

        Matches prototype:
          - Icon (wrench), label, right chevron arrow
          - When expanded: 3px coral left accent bar, icon/label in accent color
          - Hover: same coral-tinted background as normal items
        """
        import tkinter as tk

        h = self.ITEM_HEIGHT
        pad_x = self.ITEM_PAD_X
        hover_bg = c['menu_hover']

        frame = tk.Frame(parent, bg=c['menu_bg'], height=h, cursor='hand2')
        frame.place(x=0, y=y, width=width, height=h)
        frame.pack_propagate(False)

        # Left accent bar (3px, shown when expanded)
        accent_bar = tk.Frame(frame, width=3, bg=c['menu_bg'])
        accent_bar.place(x=0, y=6, height=h - 12)

        # Icon
        icon = MENU_ICONS.get("AI \u5de5\u5177\u7bb1", "\U0001F527")
        icon_label = tk.Label(frame, text=icon, bg=c['menu_bg'],
                              fg=c['text_secondary'],
                              font=('Segoe UI Emoji', 10), width=2, anchor='center')
        icon_label.place(x=pad_x, y=0, height=h, width=24)

        # Label
        text_x = pad_x + 24 + self.ITEM_GAP
        text_label = tk.Label(frame, text="AI \u5de5\u5177\u7bb1",
                              bg=c['menu_bg'], fg=c['fg'],
                              font=('Microsoft YaHei', 10), anchor='w')
        text_label.place(x=text_x, y=0, height=h,
                         width=width - text_x - pad_x - 24)

        # Right chevron arrow
        arrow_label = tk.Label(frame, text=SUBMENU_ARROW, bg=c['menu_bg'],
                               fg=c['text_muted'],
                               font=('Microsoft YaHei', 14, 'bold'), anchor='center')
        arrow_label.place(x=width - pad_x - 16, y=0, height=h, width=16)

        def _set_expanded(expanded):
            """Toggle the expanded visual state."""
            if expanded:
                accent_bar.configure(bg=c['accent'])
                icon_label.configure(fg=c['accent'])
                text_label.configure(fg=c['accent_hover'])
                arrow_label.configure(fg=c['accent'])
            else:
                accent_bar.configure(bg=c['menu_bg'])
                icon_label.configure(fg=c['text_secondary'])
                text_label.configure(fg=c['fg'])
                arrow_label.configure(fg=c['text_muted'])

        # Hover handlers
        def _on_enter(e):
            frame.configure(bg=hover_bg)
            icon_label.configure(bg=hover_bg)
            text_label.configure(bg=hover_bg)
            arrow_label.configure(bg=hover_bg)
            accent_bar.configure(bg=c['accent'] if self._submenu_visible else hover_bg)
            if not self._submenu_visible:
                self._show_submenu(y)

        def _on_leave(e):
            frame.configure(bg=c['menu_bg'])
            icon_label.configure(bg=c['menu_bg'])
            text_label.configure(bg=c['menu_bg'])
            arrow_label.configure(bg=c['menu_bg'])
            accent_bar.configure(bg=c['accent'] if self._submenu_visible else c['menu_bg'])
            if self._submenu_visible:
                self._schedule_hide_submenu()

        for widget in (frame, icon_label, text_label, arrow_label):
            widget.bind('<Enter>', _on_enter)
            widget.bind('<Leave>', _on_leave)

        self._submenu_trigger_frame = frame
        self._set_expanded = _set_expanded
        return frame

    # ------------------------------------------------------------------
    # Submenu panel
    # ------------------------------------------------------------------

    def _create_submenu_window(self, trigger_screen_y):
        """Create the submenu panel as a separate Toplevel window."""
        import tkinter as tk

        c = self._colors
        w = self.MENU_WIDTH
        h = self._calc_submenu_height()
        r = self.RADIUS

        sub = tk.Toplevel(self.parent)
        sub.overrideredirect(True)
        sub.configure(bg=c['menu_bg'])
        sub.attributes('-topmost', True)
        try:
            sub.attributes('-alpha', 0.95)
        except Exception:
            pass

        # Canvas for rounded background
        canvas = tk.Canvas(sub, width=w, height=h,
                           bg=c['menu_bg'], highlightthickness=0, bd=0)
        canvas.pack(fill='both', expand=True)
        self._draw_rounded_rect(canvas, 0, 0, w, h, r, c['menu_bg'], c['border'])

        # Overlay frame for items
        overlay = tk.Frame(canvas, bg=c['menu_bg'])
        canvas.create_window((0, 0), window=overlay, anchor='nw', tags='sub-overlay')

        def _resize(event):
            canvas.itemconfigure('sub-overlay', width=w, height=h)
        canvas.bind('<Configure>', _resize)

        # Build submenu items
        y = self.PADDING_Y
        for label in SUBMENU_ITEMS:
            callback = self._items_map.get(label)
            is_danger = label in DANGER_LABELS
            self._create_menu_item(overlay, y, label, callback, is_danger, c, w)
            y += self.ITEM_HEIGHT

        # Position: right of main menu, aligned to trigger item
        main_x = self._menu_window.winfo_rootx()
        main_w = self._menu_window.winfo_width()
        sx = main_x + main_w + self.SUBMENU_OFFSET_X
        sy = trigger_screen_y

        # Screen edge check
        sw = sub.winfo_screenwidth()
        sh = sub.winfo_screenheight()
        if sx + w > sw:
            # Place to the left of the main menu instead
            sx = main_x - w - self.SUBMENU_OFFSET_X
        if sy + h > sh:
            sy = sh - h - 4
        if sy < 0:
            sy = 4

        sub.geometry(f"{w}x{h}+{sx}+{sy}")

        # Hover handlers on submenu panel: cancel hide timer
        def _sub_enter(e):
            self._cancel_hide_timer()

        def _sub_leave(e):
            self._schedule_hide_submenu()

        sub.bind('<Enter>', _sub_enter)
        sub.bind('<Leave>', _sub_leave)

        # Click on empty canvas area dismisses everything
        canvas.bind('<Button-1>', lambda e: self._dismiss_all())

        self._submenu_window = sub
        self._submenu_visible = True
        if self._set_expanded:
            self._set_expanded(True)

    def _show_submenu(self, trigger_y):
        """Show the submenu panel aligned to the trigger item."""
        self._cancel_hide_timer()
        if self._submenu_visible:
            return
        # Calculate screen Y of the trigger item
        trigger_screen_y = (self._menu_window.winfo_rooty()
                            + trigger_y)
        self._create_submenu_window(trigger_screen_y)

    def _hide_submenu(self):
        """Hide the submenu panel."""
        if not self._submenu_visible:
            return
        self._submenu_visible = False
        if self._set_expanded:
            self._set_expanded(False)
        if self._submenu_window:
            try:
                if self._submenu_window.winfo_exists():
                    self._submenu_window.destroy()
            except Exception:
                pass
        self._submenu_window = None

    def _schedule_hide_submenu(self):
        """Schedule hidinging the submenu after a short delay (200ms)."""
        self._cancel_hide_timer()
        if self._submenu_window and self._submenu_window.winfo_exists():
            self._hide_timer = self._submenu_window.after(
                200, self._hide_submenu)

    def _cancel_hide_timer(self):
        """Cancel any pending submenu hide timer."""
        if self._hide_timer is not None:
            try:
                if self._submenu_window and self._submenu_window.winfo_exists():
                    self._submenu_window.after_cancel(self._hide_timer)
            except Exception:
                pass
            self._hide_timer = None

    # ------------------------------------------------------------------
    # Main menu creation
    # ------------------------------------------------------------------

    def _create_menu(self):
        """Create the main menu window."""
        import tkinter as tk

        c = resolve_colors(getattr(self.config, 'config', self.config))
        self._colors = c
        self._items_map = self._build_items_map()

        # Create borderless window
        self._menu_window = tk.Toplevel(self.parent)
        self._menu_window.overrideredirect(True)
        self._menu_window.configure(bg=c['menu_bg'])
        self._menu_window.attributes('-topmost', True)
        try:
            self._menu_window.attributes('-alpha', 0.95)
        except Exception:
            pass

        w = self.MENU_WIDTH
        h = self._calc_main_height()
        r = self.RADIUS

        # Canvas for rounded background
        canvas = tk.Canvas(self._menu_window, width=w, height=h,
                           bg=c['menu_bg'], highlightthickness=0, bd=0)
        canvas.pack(fill='both', expand=True)
        self._draw_rounded_rect(canvas, 0, 0, w, h, r, c['menu_bg'], c['border'])

        # Overlay frame for menu items
        overlay = tk.Frame(canvas, bg=c['menu_bg'])
        canvas.create_window((0, 0), window=overlay, anchor='nw', tags='overlay')

        def _resize_overlay(event):
            canvas.itemconfigure('overlay', width=w, height=h)
        canvas.bind('<Configure>', _resize_overlay)

        # Build menu items
        y = self.PADDING_Y
        self._submenu_trigger_y = None

        for item in PROTOTYPE_ORDER:
            if item is None:
                # Separator
                sep_y = y + self.SEPARATOR_MARGIN_Y
                sep_frame = tk.Frame(overlay, height=1, bg=c['separator'])
                sep_frame.place(x=self.SEPARATOR_MARGIN_X, y=sep_y,
                                width=w - self.SEPARATOR_MARGIN_X * 2, height=1)
                y += self.SEPARATOR_HEIGHT + self.SEPARATOR_MARGIN_Y * 2
            elif item == "SUBMENU":
                # AI toolbox submenu trigger
                self._submenu_trigger_y = y
                self._create_submenu_trigger(overlay, y, c, w)
                y += self.ITEM_HEIGHT
            else:
                label = item
                callback = self._items_map.get(label)
                is_danger = label in DANGER_LABELS
                self._create_menu_item(overlay, y, label, callback, is_danger, c, w)
                y += self.ITEM_HEIGHT

        # Store geometry
        self._menu_w = w
        self._menu_h = h

        # Dismiss handlers
        self._menu_window.bind('<FocusOut>', self._on_focus_out)
        self._menu_window.bind('<Escape>', lambda e: self._dismiss_all())
        # Click on empty canvas area dismisses
        canvas.bind('<Button-1>', lambda e: self._dismiss_all())

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show(self, x: int, y: int):
        """显示菜单 at screen coordinates (x, y)."""
        # Dismiss any existing menu first
        self._dismiss_all()
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

    # ------------------------------------------------------------------
    # Dismiss logic
    # ------------------------------------------------------------------

    def _dismiss_all(self):
        """Close both the main menu and submenu."""
        if self._dismissed:
            return
        self._dismissed = True
        self._hide_submenu()
        if self._menu_window:
            try:
                if self._menu_window.winfo_exists():
                    self._menu_window.grab_release()
                    self._menu_window.destroy()
            except Exception:
                pass
        self._menu_window = None

    def _on_focus_out(self, event=None):
        """Handle focus out — dismiss all menus."""
        # Only dismiss if focus goes to a non-submenu window
        if event and event.widget == self._menu_window:
            # Small delay to allow submenu window to grab focus
            if self._submenu_visible:
                self._schedule_hide_submenu()
            else:
                self._dismiss_all()

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_settings_saved(self):
        """设置保存回调"""
        if self.on_settings_saved:
            self.on_settings_saved()

    def _quit(self):
        """退出"""
        if self.on_quit_callback:
            self.on_quit_callback()
