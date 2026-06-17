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
# Canvas-drawn icon functions (matching prototype SVG stroke icons)
# Each draws on an 18x18 canvas with ~1.5px stroke, tagged 'icon' for hover
# ---------------------------------------------------------------------------
_SW = 1.5  # stroke width matching prototype stroke-width: 1.5


def _icon_compass(cv, color):
    """打开导航页 — circle + 4 cardinal ticks + diamond needle."""
    cv.create_oval(2, 2, 16, 16, outline=color, width=_SW, tags='icon')
    cv.create_line(9, 2, 9, 4, fill=color, width=_SW, tags='icon')
    cv.create_line(9, 14, 9, 16, fill=color, width=_SW, tags='icon')
    cv.create_line(2, 9, 4, 9, fill=color, width=_SW, tags='icon')
    cv.create_line(14, 9, 16, 9, fill=color, width=_SW, tags='icon')
    cv.create_line(9, 5, 11, 9, 9, 13, 7, 9, 9, 5,
                   fill=color, width=1, tags='icon')


def _icon_folder(cv, color):
    """打开归档目录 — folder outline with tab."""
    pts = [
        (2, 6), (2, 4), (7, 4), (9, 6),
        (16, 6), (16, 15), (2, 15),
    ]
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        cv.create_line(x1, y1, x2, y2, fill=color, width=_SW, tags='icon')


def _icon_chat(cv, color):
    """自由对话 — chat bubble with tail."""
    cv.create_oval(2, 2, 16, 14, fill=cv['bg'], outline='', tags='icon_bg')
    cv.create_polygon(2, 11, 6, 11, 3, 16, fill=cv['bg'], outline='', tags='icon_bg')
    cv.create_polygon(2, 11, 6, 11, 3, 16, outline=color, fill='', tags='icon')
    cv.create_oval(2, 2, 16, 14, outline=color, width=_SW, tags='icon')


def _icon_wrench(cv, color):
    """AI 工具箱 — wrench silhouette."""
    cv.create_line(4, 14, 11, 7, fill=color, width=2, capstyle='round', tags='icon')
    cv.create_arc(7, 2, 16, 11, start=45, extent=270, style='arc',
                  outline=color, width=_SW, tags='icon')
    cv.create_line(3, 13, 5, 15, fill=color, width=2, capstyle='round', tags='icon')


def _icon_rocket(cv, color):
    """清理磁盘 — upward arrow with base line and exhaust."""
    cv.create_line(9, 3, 9, 14, fill=color, width=_SW, tags='icon')
    cv.create_line(5, 7, 9, 3, 13, 7, fill=color, width=_SW,
                   capstyle='round', joinstyle='round', tags='icon')
    cv.create_line(3, 16, 15, 16, fill=color, width=_SW, tags='icon')
    cv.create_line(6, 12, 4, 16, fill=color, width=1, tags='icon')
    cv.create_line(12, 12, 14, 16, fill=color, width=1, tags='icon')


def _icon_monitor(cv, color):
    """系统信息 — monitor screen with stand."""
    cv.create_rectangle(2, 3, 16, 12, outline=color, width=_SW, tags='icon')
    cv.create_line(9, 12, 9, 15, fill=color, width=_SW, tags='icon')
    cv.create_line(6, 15, 12, 15, fill=color, width=_SW, tags='icon')
    cv.create_line(5, 6, 8, 6, fill=color, width=1, tags='icon')
    cv.create_line(10, 6, 13, 6, fill=color, width=1, tags='icon')
    cv.create_line(5, 9, 13, 9, fill=color, width=1, tags='icon')


def _icon_calendar(cv, color):
    """查看日期 — calendar grid."""
    cv.create_rectangle(3, 4, 15, 16, outline=color, width=_SW, tags='icon')
    cv.create_line(12, 2, 12, 6, fill=color, width=_SW, tags='icon')
    cv.create_line(6, 2, 6, 6, fill=color, width=_SW, tags='icon')
    cv.create_line(3, 8, 15, 8, fill=color, width=1, tags='icon')
    for x in (6, 9, 12):
        for y in (10, 13):
            cv.create_line(x, y, x + 1, y, fill=color, width=1.5, tags='icon')


def _icon_fireworks(cv, color):
    """假期提醒 — sparkle burst."""
    cv.create_line(12, 13, 2, 20, fill=color, width=_SW, tags='icon')
    cv.create_line(16, 2, 8, 10, fill=color, width=1, tags='icon')
    cv.create_line(12, 5, 10, 7, fill=color, width=1, tags='icon')
    cv.create_line(16, 11, 14, 13, fill=color, width=1, tags='icon')
    for cx, cy in [(4, 3), (16, 7), (9, 1), (16, 15)]:
        cv.create_line(cx - 1, cy, cx + 1, cy, fill=color, width=1, tags='icon')
        cv.create_line(cx, cy - 1, cx, cy + 1, fill=color, width=1, tags='icon')


def _icon_heart(cv, color):
    """经期提醒 — heart shape."""
    cv.create_line(
        9, 7, 7, 5, 5, 4, 4, 5, 3, 6, 3, 8, 3, 10,
        5, 12, 7, 14, 9, 16,
        11, 14, 13, 12, 15, 10, 15, 8, 15, 6, 14, 5,
        13, 4, 11, 5, 9, 7,
        fill=color, width=_SW, smooth=True, joinstyle='round', tags='icon',
    )


def _icon_gear(cv, color):
    """设置 — gear with center hole and teeth."""
    import math
    cv.create_oval(7, 7, 11, 11, outline=color, width=_SW, tags='icon')
    cx, cy = 9, 9
    r_out, r_in = 8, 6
    for i in range(8):
        base = math.radians(i * 45)
        half = math.radians(12)
        a1 = base - half
        a2 = base + half
        cv.create_arc(cx - r_out, cy - r_out, cx + r_out, cy + r_out,
                      start=math.degrees(a1), extent=math.degrees(a2 - a1),
                      style='arc', outline=color, width=_SW, tags='icon')
        ix1 = cx + r_out * math.cos(a1)
        iy1 = cy - r_out * math.sin(a1)
        ix2 = cx + r_in * math.cos(a1)
        iy2 = cy - r_in * math.sin(a1)
        cv.create_line(ix1, iy1, ix2, iy2, fill=color, width=_SW, tags='icon')
        ox1 = cx + r_out * math.cos(a2)
        oy1 = cy - r_out * math.sin(a2)
        ix3 = cx + r_in * math.cos(a2)
        iy3 = cy - r_in * math.sin(a2)
        cv.create_line(ox1, oy1, ix3, iy3, fill=color, width=_SW, tags='icon')
        gap_end = math.radians((i + 1) * 45 - 12)
        gx = cx + r_in * math.cos(gap_end)
        gy = cy - r_in * math.sin(gap_end)
        cv.create_line(ix3, iy3, gx, gy, fill=color, width=1, tags='icon')


def _icon_info(cv, color):
    """关于 — circle with i."""
    cv.create_oval(1, 1, 17, 17, outline=color, width=_SW, tags='icon')
    cv.create_line(9, 8, 9, 13, fill=color, width=_SW, tags='icon')
    cv.create_line(9, 6, 9, 6.5, fill=color, width=2, capstyle='round', tags='icon')


def _icon_power(cv, color):
    """退出 — power symbol."""
    cv.create_arc(3, 4, 15, 16, start=30, extent=120, style='arc',
                  outline=color, width=_SW, tags='icon')
    cv.create_line(9, 2, 9, 9, fill=color, width=_SW, tags='icon')


def _icon_arrow_right(cv, color):
    """子菜单右箭头 chevron."""
    cv.create_line(5, 4, 11, 9, 5, 14, fill=color, width=_SW,
                   capstyle='round', joinstyle='round', tags='icon')


# Label → drawing function mapping
ICON_DRAWERS = {
    "打开导航页": _icon_compass,
    "打开归档目录": _icon_folder,
    "自由对话": _icon_chat,
    "清理磁盘": _icon_rocket,
    "查看日期": _icon_calendar,
    "假期提醒": _icon_fireworks,
    "经期提醒": _icon_heart,
    "系统信息": _icon_monitor,
    "设置": _icon_gear,
    "关于": _icon_info,
    "退出": _icon_power,
    "AI 工具箱": _icon_wrench,
}

# Labels that should use danger styling
DANGER_LABELS = {"\u9000\u51fa"}  # 退出

# Right chevron for submenu trigger → drawn via _icon_arrow_right()

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
        """Create a single menu item row with Canvas-drawn icon + label.

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

        # Icon area: 18x18 Canvas, centered vertically in the 40px row
        icon_size = 18
        icon_canvas = tk.Canvas(frame, width=icon_size, height=icon_size,
                                bg=c['menu_bg'], highlightthickness=0, bd=0)
        icon_canvas.place(x=pad_x, y=(h - icon_size) // 2)

        # Store menu bg for icon bg fills (used by chat bubble etc.)
        icon_canvas['bg'] = c['menu_bg']
        # Draw the icon
        draw_fn = ICON_DRAWERS.get(label)
        if draw_fn:
            draw_fn(icon_canvas, icon_fg)

        # Label (flex-1 after icon + gap)
        text_x = pad_x + icon_size + self.ITEM_GAP
        text_label = tk.Label(frame, text=label, bg=c['menu_bg'], fg=fg,
                              font=('Microsoft YaHei', 10), anchor='w')
        text_label.place(x=text_x, y=0, height=h,
                         width=width - text_x - pad_x)

        # Hover handlers (matching prototype transitions)
        def _on_enter(e):
            frame.configure(bg=hover_bg)
            icon_canvas.configure(bg=hover_bg)
            # Update stroke colors on all icon items
            for item_id in icon_canvas.find_withtag('icon'):
                icon_canvas.itemconfigure(item_id, outline=hover_icon_fg, fill=hover_icon_fg)
            # Also update bg-fill items to match new hover bg
            for item_id in icon_canvas.find_withtag('icon_bg'):
                icon_canvas.itemconfigure(item_id, fill=hover_bg)
            text_label.configure(bg=hover_bg, fg=hover_label_fg)

        def _on_leave(e):
            frame.configure(bg=c['menu_bg'])
            icon_canvas.configure(bg=c['menu_bg'])
            for item_id in icon_canvas.find_withtag('icon'):
                icon_canvas.itemconfigure(item_id, outline=icon_fg, fill=icon_fg)
            for item_id in icon_canvas.find_withtag('icon_bg'):
                icon_canvas.itemconfigure(item_id, fill=c['menu_bg'])
            text_label.configure(bg=c['menu_bg'], fg=fg)

        def _on_click(e):
            self._dismiss_all()
            if callback:
                frame.after(50, callback)

        for widget in (frame, icon_canvas, text_label):
            widget.bind('<Enter>', _on_enter)
            widget.bind('<Leave>', _on_leave)
            widget.bind('<Button-1>', _on_click)

        return frame

    def _create_submenu_trigger(self, parent, y, c, width):
        """Create the 'AI 工具箱' submenu trigger item.

        Matches prototype:
          - Canvas icon (wrench), label, Canvas right chevron arrow
          - When expanded: 3px coral left accent bar, icon/label in accent color
          - Hover: same coral-tinted background as normal items
        """
        import tkinter as tk

        h = self.ITEM_HEIGHT
        pad_x = self.ITEM_PAD_X
        hover_bg = c['menu_hover']
        icon_size = 18

        frame = tk.Frame(parent, bg=c['menu_bg'], height=h, cursor='hand2')
        frame.place(x=0, y=y, width=width, height=h)
        frame.pack_propagate(False)

        # Left accent bar (3px, shown when expanded)
        accent_bar = tk.Frame(frame, width=3, bg=c['menu_bg'])
        accent_bar.place(x=0, y=6, height=h - 12)

        # Icon canvas (wrench)
        icon_canvas = tk.Canvas(frame, width=icon_size, height=icon_size,
                                bg=c['menu_bg'], highlightthickness=0, bd=0)
        icon_canvas.place(x=pad_x, y=(h - icon_size) // 2)
        icon_canvas['bg'] = c['menu_bg']
        _icon_wrench(icon_canvas, c['text_secondary'])

        # Label
        text_x = pad_x + icon_size + self.ITEM_GAP
        text_label = tk.Label(frame, text="AI 工具箱",
                              bg=c['menu_bg'], fg=c['fg'],
                              font=('Microsoft YaHei', 10), anchor='w')
        text_label.place(x=text_x, y=0, height=h,
                         width=width - text_x - pad_x - 24)

        # Right chevron arrow canvas
        arrow_size = 14
        arrow_canvas = tk.Canvas(frame, width=arrow_size, height=arrow_size,
                                 bg=c['menu_bg'], highlightthickness=0, bd=0)
        arrow_canvas.place(x=width - pad_x - arrow_size, y=(h - arrow_size) // 2)
        arrow_canvas['bg'] = c['menu_bg']
        _icon_arrow_right(arrow_canvas, c['text_muted'])

        def _set_icon_color(color):
            """Update icon canvas stroke colors."""
            for item_id in icon_canvas.find_withtag('icon'):
                icon_canvas.itemconfigure(item_id, outline=color, fill=color)

        def _set_arrow_color(color):
            """Update arrow canvas stroke colors."""
            for item_id in arrow_canvas.find_withtag('icon'):
                arrow_canvas.itemconfigure(item_id, outline=color, fill=color)

        def _set_expanded(expanded):
            """Toggle the expanded visual state."""
            if expanded:
                accent_bar.configure(bg=c['accent'])
                _set_icon_color(c['accent'])
                text_label.configure(fg=c['accent_hover'])
                _set_arrow_color(c['accent'])
            else:
                accent_bar.configure(bg=c['menu_bg'])
                _set_icon_color(c['text_secondary'])
                text_label.configure(fg=c['fg'])
                _set_arrow_color(c['text_muted'])

        # Hover handlers
        def _on_enter(e):
            frame.configure(bg=hover_bg)
            icon_canvas.configure(bg=hover_bg)
            text_label.configure(bg=hover_bg)
            arrow_canvas.configure(bg=hover_bg)
            if not self._submenu_visible:
                _set_icon_color(c['accent'])
                _set_arrow_color(c['accent'])
            accent_bar.configure(bg=c['accent'] if self._submenu_visible else hover_bg)
            if not self._submenu_visible:
                self._show_submenu(y)

        def _on_leave(e):
            frame.configure(bg=c['menu_bg'])
            icon_canvas.configure(bg=c['menu_bg'])
            text_label.configure(bg=c['menu_bg'])
            arrow_canvas.configure(bg=c['menu_bg'])
            if not self._submenu_visible:
                _set_icon_color(c['text_secondary'])
                _set_arrow_color(c['text_muted'])
            accent_bar.configure(bg=c['accent'] if self._submenu_visible else c['menu_bg'])
            if self._submenu_visible:
                self._schedule_hide_submenu()

        for widget in (frame, icon_canvas, text_label, arrow_canvas):
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
