"""
Windows 窗口圆角 + 阴影辅助工具

使用 Win32 API 为 Tkinter Toplevel 窗口添加圆角和阴影效果。
支持 Windows 11 (DWM 原生圆角+阴影) 和 Windows 10 (分层窗口绘制阴影)。
"""

import ctypes
import ctypes.wintypes
import sys

# Win32 constants
DWMWPCORNER_PREF = 33
DWMWCP_ROUND = 2


def get_hwnd(window):
    """获取 Tkinter 窗口的 HWND"""
    try:
        return ctypes.windll.user32.GetParent(window.winfo_id())
    except Exception:
        return None


def apply_rounded_corners(window, radius=14):
    """
    为窗口应用圆角效果。

    Windows 11: DWM 原生圆角（自带阴影）-> 返回 True
    Windows 10: GDI 区域裁剪 -> 返回 False

    Returns:
        True if DWM rounded corners applied (shadow included),
        False if fallback used (no shadow).
    """
    if sys.platform != 'win32':
        return False

    window.update_idletasks()
    hwnd = get_hwnd(window)
    if not hwnd:
        return False

    # 尝试 Windows 11 DWM 原生圆角
    try:
        pref = ctypes.c_int(DWMWCP_ROUND)
        hr = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWPCORNER_PREF,
            ctypes.byref(pref), ctypes.sizeof(pref)
        )
        if hr == 0:
            return True  # DWM 成功，自带阴影
    except Exception:
        pass

    # 回退: GDI 区域裁剪 (Windows 10)
    try:
        w = window.winfo_width()
        h = window.winfo_height()
        region = ctypes.windll.gdi32.CreateRoundRectRgn(
            0, 0, w, h, radius * 2, radius * 2)
        ctypes.windll.user32.SetWindowRgn(hwnd, region, True)
    except Exception:
        pass

    return False


def apply_shadow(window):
    """
    为窗口添加 CS_DROPSHADOW 投影（仅在圆角区域裁剪后作为补充）。

    注意：CS_DROPSHADOW 是矩形阴影，如果窗口已用 DWM 圆角则不需要。
    推荐配合 apply_rounded_corners 的返回值使用。
    """
    if sys.platform != 'win32':
        return

    window.update_idletasks()
    hwnd = get_hwnd(window)
    if not hwnd:
        return

    try:
        GWL_STYLE = -16
        GCL_STYLE = -26
        CS_DROPSHADOW = 0x00020000
        user32 = ctypes.windll.user32
        style = user32.GetClassLongW(hwnd, GCL_STYLE)
        user32.SetClassLongW(hwnd, GCL_STYLE, style | CS_DROPSHADOW)
    except Exception:
        pass


def style_popup_window(window, radius=14):
    """
    一步完成弹出窗口的圆角 + 阴影样式。

    - Windows 11: DWM 原生圆角（自带柔和阴影）
    - Windows 10: GDI 圆角裁剪 + CS_DROPSHADOW
    """
    has_dwm_shadow = apply_rounded_corners(window, radius)
    if not has_dwm_shadow:
        apply_shadow(window)


def apply_rounded_shadow(window, shadow_size=12, corner_radius=14,
                         shadow_opacity=80):
    """
    为 overrideredirect 窗口绘制圆角柔和阴影。

    工作原理：
    1. 窗口尺寸扩大 shadow_size*2
    2. 背景设为透明色 (#010101)
    3. 在底层 Canvas 绘制多层渐变圆角矩形
    4. 在内容区域放置实心背景 + Frame

    Args:
        window: 已创建但未 pack 内容的 Toplevel
        shadow_size: 阴影扩散像素
        corner_radius: 内容区圆角半径
        shadow_opacity: 阴影最深不透明度 (0-255)

    Returns:
        inner_frame: tk.Frame，用户在此放置所有子控件
    """
    import tkinter as tk

    if sys.platform != 'win32':
        # 非 Windows 直接返回 None
        return None

    window.update_idletasks()
    ww = window.winfo_width()
    wh = window.winfo_height()

    pad = shadow_size
    # 新尺寸 = 原尺寸 + 两侧阴影
    new_w = ww + pad * 2
    new_h = wh + pad * 2

    # 重新定位窗口（向左上偏移 pad 保持内容位置不变）
    x = window.winfo_x() - pad
    y = window.winfo_y() - pad
    window.geometry(f"{new_w}x{new_h}+{x}+{y}")

    # 透明色
    trans = '#010101'
    window.configure(bg=trans)
    window.attributes('-transparentcolor', trans)

    # 阴影 Canvas
    shadow_cv = tk.Canvas(window, width=new_w, height=new_h,
                          bg=trans, highlightthickness=0, bd=0)
    shadow_cv.place(x=0, y=0)

    # 绘制多层阴影 (从外到内，逐渐加暗)
    layers = 10
    for i in range(layers):
        spread = pad - i
        if spread < 1:
            break
        # 计算此层的不透明度
        frac = (layers - i) / layers  # 1.0 (最外层) -> ~0.1 (最内层)
        alpha = int(shadow_opacity * frac * frac)  # 二次衰减
        if alpha < 2:
            continue

        # 阴影色混合到透明色上
        gray = int(alpha * 0.15)  # 阴影灰度
        fill = f'#{gray:02x}{gray:02x}{gray:02x}'
        r = corner_radius + spread
        _draw_rounded_rect(shadow_cv, pad - spread, pad - spread,
                           pad + ww + spread, pad + wh + spread, r, fill)

    # 内容区域实心背景 (覆盖在阴影上方)
    content_bg = window._meowdesk_bg if hasattr(window, '_meowdesk_bg') else '#121218'
    _draw_rounded_rect(shadow_cv, pad, pad, pad + ww, pad + wh,
                       corner_radius, content_bg)

    # 内容 Frame
    inner = tk.Frame(window, bg=content_bg)
    inner.place(x=pad, y=pad, width=ww, height=wh)

    return inner


# ---- 内部绘制辅助 ----

def _draw_rounded_rect(canvas, x0, y0, x1, y1, r, fill):
    """在 Canvas 上绘制圆角矩形（oval + rectangle 拼合）"""
    if r <= 0:
        canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline='')
        return
    r = min(r, (x1 - x0) // 2, (y1 - y0) // 2)
    # 四个圆角
    canvas.create_oval(x0, y0, x0 + r*2, y0 + r*2, fill=fill, outline='')
    canvas.create_oval(x1 - r*2, y0, x1, y0 + r*2, fill=fill, outline='')
    canvas.create_oval(x0, y1 - r*2, x0 + r*2, y1, fill=fill, outline='')
    canvas.create_oval(x1 - r*2, y1 - r*2, x1, y1, fill=fill, outline='')
    # 十字填充
    canvas.create_rectangle(x0 + r, y0, x1 - r, y1, fill=fill, outline='')
    canvas.create_rectangle(x0, y0 + r, x1, y1 - r, fill=fill, outline='')


def _hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
