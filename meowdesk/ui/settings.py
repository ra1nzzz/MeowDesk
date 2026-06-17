"""
设置面板模块 — 支持深色/浅色/跟随系统三种色彩模式
侧栏导航 + 卡片式内容布局（匹配 HTML 原型）
"""

import os
from typing import Dict, Callable, Optional
from datetime import datetime


# ---------------------------------------------------------------------------
# Theme palettes
# ---------------------------------------------------------------------------
DARK_COLORS = {
    'bg': '#121218',
    'fg': '#F0EDE8',
    'entry_bg': '#22222E',
    'accent': '#F4845F',
    'accent_hover': '#F69B7D',
    'danger': '#F87171',
    'success': '#6EE7A0',
    'warning': '#FBBF5C',
    'border': '#2D2D3D',
    'text_muted': '#6B6880',
    # Extended palette (matching prototype)
    'bg_elevated': '#1A1A24',
    'bg_input': '#2A2A38',
    'text_secondary': '#A8A4B8',
    'border_hover': '#44445A',
}

LIGHT_COLORS = {
    'bg': '#FAF7F2',
    'fg': '#2D2A33',
    'entry_bg': '#FFFFFF',
    'accent': '#E8734E',
    'accent_hover': '#D4613B',
    'danger': '#DC4A4A',
    'success': '#3DA86A',
    'warning': '#D4A020',
    'border': '#D5CFC7',
    'text_muted': '#8A8490',
    # Extended palette (matching prototype)
    'bg_elevated': '#F2EDE4',
    'bg_input': '#F0EBE2',
    'text_secondary': '#6B6578',
    'border_hover': '#C4BFB6',
}


def _is_windows_dark_mode() -> bool:
    """Detect Windows 10/11 dark-mode preference from the registry."""
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


def resolve_colors(color_mode: str) -> dict:
    """Return the correct palette dict based on *color_mode*."""
    if color_mode == "light":
        return dict(LIGHT_COLORS)
    if color_mode == "system":
        return dict(DARK_COLORS) if _is_windows_dark_mode() else dict(LIGHT_COLORS)
    return dict(DARK_COLORS)


class SettingsPanel:
    """设置面板"""

    # Class-level default (dark); instance overrides in __init__
    COLORS = dict(DARK_COLORS)

    def __init__(self, parent, config, on_save_callback: Optional[Callable] = None):
        import tkinter as tk
        from tkinter import ttk, messagebox, filedialog
        self.tk = tk
        self.ttk = ttk
        self._messagebox = messagebox
        self._filedialog = filedialog

        self.parent = parent
        self.config = config
        self.on_save_callback = on_save_callback

        # ---- Resolve theme based on config.color_mode ----
        color_mode = "dark"
        try:
            color_mode = getattr(config.config, 'color_mode', 'dark')
        except Exception:
            pass
        self.COLORS = resolve_colors(color_mode)

        # 创建窗口
        self.window = self.tk.Toplevel(parent)
        self.window.title("设置")
        self.window.configure(bg=self.COLORS['bg'])
        self.window.resizable(False, False)

        # 设置窗口图标
        import sys as _sys
        _bundle = getattr(_sys, '_MEIPASS', None)
        _base = _bundle if _bundle else os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        _icon = os.path.join(_base, 'assets', 'icon.ico')
        if os.path.exists(_icon):
            try:
                self.window.iconbitmap(_icon)
            except Exception:
                pass

        # 居中显示
        self.window.update_idletasks()
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        ww, wh = 680, 520
        self.window.geometry(f"{ww}x{wh}+{(sw-ww)//2}+{(sh-wh)//2}")
        self.window.attributes("-topmost", True)
        self.window.grab_set()

        # 创建布局
        self._create_notebook()
        self._create_buttons()

    # ------------------------------------------------------------------
    # Theme helpers
    # ------------------------------------------------------------------

    def _get_color_mode(self) -> str:
        try:
            return getattr(self.config.config, 'color_mode', 'dark')
        except Exception:
            return 'dark'

    def _on_color_mode_changed(self):
        """Handle color_mode change — re-open settings with new theme."""
        new_mode = self.color_mode_var.get()
        if new_mode == self._get_color_mode():
            return
        try:
            self.config.set('color_mode', new_mode)
            self.config.save()
        except Exception:
            pass
        parent = self.parent
        callback = self.on_save_callback
        self.window.destroy()
        SettingsPanel(parent, self.config, on_save_callback=callback)

    # ------------------------------------------------------------------
    # Notebook / sidebar
    # ------------------------------------------------------------------

    def _create_notebook(self):
        """创建侧栏导航布局（匹配原型：左边框指示器 + 可滚动内容区）"""
        c = self.COLORS
        main_frame = self.tk.Frame(self.window, bg=c['bg'])
        main_frame.pack(side='top', fill='both', expand=True)

        # --- 侧栏 ---
        sidebar = self.tk.Frame(main_frame, width=160, bg=c['bg_elevated'])
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)

        # 品牌区域（图标 + 名称，带底部分割线）
        brand_frame = self.tk.Frame(sidebar, bg=c['bg_elevated'])
        brand_frame.pack(fill='x')

        _bundle = getattr(__import__('sys'), '_MEIPASS', None)
        _base = _bundle if _bundle else os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        _icon_png = os.path.join(_base, 'asset', 'icon.png')
        if not os.path.exists(_icon_png):
            _icon_png = os.path.join(_base, 'assets', 'icon.png')
        if os.path.exists(_icon_png):
            try:
                from PIL import Image, ImageTk
                _img = Image.open(_icon_png).resize((72, 72), Image.LANCZOS)
                self._sidebar_icon_photo = ImageTk.PhotoImage(_img)
                icon_label = self.tk.Label(brand_frame, image=self._sidebar_icon_photo,
                                           bg=c['bg_elevated'])
                icon_label.pack(pady=(16, 6))
            except Exception:
                pass

        self.tk.Label(brand_frame, text="妙喵桌宠", bg=c['bg_elevated'],
                      fg=c['fg'], font=("Microsoft YaHei", 10, "bold")).pack()
        self.tk.Frame(brand_frame, height=1, bg=c['border']).pack(fill='x', padx=16, pady=(12, 0))

        # 导航按钮（左侧竖条指示器）
        self._tab_buttons = {}
        self._tab_labels = {}
        self._tab_frames = {}
        tab_items = [
            ('general',  '⚙   常规'),
            ('ai',       '🤖  AI 助手'),
            ('reminder', '⏰  定时提醒'),
            ('period',   '📅  经期提醒'),
        ]
        nav_frame = self.tk.Frame(sidebar, bg=c['bg_elevated'])
        nav_frame.pack(fill='both', expand=True, pady=(8, 0))

        for key, label_text in tab_items:
            row = self.tk.Frame(nav_frame, bg=c['bg_elevated'])
            row.pack(fill='x', pady=2)

            indicator = self.tk.Frame(row, width=3, bg='transparent')
            indicator.pack(side='left', fill='y')

            lbl = self.tk.Label(row, text=label_text, bg=c['bg_elevated'],
                                fg=c['text_secondary'], font=("Microsoft YaHei", 10),
                                anchor='w', padx=12, pady=8, cursor='hand2')
            lbl.pack(side='left', fill='x', expand=True)
            lbl.bind('<Button-1>', lambda e, k=key: self._switch_tab(k))
            lbl.bind('<Enter>', lambda e, l=lbl, k=key:
                     l.config(bg=c['bg']) if k != self._active_tab else None)
            lbl.bind('<Leave>', lambda e, l=lbl, k=key:
                     l.config(bg=c['bg_elevated']) if k != self._active_tab else None)

            self._tab_buttons[key] = (row, indicator, lbl)
            self._tab_labels[key] = lbl

        # 侧栏底部版本号
        self.tk.Label(sidebar, text="v1.4.0", bg=c['bg_elevated'],
                      fg=c['text_muted'], font=("Microsoft YaHei", 8)).pack(
            side='bottom', pady=(0, 12))

        # --- 可滚动内容区域 ---
        self._content_area = self.tk.Frame(main_frame, bg=c['bg'])
        self._content_area.pack(side='left', fill='both', expand=True)

        self._canvas = self.tk.Canvas(self._content_area, bg=c['bg'],
                                      highlightthickness=0, bd=0)
        self._canvas.pack(fill='both', expand=True)

        scrollbar = self.ttk.Scrollbar(self._content_area, orient='vertical',
                                       command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.place(relx=1.0, rely=0, relheight=1.0, anchor='ne')

        self._inner_frame = self.tk.Frame(self._canvas, bg=c['bg'])
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._inner_frame, anchor='nw')

        self._inner_frame.bind('<Configure>',
                               lambda e: self._canvas.configure(
                                   scrollregion=self._canvas.bbox('all')))
        self._canvas.bind('<Configure>', self._on_canvas_resize)

        # 鼠标滚轮
        self._canvas.bind('<Enter>', lambda e: self._bind_mousewheel())
        self._canvas.bind('<Leave>', lambda e: self._unbind_mousewheel())

        # 创建各选项卡
        self._active_tab = None
        self._create_general_tab()
        self._create_ai_tab()
        self._create_reminder_tab()
        self._create_period_tab()

        # 默认显示常规
        self._switch_tab('general')

    def _on_canvas_resize(self, event):
        self._canvas.itemconfigure(self._canvas_window, width=event.width)

    def _bind_mousewheel(self):
        self._canvas.bind_all('<MouseWheel>',
                              lambda e: self._canvas.yview_scroll(-int(e.delta / 120), 'units'))

    def _unbind_mousewheel(self):
        self._canvas.unbind_all('<MouseWheel>')

    def _switch_tab(self, key):
        """切换选项卡（左边框指示器 + 文字颜色）"""
        c = self.COLORS

        # 隐藏所有 tab frame
        for k, frame in self._tab_frames.items():
            frame.pack_forget()

        # 重置所有导航样式
        for k, (row, indicator, lbl) in self._tab_buttons.items():
            indicator.config(bg='transparent')
            lbl.config(bg=c['bg_elevated'], fg=c['text_secondary'])

        # 激活选中的
        if key in self._tab_frames:
            self._tab_frames[key].pack(fill='x', padx=0, pady=0)
            row, indicator, lbl = self._tab_buttons[key]
            indicator.config(bg=c['accent'])
            lbl.config(bg=c['bg_elevated'], fg=c['accent'])
            self._active_tab = key
            self._canvas.yview_moveto(0)

    # ------------------------------------------------------------------
    # General tab — 卡片式布局
    # ------------------------------------------------------------------

    def _create_general_tab(self):
        """创建常规设置选项卡（卡片布局）"""
        c = self.COLORS
        tab = self.tk.Frame(self._inner_frame, bg=c['bg'])
        self._tab_frames['general'] = tab

        # 标题
        self.tk.Label(tab, text="常规设置", bg=c['bg'], fg=c['fg'],
                      font=("Microsoft YaHei", 12, "bold")).pack(
            anchor='w', padx=20, pady=(20, 12))

        # ---- Card: 归档目录 ----
        card = self._make_card(tab)

        self.tk.Label(card, text="归档目录", bg=c['entry_bg'], fg=c['fg'],
                      font=("Microsoft YaHei", 10, "bold")).pack(anchor='w')
        self.tk.Label(card, text="设置文件归档的默认保存路径", bg=c['entry_bg'],
                      fg=c['text_muted'], font=("Microsoft YaHei", 9)).pack(anchor='w', pady=(2, 8))

        dir_frame = self.tk.Frame(card, bg=c['entry_bg'])
        dir_frame.pack(fill='x')
        self.dir_var = self.tk.StringVar(value=self.config.archive_dir)
        self.tk.Entry(dir_frame, textvariable=self.dir_var, bg=c['bg_input'],
                      fg=c['fg'], insertbackground=c['fg'], relief="flat",
                      font=("Microsoft YaHei", 10)).pack(side='left', fill='x', expand=True, padx=(0, 8))
        self.tk.Button(dir_frame, text="浏览...", command=self._browse_dir,
                       bg=c['accent'], fg="#fff", relief="flat",
                       cursor="hand2", padx=12).pack(side='right')

        # ---- Card: 宠物大小 ----
        card = self._make_card(tab)

        size_hdr = self.tk.Frame(card, bg=c['entry_bg'])
        size_hdr.pack(fill='x')
        size_left = self.tk.Frame(size_hdr, bg=c['entry_bg'])
        size_left.pack(side='left')
        self.tk.Label(size_left, text="宠物大小", bg=c['entry_bg'], fg=c['fg'],
                      font=("Microsoft YaHei", 10, "bold")).pack(anchor='w')
        self.tk.Label(size_left, text="调整桌面宠物的显示尺寸", bg=c['entry_bg'],
                      fg=c['text_muted'], font=("Microsoft YaHei", 9)).pack(anchor='w', pady=(2, 0))

        self.scale_var = self.tk.DoubleVar(value=self.config.config.scale)
        self.scale_label = self.tk.Label(size_hdr, text=self._fmt_scale(self.scale_var.get()),
                                         bg=c['entry_bg'], fg=c['accent'],
                                         font=("Microsoft YaHei", 10, "bold"))
        self.scale_label.pack(side='right')

        slider_frame = self.tk.Frame(card, bg=c['entry_bg'])
        slider_frame.pack(fill='x', pady=(8, 0))
        self.tk.Scale(slider_frame, from_=0.3, to=1.0, resolution=0.05,
                      orient="horizontal", variable=self.scale_var,
                      bg=c['entry_bg'], fg=c['fg'], troughcolor=c['bg_input'],
                      highlightthickness=0, label="", showvalue=False,
                      length=300, command=self._on_scale_change).pack(side='left', fill='x', expand=True)

        # ---- Card: 截图处理 ----
        card = self._make_card(tab)

        self.tk.Label(card, text="截图处理", bg=c['entry_bg'], fg=c['fg'],
                      font=("Microsoft YaHei", 10, "bold")).pack(anchor='w')
        self.tk.Label(card, text="截图完成后的默认操作", bg=c['entry_bg'],
                      fg=c['text_muted'], font=("Microsoft YaHei", 9)).pack(anchor='w', pady=(2, 8))

        self.ss_var = self.tk.StringVar(value=self.config.config.screenshot_action.value)
        ss_frame = self.tk.Frame(card, bg=c['entry_bg'])
        ss_frame.pack(fill='x')
        for value, text in [("recycle", "移入回收站"), ("archive", "保留到图片")]:
            self.tk.Radiobutton(ss_frame, text=text, variable=self.ss_var, value=value,
                                bg=c['entry_bg'], fg=c['fg'], selectcolor=c['entry_bg'],
                                activebackground=c['entry_bg'], activeforeground=c['fg'],
                                font=("Microsoft YaHei", 10)).pack(side="left", padx=(0, 20))

        # ---- Card: 启动行为 ----
        card = self._make_card(tab)

        self.tk.Label(card, text="启动行为", bg=c['entry_bg'], fg=c['fg'],
                      font=("Microsoft YaHei", 10, "bold")).pack(anchor='w')

        self.launch_var = self.tk.BooleanVar(value=self.config.config.launch_at_startup)
        launch_row = self.tk.Frame(card, bg=c['entry_bg'])
        launch_row.pack(fill='x', pady=(4, 0))
        self.tk.Checkbutton(launch_row, text="随系统启动", variable=self.launch_var,
                            bg=c['entry_bg'], fg=c['fg'], selectcolor=c['entry_bg'],
                            activebackground=c['entry_bg'], activeforeground=c['fg'],
                            font=("Microsoft YaHei", 10)).pack(side='left')
        self.tk.Label(card, text="开机后自动启动妙喵桌宠", bg=c['entry_bg'],
                      fg=c['text_muted'], font=("Microsoft YaHei", 9)).pack(anchor='w', pady=(4, 0))

        # ---- Card: 色彩模式 ----
        card = self._make_card(tab)

        self.tk.Label(card, text="色彩模式", bg=c['entry_bg'], fg=c['fg'],
                      font=("Microsoft YaHei", 10, "bold")).pack(anchor='w')
        self.tk.Label(card, text="选择界面的显示主题", bg=c['entry_bg'],
                      fg=c['text_muted'], font=("Microsoft YaHei", 9)).pack(anchor='w', pady=(2, 8))

        self.color_mode_var = self.tk.StringVar(value=self._get_color_mode())
        cm_frame = self.tk.Frame(card, bg=c['entry_bg'])
        cm_frame.pack(fill='x')

        for value, text in [('dark', '深色'), ('light', '浅色'), ('system', '跟随系统')]:
            self._make_theme_preview(cm_frame, value, text)

        # 底部间距
        self.tk.Frame(tab, height=12, bg=c['bg']).pack()

    def _make_card(self, parent):
        """Create a card container matching the prototype style."""
        c = self.COLORS
        card = self.tk.Frame(parent, bg=c['entry_bg'], highlightbackground=c['border'],
                             highlightthickness=1)
        card.pack(fill='x', padx=16, pady=(0, 10))
        inner = self.tk.Frame(card, bg=c['entry_bg'])
        inner.pack(fill='x', padx=16, pady=14)
        return inner

    def _make_theme_preview(self, parent, value, text):
        """Create a theme preview option (simplified visual card)."""
        c = self.COLORS
        opt = self.tk.Frame(parent, bg=c['entry_bg'], cursor='hand2')
        opt.pack(side='left', padx=(0, 12))

        # Mini preview area
        preview = self.tk.Frame(opt, width=72, height=36, bg=c['entry_bg'],
                                highlightbackground=c['border'], highlightthickness=1)
        preview.pack_propagate(False)
        preview.pack()

        if value == 'dark':
            preview.configure(bg='#121218')
            self.tk.Frame(preview, width=40, height=4, bg='#F4845F').pack(pady=(8, 3), padx=8, anchor='w')
            self.tk.Frame(preview, width=50, height=3, bg='#2D2D3D').pack(pady=1, padx=8, anchor='w')
            self.tk.Frame(preview, width=30, height=3, bg='#2D2D3D').pack(pady=1, padx=8, anchor='w')
        elif value == 'light':
            preview.configure(bg='#FAF7F2')
            self.tk.Frame(preview, width=40, height=4, bg='#E06B45').pack(pady=(8, 3), padx=8, anchor='w')
            self.tk.Frame(preview, width=50, height=3, bg='#DDD8CF').pack(pady=1, padx=8, anchor='w')
            self.tk.Frame(preview, width=30, height=3, bg='#DDD8CF').pack(pady=1, padx=8, anchor='w')
        else:  # system — half dark, half light
            preview.configure(bg='#121218')
            half_right = self.tk.Frame(preview, bg='#FAF7F2')
            half_right.pack(side='right', fill='y', expand=True)

        # Radio + label
        radio_row = self.tk.Frame(opt, bg=c['entry_bg'])
        radio_row.pack(pady=(4, 0))
        self.tk.Radiobutton(radio_row, text=text, variable=self.color_mode_var, value=value,
                            bg=c['entry_bg'], fg=c['fg'], selectcolor=c['entry_bg'],
                            activebackground=c['entry_bg'], activeforeground=c['fg'],
                            font=("Microsoft YaHei", 9),
                            command=self._on_color_mode_changed).pack()

    # ------------------------------------------------------------------
    # AI tab
    # ------------------------------------------------------------------

    def _create_ai_tab(self):
        c = self.COLORS
        tab = self.tk.Frame(self._inner_frame, bg=c['bg'])
        self._tab_frames['ai'] = tab

        self.tk.Label(tab, text="AI 助手设置", bg=c['bg'], fg=c['fg'],
                      font=("Microsoft YaHei", 12, "bold")).pack(anchor='w', padx=20, pady=(20, 12))

        # Card: 启用 AI
        card = self._make_card(tab)
        self.ai_enabled_var = self.tk.BooleanVar(value=self.config.agent_config.enabled)
        self.tk.Checkbutton(card, text="启用 AI 助手", variable=self.ai_enabled_var,
                            bg=c['entry_bg'], fg=c['fg'], selectcolor=c['entry_bg'],
                            activebackground=c['entry_bg'], activeforeground=c['fg'],
                            font=("Microsoft YaHei", 10, "bold")).pack(anchor='w')
        self.tk.Label(card, text="开启后可在右键菜单中使用 AI 对话功能", bg=c['entry_bg'],
                      fg=c['text_muted'], font=("Microsoft YaHei", 9)).pack(anchor='w', pady=(2, 0))

        # Card: 网关类型
        card = self._make_card(tab)
        self.tk.Label(card, text="网关类型", bg=c['entry_bg'], fg=c['fg'],
                      font=("Microsoft YaHei", 10, "bold")).pack(anchor='w')
        self.tk.Label(card, text="选择本地已部署的 AI 网关服务", bg=c['entry_bg'],
                      fg=c['text_muted'], font=("Microsoft YaHei", 9)).pack(anchor='w', pady=(2, 8))
        self.agent_type_var = self.tk.StringVar(value=self.config.agent_config.agent_type.value)
        type_frame = self.tk.Frame(card, bg=c['entry_bg'])
        type_frame.pack(fill='x')
        for value, text in [('openclaw', 'OpenClaw'), ('hermes', 'Hermes'), ('custom', '自定义')]:
            self.tk.Radiobutton(type_frame, text=text, variable=self.agent_type_var, value=value,
                                bg=c['entry_bg'], fg=c['fg'], selectcolor=c['entry_bg'],
                                activebackground=c['entry_bg'], activeforeground=c['fg'],
                                font=("Microsoft YaHei", 10)).pack(side="left", padx=(0, 16))

        # Card: 网关地址
        card = self._make_card(tab)
        self.tk.Label(card, text="网关地址", bg=c['entry_bg'], fg=c['fg'],
                      font=("Microsoft YaHei", 10, "bold")).pack(anchor='w')
        self.tk.Label(card, text="AI 网关服务的访问端点 URL", bg=c['entry_bg'],
                      fg=c['text_muted'], font=("Microsoft YaHei", 9)).pack(anchor='w', pady=(2, 8))
        self.endpoint_var = self.tk.StringVar(value=self.config.agent_config.endpoint)
        self.tk.Entry(card, textvariable=self.endpoint_var, bg=c['bg_input'],
                      fg=c['fg'], insertbackground=c['fg'], relief="flat",
                      font=("Microsoft YaHei", 10)).pack(fill='x')

        # Card: API Token
        card = self._make_card(tab)
        self.tk.Label(card, text="API Token", bg=c['entry_bg'], fg=c['fg'],
                      font=("Microsoft YaHei", 10, "bold")).pack(anchor='w')
        self.tk.Label(card, text="连接 AI 服务的访问凭证", bg=c['entry_bg'],
                      fg=c['text_muted'], font=("Microsoft YaHei", 9)).pack(anchor='w', pady=(2, 8))
        self.token_var = self.tk.StringVar(value=self.config.agent_config.api_key)
        self.tk.Entry(card, textvariable=self.token_var, bg=c['bg_input'],
                      fg=c['fg'], insertbackground=c['fg'], relief="flat",
                      font=("Microsoft YaHei", 10), show="*").pack(fill='x')

        # Card: 超时
        card = self._make_card(tab)
        self.tk.Label(card, text="请求超时", bg=c['entry_bg'], fg=c['fg'],
                      font=("Microsoft YaHei", 10, "bold")).pack(anchor='w')
        self.tk.Label(card, text="AI 请求的最大等待时间（秒）", bg=c['entry_bg'],
                      fg=c['text_muted'], font=("Microsoft YaHei", 9)).pack(anchor='w', pady=(2, 8))
        timeout_row = self.tk.Frame(card, bg=c['entry_bg'])
        timeout_row.pack(anchor='w')
        self.timeout_var = self.tk.IntVar(value=self.config.agent_config.timeout)
        self.tk.Spinbox(timeout_row, textvariable=self.timeout_var, from_=5, to=120,
                        bg=c['bg_input'], fg=c['fg'], insertbackground=c['fg'],
                        relief="flat", font=("Microsoft YaHei", 10), width=6).pack(side='left')
        self.tk.Label(timeout_row, text="秒", bg=c['entry_bg'], fg=c['text_muted'],
                      font=("Microsoft YaHei", 10)).pack(side='left', padx=(4, 0))

        # Card: 测试连接
        card = self._make_card(tab)
        self.tk.Button(card, text="测试连接", command=self._test_connection,
                       bg='transparent', fg=c['accent'], relief="flat",
                       cursor="hand2", padx=20, pady=4,
                       font=("Microsoft YaHei", 10, "bold")).pack()

        self.tk.Frame(tab, height=12, bg=c['bg']).pack()

    # ------------------------------------------------------------------
    # Reminder tab
    # ------------------------------------------------------------------

    def _create_reminder_tab(self):
        c = self.COLORS
        tab = self.tk.Frame(self._inner_frame, bg=c['bg'])
        self._tab_frames['reminder'] = tab

        self.tk.Label(tab, text="定时提醒", bg=c['bg'], fg=c['fg'],
                      font=("Microsoft YaHei", 12, "bold")).pack(anchor='w', padx=20, pady=(20, 12))

        # 提醒列表
        card_outer = self.tk.Frame(tab, bg=c['entry_bg'], highlightbackground=c['border'],
                                   highlightthickness=1)
        card_outer.pack(fill='both', expand=True, padx=16, pady=(0, 10))
        list_frame = self.tk.Frame(card_outer, bg=c['entry_bg'])
        list_frame.pack(fill='both', expand=True, padx=16, pady=14)

        header_frame = self.tk.Frame(list_frame, bg=c['entry_bg'])
        header_frame.pack(fill='x', pady=(0, 8))
        self.tk.Label(header_frame, text="提醒列表", bg=c['entry_bg'], fg=c['fg'],
                      font=("Microsoft YaHei", 10, "bold")).pack(side='left')
        self.tk.Button(header_frame, text="+ 添加提醒", command=self._add_reminder,
                       bg=c['accent'], fg="#fff", relief="flat",
                       cursor="hand2", padx=8, pady=2).pack(side='right')

        columns = ('name', 'time', 'repeat', 'enabled')
        self.reminder_tree = self.ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        self.reminder_tree.heading('name', text='名称')
        self.reminder_tree.heading('time', text='时间')
        self.reminder_tree.heading('repeat', text='重复')
        self.reminder_tree.heading('enabled', text='状态')
        self.reminder_tree.column('name', width=150)
        self.reminder_tree.column('time', width=100)
        self.reminder_tree.column('repeat', width=100)
        self.reminder_tree.column('enabled', width=60, anchor='center')

        scrollbar = self.ttk.Scrollbar(list_frame, orient='vertical', command=self.reminder_tree.yview)
        self.reminder_tree.configure(yscrollcommand=scrollbar.set)
        self.reminder_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        btn_frame = self.tk.Frame(tab, bg=c['bg'])
        btn_frame.pack(fill='x', padx=16, pady=(0, 12))
        self.tk.Button(btn_frame, text="编辑", command=self._edit_reminder,
                       bg=c['border'], fg=c['fg'], relief="flat",
                       cursor="hand2", padx=12, pady=2).pack(side='left', padx=(0, 8))
        self.tk.Button(btn_frame, text="删除", command=self._delete_reminder,
                       bg=c['danger'], fg="#fff", relief="flat",
                       cursor="hand2", padx=12, pady=2).pack(side='left', padx=(0, 8))

        self._load_reminders()

    # ------------------------------------------------------------------
    # Period tab
    # ------------------------------------------------------------------

    def _create_period_tab(self):
        c = self.COLORS
        tab = self.tk.Frame(self._inner_frame, bg=c['bg'])
        self._tab_frames['period'] = tab

        self.tk.Label(tab, text="经期提醒", bg=c['bg'], fg=c['fg'],
                      font=("Microsoft YaHei", 12, "bold")).pack(anchor='w', padx=20, pady=(20, 12))

        period = self.config.config.period

        # Card: 启用
        card = self._make_card(tab)
        self.period_enabled_var = self.tk.BooleanVar(value=period.enabled)
        self.tk.Checkbutton(card, text="启用经期提醒", variable=self.period_enabled_var,
                            bg=c['entry_bg'], fg=c['fg'], selectcolor=c['entry_bg'],
                            activebackground=c['entry_bg'], activeforeground=c['fg'],
                            font=("Microsoft YaHei", 10, "bold")).pack(anchor='w')
        self.tk.Label(card, text="开启后在临近日期由宠物发送温馨提醒", bg=c['entry_bg'],
                      fg=c['text_muted'], font=("Microsoft YaHei", 9)).pack(anchor='w', pady=(2, 0))

        # Card: 提醒模式
        card = self._make_card(tab)
        self.tk.Label(card, text="提醒模式", bg=c['entry_bg'], fg=c['fg'],
                      font=("Microsoft YaHei", 10, "bold")).pack(anchor='w')
        self.tk.Label(card, text="选择使用方式以匹配合适的提醒逻辑", bg=c['entry_bg'],
                      fg=c['text_muted'], font=("Microsoft YaHei", 9)).pack(anchor='w', pady=(2, 8))
        self.period_mode_var = self.tk.StringVar(value=period.mode)
        mode_frame = self.tk.Frame(card, bg=c['entry_bg'])
        mode_frame.pack(fill='x')
        self.tk.Radiobutton(mode_frame, text="我是女生", variable=self.period_mode_var, value="self",
                            bg=c['entry_bg'], fg=c['fg'], selectcolor=c['entry_bg'],
                            activebackground=c['entry_bg'], activeforeground=c['fg'],
                            font=("Microsoft YaHei", 10)).pack(side="left", padx=(0, 20))
        self.tk.Radiobutton(mode_frame, text="伴侣提醒", variable=self.period_mode_var, value="partner",
                            bg=c['entry_bg'], fg=c['fg'], selectcolor=c['entry_bg'],
                            activebackground=c['entry_bg'], activeforeground=c['fg'],
                            font=("Microsoft YaHei", 10)).pack(side="left")

        # Card: 周期设置
        card = self._make_card(tab)
        self.tk.Label(card, text="周期设置", bg=c['entry_bg'], fg=c['fg'],
                      font=("Microsoft YaHei", 10, "bold")).pack(anchor='w')
        self.tk.Label(card, text="设置平均月经周期和经期持续天数", bg=c['entry_bg'],
                      fg=c['text_muted'], font=("Microsoft YaHei", 9)).pack(anchor='w', pady=(2, 8))
        cycle_frame = self.tk.Frame(card, bg=c['entry_bg'])
        cycle_frame.pack(fill='x')
        self.tk.Label(cycle_frame, text="周期天数", bg=c['entry_bg'], fg=c['text_secondary'],
                      font=("Microsoft YaHei", 9)).pack(side='left')
        self.cycle_days_var = self.tk.IntVar(value=period.cycle_days)
        self.tk.Spinbox(cycle_frame, textvariable=self.cycle_days_var, from_=21, to=45,
                        bg=c['bg_input'], fg=c['fg'], insertbackground=c['fg'], relief="flat",
                        font=("Microsoft YaHei", 10), width=5).pack(side='left', padx=(8, 20))
        self.tk.Label(cycle_frame, text="经期天数", bg=c['entry_bg'], fg=c['text_secondary'],
                      font=("Microsoft YaHei", 9)).pack(side='left')
        self.period_days_var = self.tk.IntVar(value=period.period_days)
        self.tk.Spinbox(cycle_frame, textvariable=self.period_days_var, from_=2, to=10,
                        bg=c['bg_input'], fg=c['fg'], insertbackground=c['fg'], relief="flat",
                        font=("Microsoft YaHei", 10), width=5).pack(side='left', padx=(8, 0))

        # Card: 上次经期日期
        card = self._make_card(tab)
        self.tk.Label(card, text="上次经期日期", bg=c['entry_bg'], fg=c['fg'],
                      font=("Microsoft YaHei", 10, "bold")).pack(anchor='w')
        self.tk.Label(card, text="填写最近一次经期的起止日期 (YYYY-MM-DD)", bg=c['entry_bg'],
                      fg=c['text_muted'], font=("Microsoft YaHei", 9)).pack(anchor='w', pady=(2, 8))
        date_frame = self.tk.Frame(card, bg=c['entry_bg'])
        date_frame.pack(fill='x')
        self.tk.Label(date_frame, text="首日:", bg=c['entry_bg'], fg=c['text_secondary'],
                      font=("Microsoft YaHei", 9)).pack(side='left')
        self.last_start_var = self.tk.StringVar(value=period.last_period_start or "")
        self.tk.Entry(date_frame, textvariable=self.last_start_var, bg=c['bg_input'],
                      fg=c['fg'], insertbackground=c['fg'], relief="flat",
                      font=("Microsoft YaHei", 10), width=12).pack(side='left', padx=(4, 16))
        self.tk.Label(date_frame, text="结束日:", bg=c['entry_bg'], fg=c['text_secondary'],
                      font=("Microsoft YaHei", 9)).pack(side='left')
        self.last_end_var = self.tk.StringVar(value=period.last_period_end or "")
        self.tk.Entry(date_frame, textvariable=self.last_end_var, bg=c['bg_input'],
                      fg=c['fg'], insertbackground=c['fg'], relief="flat",
                      font=("Microsoft YaHei", 10), width=12).pack(side='left', padx=(4, 0))

        # Card: 预测结果
        prediction = period.get_predicted_dates()
        if prediction:
            pred_text = f"预计下次经期: {prediction['predicted_start']} ~ {prediction['predicted_end']}"
            days_until = prediction['days_until']
            if days_until > 0:
                pred_text += f" (还有 {days_until} 天)"
            elif days_until == 0:
                pred_text += " (今天)"
            else:
                pred_text += f" (已过 {abs(days_until)} 天)"
        else:
            pred_text = "请填写上次经期日期后自动预测"

        pred_card = self.tk.Frame(tab, bg=c['entry_bg'], highlightbackground=c['accent'],
                                  highlightthickness=1)
        pred_card.pack(fill='x', padx=16, pady=(0, 10))
        pred_inner = self.tk.Frame(pred_card, bg=c['entry_bg'])
        pred_inner.pack(fill='x', padx=16, pady=14)
        self.tk.Label(pred_inner, text="预测结果", bg=c['entry_bg'], fg=c['fg'],
                      font=("Microsoft YaHei", 10, "bold")).pack(anchor='w')
        self.pred_label = self.tk.Label(pred_inner, text=pred_text, bg=c['entry_bg'],
                                        fg=c['accent'], font=("Microsoft YaHei", 10), wraplength=400)
        self.pred_label.pack(anchor='w', pady=(4, 0))

        # Card: 校准调整
        card = self._make_card(tab)
        self.tk.Label(card, text="校准调整", bg=c['entry_bg'], fg=c['fg'],
                      font=("Microsoft YaHei", 10, "bold")).pack(anchor='w')
        self.tk.Label(card, text="如果预测有偏差，可手动微调偏移天数", bg=c['entry_bg'],
                      fg=c['text_muted'], font=("Microsoft YaHei", 9)).pack(anchor='w', pady=(2, 8))
        calib_frame = self.tk.Frame(card, bg=c['entry_bg'])
        calib_frame.pack(fill='x')
        self.tk.Label(calib_frame, text="偏移天数:", bg=c['entry_bg'], fg=c['text_secondary'],
                      font=("Microsoft YaHei", 10)).pack(side='left')
        self.calib_offset_var = self.tk.IntVar(value=period.calibration_offset)
        self.calib_label = self.tk.Label(calib_frame, text=str(period.calibration_offset),
                                         bg=c['entry_bg'], fg=c['accent'],
                                         font=("Microsoft YaHei", 11, "bold"), width=4)
        self.calib_label.pack(side='left', padx=4)
        self.tk.Button(calib_frame, text="-1天", command=lambda: self._adjust_calibration(-1),
                       bg=c['bg_input'], fg=c['text_secondary'], relief="flat",
                       cursor="hand2", padx=8, pady=2).pack(side='left', padx=(8, 4))
        self.tk.Button(calib_frame, text="+1天", command=lambda: self._adjust_calibration(1),
                       bg=c['bg_input'], fg=c['text_secondary'], relief="flat",
                       cursor="hand2", padx=8, pady=2).pack(side='left', padx=(4, 16))
        self.tk.Button(calib_frame, text="重置", command=lambda: self._adjust_calibration(0, reset=True),
                       bg=c['bg_input'], fg=c['text_muted'], relief="flat",
                       cursor="hand2", padx=8, pady=2).pack(side='left')

        # Card: 历史记录
        if period.records:
            card = self._make_card(tab)
            self.tk.Label(card, text="历史记录（最近 3 次）", bg=c['entry_bg'], fg=c['fg'],
                          font=("Microsoft YaHei", 10, "bold")).pack(anchor='w')
            for i, record in enumerate(period.records[-3:]):
                days = record.actual_days if record.actual_days else period.period_days
                record_text = f"{record.start_date} ~ {record.end_date}"
                row = self.tk.Frame(card, bg=c['entry_bg'])
                row.pack(fill='x', pady=(4, 0))
                self.tk.Label(row, text=record_text, bg=c['entry_bg'], fg=c['fg'],
                              font=("Microsoft YaHei", 9)).pack(side='left')
                self.tk.Label(row, text=f"{days} 天", bg=c['bg_input'], fg=c['text_muted'],
                              font=("Microsoft YaHei", 9), padx=6).pack(side='right')

        self.tk.Frame(tab, height=12, bg=c['bg']).pack()

    def _adjust_calibration(self, delta, reset=False):
        if reset:
            new_offset = 0
        else:
            new_offset = self.calib_offset_var.get() + delta
        self.calib_offset_var.set(new_offset)
        self.calib_label.config(text=str(new_offset))

    # ------------------------------------------------------------------
    # Bottom buttons
    # ------------------------------------------------------------------

    def _create_buttons(self):
        """创建底部按钮（带分割线，匹配原型按钮样式）"""
        c = self.COLORS
        self.button_frame = self.tk.Frame(self.window, bg=c['bg'])
        self.button_frame.pack(side='bottom', fill='x')

        # 分割线
        self.tk.Frame(self.button_frame, height=1, bg=c['border']).pack(fill='x')

        btn_inner = self.tk.Frame(self.button_frame, bg=c['bg'])
        btn_inner.pack(fill='x', padx=20, pady=12)

        self.tk.Button(btn_inner, text="保存", command=self._save,
                       bg=c['accent'], fg="#fff", relief="flat", cursor="hand2",
                       padx=28, pady=6, font=("Microsoft YaHei", 10, "bold")).pack(side='right', padx=(8, 0))

        self.tk.Button(btn_inner, text="取消", command=self.window.destroy,
                       bg=c['bg'], fg=c['text_secondary'], relief="flat", cursor="hand2",
                       padx=20, pady=6, font=("Microsoft YaHei", 10),
                       highlightbackground=c['border'], highlightthickness=1).pack(side='right')

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _browse_dir(self):
        d = self._filedialog.askdirectory(title="选择归档目录", initialdir=self.dir_var.get())
        if d:
            self.dir_var.set(d)

    def _fmt_scale(self, v):
        return f"{int(float(v)*100)}%"

    def _on_scale_change(self, v):
        self.scale_label.config(text=self._fmt_scale(v))

    def _test_connection(self):
        config = {
            'enabled': True,
            'agent_type': self.agent_type_var.get(),
            'endpoint': self.endpoint_var.get(),
            'api_key': self.token_var.get(),
            'timeout': self.timeout_var.get()
        }
        try:
            import requests
            response = requests.get(f"{config['endpoint']}/health", timeout=5)
            if response.status_code == 200:
                self._messagebox.showinfo("测试连接", "连接成功！", parent=self.window)
            else:
                self._messagebox.showwarning("测试连接", f"连接失败：HTTP {response.status_code}",
                                             parent=self.window)
        except requests.Timeout:
            self._messagebox.showerror("测试连接", "连接超时", parent=self.window)
        except Exception as e:
            self._messagebox.showerror("测试连接", f"连接失败：{str(e)}", parent=self.window)

    def _load_reminders(self):
        reminders = self.config.reminders
        for item in self.reminder_tree.get_children():
            self.reminder_tree.delete(item)
        for reminder in reminders:
            data = reminder.to_dict() if hasattr(reminder, "to_dict") else reminder
            status = "启用" if data.get('enabled', True) else "禁用"
            self.reminder_tree.insert('', 'end', values=(
                data.get('name', ''), data.get('time', ''),
                data.get('repeat', '不重复'), status))

    def _add_reminder(self):
        ReminderDialog(self.window, callback=self._on_reminder_added, colors=self.COLORS)

    def _edit_reminder(self):
        selected = self.reminder_tree.selection()
        if not selected:
            self._messagebox.showwarning("提示", "请先选择一个提醒", parent=self.window)
            return
        item = self.reminder_tree.item(selected[0])
        values = item['values']
        reminders = self.config.reminders
        for reminder in reminders:
            data = reminder.to_dict() if hasattr(reminder, "to_dict") else reminder
            if data.get('name') == values[0]:
                ReminderDialog(self.window, reminder=data, callback=self._on_reminder_updated,
                               colors=self.COLORS)
                break

    def _delete_reminder(self):
        selected = self.reminder_tree.selection()
        if not selected:
            self._messagebox.showwarning("提示", "请先选择一个提醒", parent=self.window)
            return
        if not self._messagebox.askyesno("确认", "确定要删除这个提醒吗？", parent=self.window):
            return
        item = self.reminder_tree.item(selected[0])
        name = item['values'][0]
        reminders = self.config.reminders
        reminders = [
            r for r in reminders
            if (r.to_dict() if hasattr(r, "to_dict") else r).get('name') != name
        ]
        self.config.set('reminders', reminders)
        self._load_reminders()

    def _on_reminder_added(self, reminder):
        from ..core.types import Reminder
        reminders = self.config.reminders
        reminders.append(Reminder.from_dict(reminder))
        self.config.set('reminders', reminders)
        self._load_reminders()

    def _on_reminder_updated(self, reminder):
        from ..core.types import Reminder
        updated = Reminder.from_dict(reminder)
        reminders = self.config.reminders
        for i, r in enumerate(reminders):
            data = r.to_dict() if hasattr(r, "to_dict") else r
            if data.get('name') == reminder.get('name'):
                reminders[i] = updated
                break
        self.config.set('reminders', reminders)
        self._load_reminders()

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def _save(self):
        from ..core.types import AgentType, FileAction, PeriodRecord

        self.config.set('archive_dir', self.dir_var.get().strip())
        self.config.set('scale', round(self.scale_var.get(), 2))
        self.config.set('screenshot_action', FileAction(self.ss_var.get()))

        try:
            self.config.set('color_mode', self.color_mode_var.get())
        except Exception:
            pass

        agent_config = self.config.agent_config
        agent_config.enabled = self.ai_enabled_var.get()
        agent_config.agent_type = AgentType(self.agent_type_var.get())
        agent_config.endpoint = self.endpoint_var.get().strip()
        agent_config.api_key = self.token_var.get().strip()
        agent_config.timeout = self.timeout_var.get()
        self.config.config.agent = agent_config

        period = self.config.config.period
        period.enabled = self.period_enabled_var.get()
        period.mode = self.period_mode_var.get()
        period.cycle_days = self.cycle_days_var.get()
        period.period_days = self.period_days_var.get()

        new_start = self.last_start_var.get().strip()
        new_end = self.last_end_var.get().strip()
        if new_start and new_start != period.last_period_start:
            period.last_period_start = new_start
            if new_end:
                period.last_period_end = new_end
                actual_days = 5
                try:
                    start = datetime.strptime(new_start, '%Y-%m-%d')
                    end = datetime.strptime(new_end, '%Y-%m-%d')
                    actual_days = (end - start).days + 1
                except:
                    pass
                record = PeriodRecord(start_date=new_start, end_date=new_end, actual_days=actual_days)
                period.records.append(record)
                if len(period.records) > 6:
                    period.records = period.records[-6:]

        period.calibration_offset = self.calib_offset_var.get()
        self.config.config.period = period

        try:
            self.config.set('launch_at_startup', bool(self.launch_var.get()))
        except Exception:
            pass
        try:
            self.config.config.launch_at_startup = bool(self.launch_var.get())
        except Exception:
            pass

        self.config.save()
        if self.on_save_callback:
            self.on_save_callback()
        self._messagebox.showinfo("设置", "设置已保存！", parent=self.window)
        self.window.destroy()


# ======================================================================
# ReminderDialog
# ======================================================================

class ReminderDialog:
    """提醒编辑对话框"""

    REPEAT_OPTIONS = ['不重复', '每天', '每周', '每月', '每年']

    def __init__(self, parent, reminder: Optional[Dict] = None,
                 callback: Optional[Callable] = None, colors=None):
        import tkinter as tk
        from tkinter import ttk, messagebox
        self.tk = tk
        self.ttk = ttk
        self._messagebox = messagebox

        self.parent = parent
        self.reminder = reminder or {}
        self.callback = callback
        self.COLORS = colors or dict(DARK_COLORS)
        c = self.COLORS

        self.dialog = self.tk.Toplevel(parent)
        self.dialog.title("编辑提醒" if reminder else "添加提醒")
        self.dialog.configure(bg=c['bg'])
        self.dialog.resizable(False, False)

        self.dialog.update_idletasks()
        sw = self.dialog.winfo_screenwidth()
        sh = self.dialog.winfo_screenheight()
        ww, wh = 360, 320
        self.dialog.geometry(f"{ww}x{wh}+{(sw-ww)//2}+{(sh-wh)//2}")
        self.dialog.attributes("-topmost", True)
        self.dialog.grab_set()

        self._create_form()

    def _create_form(self):
        c = self.COLORS
        bg, fg, entry_bg = c['bg'], c['fg'], c['entry_bg']
        row = 0

        self.tk.Label(self.dialog, text="提醒名称", bg=bg, fg=fg,
                      anchor="w", font=("Microsoft YaHei", 10)).grid(
            row=row, column=0, sticky="w", padx=20, pady=(20, 4))
        row += 1
        self.name_var = self.tk.StringVar(value=self.reminder.get('name', ''))
        self.tk.Entry(self.dialog, textvariable=self.name_var, bg=entry_bg, fg=fg,
                      insertbackground=fg, relief="flat", font=("Microsoft YaHei", 10)).grid(
            row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 8))
        row += 1

        self.tk.Label(self.dialog, text="提醒时间 (HH:MM)", bg=bg, fg=fg,
                      anchor="w", font=("Microsoft YaHei", 10)).grid(
            row=row, column=0, sticky="w", padx=20, pady=(8, 4))
        row += 1
        self.time_var = self.tk.StringVar(value=self.reminder.get('time', '09:00'))
        self.tk.Entry(self.dialog, textvariable=self.time_var, bg=entry_bg, fg=fg,
                      insertbackground=fg, relief="flat", font=("Microsoft YaHei", 10)).grid(
            row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 8))
        row += 1

        self.tk.Label(self.dialog, text="重复方式", bg=bg, fg=fg,
                      anchor="w", font=("Microsoft YaHei", 10)).grid(
            row=row, column=0, sticky="w", padx=20, pady=(8, 4))
        row += 1
        self.repeat_var = self.tk.StringVar(value=self.reminder.get('repeat', '不重复'))
        combo = self.ttk.Combobox(self.dialog, textvariable=self.repeat_var,
                                  values=self.REPEAT_OPTIONS, state='readonly',
                                  font=("Microsoft YaHei", 10))
        combo.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 8))
        row += 1

        self.tk.Label(self.dialog, text="提醒内容", bg=bg, fg=fg,
                      anchor="w", font=("Microsoft YaHei", 10)).grid(
            row=row, column=0, sticky="w", padx=20, pady=(8, 4))
        row += 1
        self.content_var = self.tk.StringVar(value=self.reminder.get('content', ''))
        self.tk.Entry(self.dialog, textvariable=self.content_var, bg=entry_bg, fg=fg,
                      insertbackground=fg, relief="flat", font=("Microsoft YaHei", 10)).grid(
            row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 8))
        row += 1

        self.enabled_var = self.tk.BooleanVar(value=self.reminder.get('enabled', True))
        self.tk.Checkbutton(self.dialog, text="启用提醒", variable=self.enabled_var,
                            bg=bg, fg=fg, selectcolor=bg, activebackground=bg,
                            activeforeground=fg, font=("Microsoft YaHei", 10)).grid(
            row=row, column=0, sticky="w", padx=20, pady=(8, 4))
        row += 1

        btn_frame = self.tk.Frame(self.dialog, bg=bg)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=(16, 20))
        self.tk.Button(btn_frame, text="确定", command=self._ok,
                       bg=c['accent'], fg="#fff", relief="flat",
                       cursor="hand2", padx=24, pady=4).pack(side='left', padx=8)
        self.tk.Button(btn_frame, text="取消", command=self.dialog.destroy,
                       bg=c['border'], fg=fg, relief="flat",
                       cursor="hand2", padx=16, pady=4).pack(side='left', padx=8)

    def _ok(self):
        name = self.name_var.get().strip()
        time_str = self.time_var.get().strip()
        if not name:
            self._messagebox.showwarning("提示", "请输入提醒名称", parent=self.dialog)
            return
        if not time_str:
            self._messagebox.showwarning("提示", "请输入提醒时间", parent=self.dialog)
            return
        try:
            datetime.strptime(time_str, '%H:%M')
        except ValueError:
            self._messagebox.showwarning("提示", "时间格式不正确，请使用 HH:MM 格式", parent=self.dialog)
            return
        reminder = {
            'name': name, 'time': time_str, 'repeat': self.repeat_var.get(),
            'content': self.content_var.get().strip(), 'enabled': self.enabled_var.get()
        }
        if self.callback:
            self.callback(reminder)
        self.dialog.destroy()
