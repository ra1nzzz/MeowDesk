"""
右键菜单模块 — Windows 自定义绘制实现

使用 Toplevel + Canvas 实现圆角、悬停效果、图标和分区样式，
支持二级子菜单（工具箱），匹配 meowdesk-context-menu.html 原型设计。

图标使用 PIL 超采样渲染（4x → 18×18 LANCZOS），确保抗锯齿质量。
"""

import sys
import math
import re
from typing import Any, Optional

from PIL import Image, ImageDraw


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
    'menu_bg': '#1A1A24',
    'menu_hover': '#2D2428',
    'separator': '#2D2D3D',
    'text_secondary': '#A8A4B8',
    'danger': '#F87171',
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
    'menu_bg': '#FFFFFF',
    'menu_hover': '#FDF0EB',
    'separator': '#E5E0D8',
    'text_secondary': '#6B6578',
    'danger': '#D94444',
    'danger_hover': '#FDE8E8',
}


def _is_windows_dark_mode() -> bool:
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return int(value) == 0
    except Exception:
        return True


def resolve_colors(config=None) -> dict:
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
# Icon SVG data — exact paths from meowdesk-context-menu.html prototype.
# viewBox 0 0 24 24, rendered at 18×18 via PIL supersampling (4× → LANCZOS).
# ---------------------------------------------------------------------------

ICON_DATA = {
    "打开导航页": [
        ('circle', 12, 12, 9),
        ('path', 'M12 3v2 M12 19v2 M3 12h2 M19 12h2'),
        ('path', 'M12 8l2 4-2 4-2-4z'),
    ],
    "打开归档目录": [
        ('path',
         'M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8'
         'a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z'),
    ],
    "自由对话": [
        ('path',
         'M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7'
         ' 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7'
         'a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6'
         ' 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z'),
    ],
    "工具箱": [
        ('path',
         'M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0'
         'l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91'
         'a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94'
         'l-3.76 3.76z'),
    ],
    "清理磁盘": [
        ('path', 'M12 19V5 M5 12l7-7 7 7 M3 21h18'),
        ('path', 'M8 17l-2 4 M16 17l2 4'),
        ('path', 'M7 3v3 M17 3v3'),
    ],
    "系统信息": [
        ('rect', 2, 3, 20, 14, 2),
        ('path', 'M8 21h8 M12 17v4'),
        ('path', 'M7 10h2 M15 10h2 M7 7h10'),
    ],
    "查看日期": [
        ('rect', 3, 4, 18, 18, 2),
        ('path',
         'M16 2v4 M8 2v4 M3 10h18'
         ' M8 14h.01 M12 14h.01 M16 14h.01'
         ' M8 18h.01 M12 18h.01'),
    ],
    "假期提醒": [
        ('path', 'M5.8 11.3L2 22l10.7-3.8'),
        ('path', 'M22 2L12 12'),
        ('path', 'M16 8l-4-4 M9 3L7.5 4.5 M20 13l1.5-1.5'),
        ('path', 'M4 3h.01 M22 8h.01 M15 2h.01 M22 20h.01'),
    ],
    "经期提醒": [
        ('path',
         'M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06'
         'a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78'
         ' 1.06-1.06a5.5 5.5 0 0 0 0-7.78z'),
    ],
    "设置": [
        ('circle', 12, 12, 3),
        ('path',
         'M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06'
         'a2 2 0 1 1-2.83 2.83l-.06-.06'
         'a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21'
         'a2 2 0 0 1-4 0v-.09'
         'a1.65 1.65 0 0 0-1.08-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06'
         'a2 2 0 1 1-2.83-2.83l.06-.06'
         'a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3'
         'a2 2 0 0 1 0-4h.09'
         'a1.65 1.65 0 0 0 1.51-1.08 1.65 1.65 0 0 0-.33-1.82l-.06-.06'
         'a2 2 0 1 1 2.83-2.83l.06.06'
         'a1.65 1.65 0 0 0 1.82.33H9'
         'a1.65 1.65 0 0 0 1-1.51V3'
         'a2 2 0 0 1 4 0v.09'
         'a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06'
         'a2 2 0 1 1 2.83 2.83l-.06.06'
         'a1.65 1.65 0 0 0-.33 1.82V9'
         'a1.65 1.65 0 0 0 1.51 1H21'
         'a2 2 0 0 1 0 4h-.09'
         'a1.65 1.65 0 0 0-1.51 1z'),
    ],
    "关于": [
        ('circle', 12, 12, 10),
        ('path', 'M12 16v-4 M12 8h.01'),
    ],
    "退出": [
        ('path', 'M18.36 6.64a9 9 0 1 1-12.73 0'),
        ('path', 'M12 2v10'),
    ],
}

_CHEVRON_RIGHT = [('polyline', [9, 18, 15, 12, 9, 6])]


# ---------------------------------------------------------------------------
# SVG path parser  (M/L/H/V/C/A/Z → coordinate commands)
# ---------------------------------------------------------------------------

def _resplit_path(d: str) -> list:
    """Robust SVG path parser using regex tokenisation."""
    tokens = re.findall(
        r'[MmLlHhVvCcSsAaZz]|-?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?', d)

    cmds = []
    i = 0
    cx, cy = 0.0, 0.0

    def _num():
        nonlocal i
        val = float(tokens[i])
        i += 1
        return val

    while i < len(tokens):
        t = tokens[i]
        if t in 'Mm':
            i += 1
            x, y = _num(), _num()
            if t == 'm':
                x += cx; y += cy
            cmds.append(('M', x, y))
            cx, cy = x, y
            while i < len(tokens) and not tokens[i].isalpha():
                x, y = _num(), _num()
                if t == 'm':
                    x += cx; y += cy
                cmds.append(('L', x, y))
                cx, cy = x, y
        elif t in 'Ll':
            i += 1
            while i < len(tokens) and not tokens[i].isalpha():
                x, y = _num(), _num()
                if t == 'l':
                    x += cx; y += cy
                cmds.append(('L', x, y))
                cx, cy = x, y
        elif t in 'Hh':
            i += 1
            while i < len(tokens) and not tokens[i].isalpha():
                x = _num()
                if t == 'h':
                    x += cx
                cmds.append(('L', x, cy))
                cx = x
        elif t in 'Vv':
            i += 1
            while i < len(tokens) and not tokens[i].isalpha():
                y = _num()
                if t == 'v':
                    y += cy
                cmds.append(('L', cx, y))
                cy = y
        elif t in 'Cc':
            i += 1
            while i + 5 < len(tokens) and not tokens[i].isalpha():
                x1, y1 = _num(), _num()
                x2, y2 = _num(), _num()
                x, y = _num(), _num()
                if t == 'c':
                    x1 += cx; y1 += cy; x2 += cx; y2 += cy
                    x += cx; y += cy
                cmds.append(('C', x1, y1, x2, y2, x, y))
                cx, cy = x, y
        elif t in 'Aa':
            i += 1
            while i + 6 < len(tokens) and not tokens[i].isalpha():
                rx = _num(); ry = _num(); rot = _num()
                la = _num(); sw = _num()
                x, y = _num(), _num()
                if t == 'a':
                    x += cx; y += cy
                cmds.append(('A', rx, ry, rot, la, sw, x, y))
                cx, cy = x, y
        elif t in 'Zz':
            i += 1
            cmds.append(('Z',))
        else:
            i += 1

    return cmds


# ---------------------------------------------------------------------------
# SVG arc → sampled points (avoids PIL arc() angle parameterization issues)
# ---------------------------------------------------------------------------

def _sample_svg_arc(rx, ry, rot, large_arc, sweep, x1, y1, x2, y2, n=64):
    """Sample *n* points along an SVG arc.  Returns list of (x, y)."""
    if rx == 0 or ry == 0:
        return [(x1, y1), (x2, y2)]

    rx, ry = abs(rx), abs(ry)
    phi = math.radians(rot)
    cos_p, sin_p = math.cos(phi), math.sin(phi)

    dx = (x1 - x2) / 2
    dy = (y1 - y2) / 2
    x1p = cos_p * dx + sin_p * dy
    y1p = -sin_p * dx + cos_p * dy

    lam = (x1p / rx) ** 2 + (y1p / ry) ** 2
    if lam > 1:
        s = math.sqrt(lam)
        rx *= s
        ry *= s

    num = max(0, rx ** 2 * ry ** 2 - rx ** 2 * y1p ** 2 - ry ** 2 * x1p ** 2)
    den = rx ** 2 * y1p ** 2 + ry ** 2 * x1p ** 2
    sq = math.sqrt(num / den) if den > 0 else 0
    if large_arc == sweep:
        sq = -sq

    cxp = sq * rx * y1p / ry
    cyp = -sq * ry * x1p / rx
    cx = cos_p * cxp - sin_p * cyp + (x1 + x2) / 2
    cy = sin_p * cxp + cos_p * cyp + (y1 + y2) / 2

    def _angle(ux, uy, vx, vy):
        dot = ux * vx + uy * vy
        nm = math.sqrt(ux ** 2 + uy ** 2) * math.sqrt(vx ** 2 + vy ** 2)
        c = max(-1, min(1, dot / nm)) if nm > 0 else 1
        a = math.acos(c)
        if ux * vy - uy * vx < 0:
            a = -a
        return a

    theta1 = _angle(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dtheta = _angle(
        (x1p - cxp) / rx, (y1p - cyp) / ry,
        (-x1p - cxp) / rx, (-y1p - cyp) / ry)

    if sweep and dtheta < 0:
        dtheta += 2 * math.pi
    elif not sweep and dtheta > 0:
        dtheta -= 2 * math.pi

    points = []
    for i in range(n + 1):
        t = theta1 + dtheta * i / n
        xp = rx * math.cos(t)
        yp = ry * math.sin(t)
        x = cos_p * xp - sin_p * yp + cx
        y = sin_p * xp + cos_p * yp + cy
        points.append((x, y))
    return points


# ---------------------------------------------------------------------------
# PIL icon renderer  (4× supersampling → LANCZOS downscale)
# ---------------------------------------------------------------------------

_IC_SCALE = 8
_IC_SIZE = 18
_IC_RENDER = _IC_SIZE * _IC_SCALE   # 144 px render buffer
_IC_SW = 1.5 * _IC_SCALE            # 12 px stroke at render resolution


def _pil_draw_path(draw, d, scale, color, width):
    """Render an SVG path string onto a PIL ImageDraw context."""
    cmds = _resplit_path(d)
    cur_x, cur_y = 0.0, 0.0
    start_x, start_y = 0.0, 0.0

    def tx(x):
        return x * scale

    def ty(y):
        return y * scale

    w = int(round(width))
    for cmd in cmds:
        if cmd[0] == 'M':
            cur_x, cur_y = cmd[1], cmd[2]
            start_x, start_y = cur_x, cur_y
        elif cmd[0] == 'L':
            draw.line([(tx(cur_x), ty(cur_y)),
                        (tx(cmd[1]), ty(cmd[2]))],
                      fill=color, width=w)
            cur_x, cur_y = cmd[1], cmd[2]
        elif cmd[0] == 'C':
            pts = []
            for j in range(17):
                t = j / 16
                mt = 1 - t
                bx = (mt ** 3 * cur_x + 3 * mt ** 2 * t * cmd[1]
                       + 3 * mt * t ** 2 * cmd[3] + t ** 3 * cmd[5])
                by = (mt ** 3 * cur_y + 3 * mt ** 2 * t * cmd[2]
                       + 3 * mt * t ** 2 * cmd[4] + t ** 3 * cmd[6])
                pts.append((tx(bx), ty(by)))
            if len(pts) >= 2:
                draw.line(pts, fill=color, width=w, joint='curve')
            cur_x, cur_y = cmd[5], cmd[6]
        elif cmd[0] == 'A':
            arc_pts = _sample_svg_arc(
                cmd[1], cmd[2], cmd[3], cmd[4], cmd[5],
                cur_x, cur_y, cmd[6], cmd[7])
            if arc_pts:
                scaled = [(tx(p[0]), ty(p[1])) for p in arc_pts]
                draw.line(scaled, fill=color, width=w, joint='curve')
            cur_x, cur_y = cmd[6], cmd[7]
        elif cmd[0] == 'Z':
            if (abs(cur_x - start_x) > 0.01
                    or abs(cur_y - start_y) > 0.01):
                draw.line([(tx(cur_x), ty(cur_y)),
                            (tx(start_x), ty(start_y))],
                          fill=color, width=w)
            cur_x, cur_y = start_x, start_y


def _pil_render_elements(elements, color, bg_color,
                         size=_IC_RENDER, sw=_IC_SW):
    """Render SVG element list to a PIL RGBA Image at high resolution.

    The rendered strokes are composited onto *bg_color* so that
    transparent areas become the menu surface colour (not black).
    """
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    scale = size / 24.0

    for elem in elements:
        etype = elem[0]
        if etype == 'path':
            _pil_draw_path(draw, elem[1], scale, color, sw)
        elif etype == 'circle':
            cx = elem[1] * scale
            cy = elem[2] * scale
            r = elem[3] * scale
            draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                         outline=color, width=int(round(sw)))
        elif etype == 'rect':
            x, y = elem[1] * scale, elem[2] * scale
            rw, rh = elem[3] * scale, elem[4] * scale
            rx = (elem[5] if len(elem) > 5 else 0) * scale
            if rx > 0 and hasattr(draw, 'rounded_rectangle'):
                draw.rounded_rectangle([x, y, x + rw, y + rh],
                                       radius=rx, outline=color,
                                       width=int(round(sw)))
            else:
                draw.rectangle([x, y, x + rw, y + rh],
                               outline=color, width=int(round(sw)))
        elif etype == 'polyline':
            pts = elem[1]
            coords = [(pts[j] * scale, pts[j + 1] * scale)
                      for j in range(0, len(pts), 2)]
            if len(coords) >= 2:
                draw.line(coords, fill=color, width=int(round(sw)),
                          joint='curve')

    # Composite onto bg_color so transparent pixels become the menu
    # surface colour instead of black.
    bg_hex = bg_color.lstrip('#')
    bg_rgb = tuple(int(bg_hex[i:i + 2], 16) for i in (0, 2, 4))
    bg_layer = Image.new('RGBA', (size, size), bg_rgb + (255,))
    return Image.alpha_composite(bg_layer, img)


# ---------------------------------------------------------------------------
# Icon cache  (pre-rendered PhotoImages for normal + hover states)
# ---------------------------------------------------------------------------

_ICON_CACHE: dict = {}


def _build_icon_cache(menu_bg, text_secondary, accent):
    """Pre-render all icons as PhotoImages.

    Each icon has two variants:
      - 'normal': stroke in text_secondary on menu_bg
      - 'accent': stroke in accent on hover_bg  (hover surface)
    """
    import tkinter as tk
    import io

    # Determine hover bg based on palette (dark vs light)
    if menu_bg.upper() in ('#FFFFFF', '#FAF7F2'):
        hover_bg = '#FDF0EB'    # light hover
        danger_hover = '#FDE8E8'
    else:
        hover_bg = '#2D2428'    # dark hover
        danger_hover = '#2C1A1F'

    all_icons = dict(ICON_DATA)
    all_icons['_arrow'] = _CHEVRON_RIGHT

    for label, elements in all_icons.items():
        for variant, stroke_color, bg in [
            ('normal', text_secondary, menu_bg),
            ('accent', accent, hover_bg),
        ]:
            img = _pil_render_elements(elements, stroke_color, bg)
            small = img.resize((_IC_SIZE, _IC_SIZE), Image.LANCZOS)
            buf = io.BytesIO()
            small.convert('RGB').save(buf, format='PPM')
            photo = tk.PhotoImage(data=buf.getvalue())
            _ICON_CACHE[f'{label}_{variant}'] = photo


def _get_icon(label: str, variant: str = 'normal'):
    """Look up a cached icon PhotoImage."""
    return _ICON_CACHE.get(f'{label}_{variant}')


# ---------------------------------------------------------------------------
# Menu structure
# ---------------------------------------------------------------------------

DANGER_LABELS = {"退出"}


def _build_menu_order(agent_available: bool) -> list:
    """根据 agent 可用性动态生成菜单项顺序。

    agent 不可用时仅移除"自由对话"（依赖 AI agent）。
    "工具箱"子菜单始终显示（其中的功能为本地命令，不依赖 agent）。
    分隔符采用条件性添加策略，避免连续分隔符。
    """
    order = ["打开导航页", "打开归档目录"]
    if agent_available:
        order.append("自由对话")
    order.append(None)  # separator before toolbox
    order.append("SUBMENU")
    order.append(None)  # separator before settings
    order += ["设置", "关于", None, "退出"]
    return order


SUBMENU_ITEMS = [
    "清理磁盘",
    "系统信息",
    "查看日期",
    "假期提醒",
    "经期提醒",
]


# ===================================================================
# Adapter + ContextMenu
# ===================================================================

class _MenuWindowAdapter:
    config: Any
    parent: Any
    state: Any
    agent_gateway: Any
    _update_html: Any
    _on_settings_saved: Any

    def __init__(self, config, parent, agent_gateway=None,
                 on_quit_callback=None, on_settings_saved=None):
        self.config = config
        self.parent = parent
        self.agent_gateway = agent_gateway
        self._on_quit_callback = on_quit_callback
        self.state = type("FakeState", (),
                          {"show_bubble": lambda s, t, d: None})()
        self._update_html = lambda: None
        self._on_settings_saved = on_settings_saved

    def quit(self):
        if self._on_quit_callback:
            self._on_quit_callback()


class ContextMenu:
    """右键菜单（自定义绘制实现，匹配 HTML 原型）"""

    MENU_WIDTH = 220
    ITEM_HEIGHT = 40
    RADIUS = 12
    PADDING_Y = 6
    SEPARATOR_HEIGHT = 1
    SEPARATOR_MARGIN_Y = 6
    SEPARATOR_MARGIN_X = 12
    ITEM_GAP = 12
    ITEM_PAD_X = 16
    SUBMENU_OFFSET_X = 0

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
        self._trigger_accent_bar = None

    # ------------------------------------------------------------------
    # Build callback map
    # ------------------------------------------------------------------

    def _get_menu_order(self) -> list:
        """根据当前 agent 状态动态获取菜单顺序。"""
        agent_available = False
        if self.window is not None:
            agent_available = getattr(self.window, "agent_available", False)
        elif self.agent_gateway is not None:
            agent_available = getattr(self.agent_gateway, "enabled", False)
        return _build_menu_order(agent_available)

    def _build_items_map(self):
        from .menu_actions import build_menu_items
        menu_window = self.window or _MenuWindowAdapter(
            self.config, self.parent,
            agent_gateway=self.agent_gateway,
            on_quit_callback=self._quit,
            on_settings_saved=self._on_settings_saved,
        )
        items = build_menu_items(menu_window)
        item_map = {}
        for item in items:
            if item is not None:
                label, callback = item
                item_map[label] = callback
        return item_map

    # ------------------------------------------------------------------
    # Height calculation
    # ------------------------------------------------------------------

    def _calc_main_height(self, menu_order=None):
        if menu_order is None:
            menu_order = self._get_menu_order()
        h = self.PADDING_Y * 2
        for item in menu_order:
            if item is None:
                h += self.SEPARATOR_HEIGHT + self.SEPARATOR_MARGIN_Y * 2
            else:
                h += self.ITEM_HEIGHT
        return h

    def _calc_submenu_height(self):
        h = self.PADDING_Y * 2
        for _ in SUBMENU_ITEMS:
            h += self.ITEM_HEIGHT
        return h

    # ------------------------------------------------------------------
    # Rounded rectangle
    # ------------------------------------------------------------------

    @staticmethod
    def _draw_rounded_rect(canvas, x1, y1, x2, y2, r, fill, outline):
        canvas.create_oval(x1, y1, x1 + r*2, y1 + r*2,
                           fill=fill, outline='', tags='bg')
        canvas.create_oval(x2 - r*2, y1, x2, y1 + r*2,
                           fill=fill, outline='', tags='bg')
        canvas.create_oval(x1, y2 - r*2, x1 + r*2, y2,
                           fill=fill, outline='', tags='bg')
        canvas.create_oval(x2 - r*2, y2 - r*2, x2, y2,
                           fill=fill, outline='', tags='bg')
        canvas.create_rectangle(x1 + r, y1, x2 - r, y2,
                                fill=fill, outline='', tags='bg')
        canvas.create_rectangle(x1, y1 + r, x2, y2 - r,
                                fill=fill, outline='', tags='bg')
        canvas.create_arc(x1, y1, x1 + r*2, y1 + r*2, start=90, extent=90,
                          style='arc', outline=outline, width=1, tags='bg')
        canvas.create_arc(x2 - r*2, y1, x2, y1 + r*2, start=0, extent=90,
                          style='arc', outline=outline, width=1, tags='bg')
        canvas.create_arc(x1, y2 - r*2, x1 + r*2, y2, start=180, extent=90,
                          style='arc', outline=outline, width=1, tags='bg')
        canvas.create_arc(x2 - r*2, y2 - r*2, x2, y2, start=270, extent=90,
                          style='arc', outline=outline, width=1, tags='bg')
        canvas.create_line(x1 + r, y1, x2 - r, y1, fill=outline, tags='bg')
        canvas.create_line(x1 + r, y2, x2 - r, y2, fill=outline, tags='bg')
        canvas.create_line(x1, y1 + r, x1, y2 - r, fill=outline, tags='bg')
        canvas.create_line(x2, y1 + r, x2, y2 - r, fill=outline, tags='bg')

    # ------------------------------------------------------------------
    # Menu item creation  (icons via PIL PhotoImage on Label)
    # ------------------------------------------------------------------

    def _create_menu_item(self, parent, y, label, callback, is_danger, c, width):
        import tkinter as tk

        h = self.ITEM_HEIGHT
        pad_x = self.ITEM_PAD_X

        if is_danger:
            fg = c['danger']
            hover_bg = c['danger_hover']
            hover_label_fg = c['danger']
        else:
            fg = c['fg']
            hover_bg = c['menu_hover']
            hover_label_fg = c['fg']

        frame = tk.Frame(parent, bg=c['menu_bg'], height=h, cursor='hand2')
        frame.place(x=0, y=y, width=width, height=h)
        frame.pack_propagate(False)

        # Icon: PIL-rendered PhotoImage on a Label
        icon_size = _IC_SIZE
        normal_img = _get_icon(label, 'normal')
        hover_img = _get_icon(label, 'accent')

        icon_label = tk.Label(frame, bg=c['menu_bg'],
                              image=normal_img, bd=0, highlightthickness=0)
        icon_label.place(x=pad_x, y=(h - icon_size) // 2,
                         width=icon_size, height=icon_size)
        icon_label._icon_normal = normal_img
        icon_label._icon_hover = hover_img

        # Label text
        text_x = pad_x + icon_size + self.ITEM_GAP
        text_label = tk.Label(frame, text=label, bg=c['menu_bg'], fg=fg,
                              font=('Microsoft YaHei', 10), anchor='w')
        text_label.place(x=text_x, y=0, height=h,
                         width=width - text_x - pad_x)

        def _on_enter(e):
            frame.configure(bg=hover_bg)
            icon_label.configure(bg=hover_bg, image=hover_img)
            text_label.configure(bg=hover_bg, fg=hover_label_fg)

        def _on_leave(e):
            frame.configure(bg=c['menu_bg'])
            icon_label.configure(bg=c['menu_bg'], image=normal_img)
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
        import tkinter as tk

        h = self.ITEM_HEIGHT
        pad_x = self.ITEM_PAD_X
        hover_bg = c['menu_hover']
        icon_size = _IC_SIZE

        frame = tk.Frame(parent, bg=c['menu_bg'], height=h, cursor='hand2')
        frame.place(x=0, y=y, width=width, height=h)
        frame.pack_propagate(False)

        # Left accent bar
        accent_bar = tk.Frame(frame, width=3, bg=c['menu_bg'])
        accent_bar.place(x=0, y=6, height=h - 12)

        # Wrench icon
        normal_img = _get_icon("工具箱", 'normal')
        hover_img = _get_icon("工具箱", 'accent')
        icon_label = tk.Label(frame, bg=c['menu_bg'],
                              image=normal_img, bd=0, highlightthickness=0)
        icon_label.place(x=pad_x, y=(h - icon_size) // 2,
                         width=icon_size, height=icon_size)
        icon_label._icon_normal = normal_img
        icon_label._icon_hover = hover_img

        # Label
        text_x = pad_x + icon_size + self.ITEM_GAP
        text_label = tk.Label(frame, text="工具箱",
                              bg=c['menu_bg'], fg=c['fg'],
                              font=('Microsoft YaHei', 10), anchor='w')
        text_label.place(x=text_x, y=0, height=h,
                         width=width - text_x - pad_x - 24)

        # Chevron arrow
        arrow_size = 14
        arrow_normal = _get_icon('_arrow', 'normal')
        arrow_hover = _get_icon('_arrow', 'accent')
        arrow_label = tk.Label(frame, bg=c['menu_bg'],
                               image=arrow_normal, bd=0, highlightthickness=0)
        arrow_label.place(x=width - pad_x - arrow_size,
                          y=(h - arrow_size) // 2,
                          width=arrow_size, height=arrow_size)
        arrow_label._icon_normal = arrow_normal
        arrow_label._icon_hover = arrow_hover

        def _set_expanded(expanded):
            if expanded:
                accent_bar.configure(bg=c['accent'])
                icon_label.configure(image=hover_img)
                text_label.configure(fg=c['accent_hover'])
                arrow_label.configure(image=arrow_hover)
            else:
                accent_bar.configure(bg=c['menu_bg'])
                icon_label.configure(image=normal_img)
                text_label.configure(fg=c['fg'])
                arrow_label.configure(image=arrow_normal)

        # Hover handlers
        _trigger_hovered = [False]

        def _on_enter(e):
            _trigger_hovered[0] = True
            frame.configure(bg=hover_bg)
            icon_label.configure(bg=hover_bg, image=hover_img)
            text_label.configure(bg=hover_bg)
            arrow_label.configure(bg=hover_bg, image=arrow_hover)
            if not self._submenu_visible:
                accent_bar.configure(bg=hover_bg)
                self._show_submenu(y)
            else:
                accent_bar.configure(bg=c['accent'])

        def _on_leave(e):
            _trigger_hovered[0] = False
            frame.configure(bg=c['menu_bg'])
            icon_label.configure(bg=c['menu_bg'], image=normal_img)
            text_label.configure(bg=c['menu_bg'])
            arrow_label.configure(bg=c['menu_bg'], image=arrow_normal)
            if self._submenu_visible:
                accent_bar.configure(bg=c['accent'])
                self._schedule_hide_submenu()
            else:
                accent_bar.configure(bg=c['menu_bg'])

        for widget in (frame, icon_label, text_label, arrow_label, accent_bar):
            widget.bind('<Enter>', _on_enter)
            widget.bind('<Leave>', _on_leave)

        self._submenu_trigger_frame = frame
        self._set_expanded = _set_expanded
        self._trigger_accent_bar = accent_bar
        return frame

    # ------------------------------------------------------------------
    # Submenu panel
    # ------------------------------------------------------------------

    def _create_submenu_window(self, trigger_screen_y):
        import tkinter as tk

        # Set flag BEFORE creating Toplevel — creating a new Toplevel
        # steals focus, which fires FocusOut on the main menu.  If this
        # flag is still False at that point, _on_focus_out calls
        # _dismiss_all and destroys the menu.
        self._submenu_visible = True

        c = self._colors
        w = self.MENU_WIDTH
        h = self._calc_submenu_height()
        r = self.RADIUS

        sub = tk.Toplevel(self.parent)
        sub.overrideredirect(True)
        sub.configure(bg=c['menu_bg'])
        sub.attributes('-topmost', True)

        canvas = tk.Canvas(sub, width=w, height=h,
                           bg=c['menu_bg'], highlightthickness=0, bd=0)
        canvas.pack(fill='both', expand=True)
        self._draw_rounded_rect(canvas, 0, 0, w, h, r, c['menu_bg'], c['border'])

        overlay = tk.Frame(canvas, bg=c['menu_bg'])
        canvas.create_window((0, 0), window=overlay, anchor='nw',
                             tags='sub-overlay')

        def _resize(event):
            canvas.itemconfigure('sub-overlay', width=w, height=h)
        canvas.bind('<Configure>', _resize)

        y = self.PADDING_Y
        for label in SUBMENU_ITEMS:
            callback = self._items_map.get(label)
            is_danger = label in DANGER_LABELS
            self._create_menu_item(overlay, y, label, callback, is_danger, c, w)
            y += self.ITEM_HEIGHT

        main_x = self._menu_window.winfo_rootx()
        main_w = self._menu_window.winfo_width()
        sx = main_x + main_w + self.SUBMENU_OFFSET_X
        sy = trigger_screen_y

        sw = sub.winfo_screenwidth()
        sh = sub.winfo_screenheight()
        if sx + w > sw:
            sx = main_x - w - self.SUBMENU_OFFSET_X
        if sy + h > sh:
            sy = sh - h - 4
        if sy < 0:
            sy = 4

        sub.geometry(f"{w}x{h}+{sx}+{sy}")

        def _sub_enter(e):
            self._cancel_hide_timer()

        def _sub_leave(e):
            self._schedule_hide_submenu()

        for w_bind in (sub, canvas, overlay):
            w_bind.bind('<Enter>', _sub_enter)
            w_bind.bind('<Leave>', _sub_leave)

        canvas.bind('<Button-1>', lambda e: self._dismiss_all())

        self._submenu_window = sub
        if self._set_expanded:
            self._set_expanded(True)
        # Force-restore accent bar (spurious Leave from Toplevel creation)
        if self._trigger_accent_bar:
            try:
                self._trigger_accent_bar.configure(bg=c['accent'])
            except Exception:
                pass

    def _show_submenu(self, trigger_y):
        self._cancel_hide_timer()
        if self._submenu_visible:
            return
        trigger_screen_y = self._menu_window.winfo_rooty() + trigger_y
        self._create_submenu_window(trigger_screen_y)

    def _hide_submenu(self):
        """Hide submenu — only if pointer is NOT over the menu area."""
        if not self._submenu_visible:
            return

        # Pointer-position guard: only hide when cursor has truly left
        try:
            px = self.parent.winfo_pointerx()
            py = self.parent.winfo_pointery()
        except Exception:
            px = py = -1

        if self._pointer_over_menu(px, py):
            # Cursor still inside menu region — reschedule check
            self._schedule_hide_submenu()
            return

        # Actually hide
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

    def _pointer_over_menu(self, px, py) -> bool:
        """Check whether screen coords (px, py) are over the main or submenu."""
        for win in (self._menu_window, self._submenu_window):
            if win is None:
                continue
            try:
                if not win.winfo_exists():
                    continue
                wx = win.winfo_rootx()
                wy = win.winfo_rooty()
                ww = win.winfo_width()
                wh = win.winfo_height()
                if wx <= px <= wx + ww and wy <= py <= wy + wh:
                    return True
            except Exception:
                pass
        return False

    def _schedule_hide_submenu(self):
        """Schedule a hide attempt after 500 ms.

        The actual _hide_submenu checks the pointer position and bails
        out if the cursor is still over the menu / submenu area.
        """
        self._cancel_hide_timer()
        target = self._submenu_window or self._menu_window
        if target:
            try:
                self._hide_timer = target.after(500, self._hide_submenu)
            except Exception:
                pass

    def _cancel_hide_timer(self):
        if self._hide_timer is not None:
            target = self._submenu_window or self._menu_window
            if target:
                try:
                    target.after_cancel(self._hide_timer)
                except Exception:
                    pass
            self._hide_timer = None

    # ------------------------------------------------------------------
    # Main menu creation
    # ------------------------------------------------------------------

    def _create_menu(self):
        import tkinter as tk

        c = resolve_colors(getattr(self.config, 'config', self.config))
        self._colors = c
        self._items_map = self._build_items_map()

        # Ensure icon cache is built
        if not _ICON_CACHE:
            _build_icon_cache(c['menu_bg'], c['text_secondary'], c['accent'])

        self._menu_window = tk.Toplevel(self.parent)
        self._menu_window.overrideredirect(True)
        self._menu_window.configure(bg=c['menu_bg'])
        self._menu_window.attributes('-topmost', True)

        w = self.MENU_WIDTH
        menu_order = self._get_menu_order()
        h = self._calc_main_height(menu_order)
        r = self.RADIUS

        canvas = tk.Canvas(self._menu_window, width=w, height=h,
                           bg=c['menu_bg'], highlightthickness=0, bd=0)
        canvas.pack(fill='both', expand=True)
        self._draw_rounded_rect(canvas, 0, 0, w, h, r, c['menu_bg'], c['border'])

        overlay = tk.Frame(canvas, bg=c['menu_bg'])
        canvas.create_window((0, 0), window=overlay, anchor='nw',
                             tags='overlay')

        def _resize_overlay(event):
            canvas.itemconfigure('overlay', width=w, height=h)
        canvas.bind('<Configure>', _resize_overlay)

        y = self.PADDING_Y
        self._submenu_trigger_y = None

        for item in menu_order:
            if item is None:
                sep_y = y + self.SEPARATOR_MARGIN_Y
                sep_frame = tk.Frame(overlay, height=1, bg=c['separator'])
                sep_frame.place(x=self.SEPARATOR_MARGIN_X, y=sep_y,
                                width=w - self.SEPARATOR_MARGIN_X * 2, height=1)
                y += self.SEPARATOR_HEIGHT + self.SEPARATOR_MARGIN_Y * 2
            elif item == "SUBMENU":
                self._submenu_trigger_y = y
                self._create_submenu_trigger(overlay, y, c, w)
                y += self.ITEM_HEIGHT
            else:
                label = item
                callback = self._items_map.get(label)
                is_danger = label in DANGER_LABELS
                self._create_menu_item(overlay, y, label, callback, is_danger, c, w)
                y += self.ITEM_HEIGHT

        self._menu_w = w
        self._menu_h = h

        self._menu_window.bind('<FocusOut>', self._on_focus_out)
        self._menu_window.bind('<Escape>', lambda e: self._dismiss_all())
        canvas.bind('<Button-1>', lambda e: self._dismiss_all())

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show(self, x: int, y: int):
        self._dismiss_all()
        self._dismissed = False

        self._create_menu()

        sw = self._menu_window.winfo_screenwidth()
        sh = self._menu_window.winfo_screenheight()

        mx, my = x, y
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

        try:
            self._menu_window.focus_set()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Dismiss logic
    # ------------------------------------------------------------------

    def _dismiss_all(self):
        if self._dismissed:
            return
        self._dismissed = True
        self._submenu_visible = False
        if self._submenu_window:
            try:
                if self._submenu_window.winfo_exists():
                    self._submenu_window.destroy()
            except Exception:
                pass
        self._submenu_window = None
        if self._menu_window:
            try:
                if self._menu_window.winfo_exists():
                    self._menu_window.destroy()
            except Exception:
                pass
        self._menu_window = None

    def _on_focus_out(self, event=None):
        if event and event.widget == self._menu_window:
            if self._submenu_visible:
                self._schedule_hide_submenu()
            else:
                # Pointer-position guard: the submenu Toplevel creation
                # can steal focus before _submenu_visible is set.  If
                # the pointer is still over the menu, don't dismiss.
                try:
                    px = self.parent.winfo_pointerx()
                    py = self.parent.winfo_pointery()
                except Exception:
                    px = py = -1
                if self._pointer_over_menu(px, py):
                    # Reschedule a check after a short delay
                    try:
                        self._menu_window.after(300, self._focus_out_recheck)
                    except Exception:
                        pass
                else:
                    self._dismiss_all()

    def _focus_out_recheck(self):
        """Re-check focus state after a delay (called from _on_focus_out)."""
        if self._submenu_visible:
            return  # submenu is showing, don't dismiss
        if self._menu_window is None:
            return
        try:
            if not self._menu_window.winfo_exists():
                return
            px = self.parent.winfo_pointerx()
            py = self.parent.winfo_pointery()
        except Exception:
            return
        if not self._pointer_over_menu(px, py):
            self._dismiss_all()

    def _on_settings_saved(self):
        if self.on_settings_saved:
            self.on_settings_saved()

    def _quit(self):
        if self.on_quit_callback:
            self.on_quit_callback()
