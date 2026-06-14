"""
设置面板模块
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Callable, Optional
from datetime import datetime


class SettingsPanel:
    """设置面板"""
    
    # 颜色配置
    COLORS = {
        'bg': '#1a1d27',
        'fg': '#e2e8f0',
        'entry_bg': '#242837',
        'accent': '#6366f1',
        'accent_hover': '#818cf8',
        'danger': '#ef4444',
        'success': '#22c55e',
        'warning': '#f59e0b',
        'border': '#374151',
    }
    
    def __init__(self, parent, config, on_save_callback: Optional[Callable] = None):
        """
        初始化设置面板
        
        Args:
            parent: 父窗口
            config: ConfigManager 实例
            on_save_callback: 保存后的回调函数
        """
        self.parent = parent
        self.config = config
        self.on_save_callback = on_save_callback
        
        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("设置")
        self.window.configure(bg=self.COLORS['bg'])
        self.window.resizable(False, False)
        
        # 居中显示
        self.window.update_idletasks()
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        ww, wh = 520, 600
        self.window.geometry(f"{ww}x{wh}+{(sw-ww)//2}+{(sh-wh)//2}")
        self.window.attributes("-topmost", True)
        self.window.grab_set()
        
        # 创建选项卡
        self._create_notebook()

        # 创建底部按钮（必须在 notebook 之后创建并 pack(side='bottom')，
        # 否则 notebook 先占满窗口会导致按钮被挤出可视区域）
        self._create_buttons()
    
    def _create_notebook(self):
        """创建选项卡控件"""
        style = ttk.Style()
        style.theme_use('default')
        
        # 配置选项卡样式
        style.configure('TNotebook', background=self.COLORS['bg'])
        style.configure('TNotebook.Tab', 
                       background=self.COLORS['entry_bg'],
                       foreground=self.COLORS['fg'],
                       padding=[12, 4],
                       font=('Microsoft YaHei', 9))
        style.map('TNotebook.Tab',
                 background=[('selected', self.COLORS['accent'])],
                 foreground=[('selected', '#ffffff')])
        
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(side='top', fill='both', expand=True, padx=10, pady=(10, 8))
        
        # 创建各个选项卡
        self._create_general_tab()
        self._create_ai_tab()
        self._create_reminder_tab()
        self._create_period_tab()
    
    def _create_general_tab(self):
        """创建常规设置选项卡"""
        tab = tk.Frame(self.notebook, bg=self.COLORS['bg'])
        self.notebook.add(tab, text='  常规  ')
        
        row = 0
        
        # 归档目录
        tk.Label(tab, text="归档目录", bg=self.COLORS['bg'], fg=self.COLORS['fg'],
                 anchor="w", font=("Microsoft YaHei", 10, "bold")).grid(
            row=row, column=0, sticky="w", padx=20, pady=(20, 4))
        row += 1
        
        dir_frame = tk.Frame(tab, bg=self.COLORS['bg'])
        dir_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 4))
        
        self.dir_var = tk.StringVar(value=self.config.archive_dir)
        dir_entry = tk.Entry(dir_frame, textvariable=self.dir_var, bg=self.COLORS['entry_bg'],
                            fg=self.COLORS['fg'], insertbackground=self.COLORS['fg'],
                            relief="flat", font=("Microsoft YaHei", 10))
        dir_entry.pack(side='left', fill='x', expand=True, padx=(0, 8))
        
        tk.Button(dir_frame, text="浏览...", command=self._browse_dir,
                 bg=self.COLORS['accent'], fg="#fff", relief="flat",
                 cursor="hand2", padx=12).pack(side='right')
        row += 1
        
        # 宠物大小
        tk.Label(tab, text="宠物大小", bg=self.COLORS['bg'], fg=self.COLORS['fg'],
                 anchor="w", font=("Microsoft YaHei", 10, "bold")).grid(
            row=row, column=0, sticky="w", padx=20, pady=(16, 4))
        row += 1
        
        scale_frame = tk.Frame(tab, bg=self.COLORS['bg'])
        scale_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 4))
        
        self.scale_var = tk.DoubleVar(value=self.config.config.scale)
        
        self.scale_label = tk.Label(scale_frame, text=self._fmt_scale(self.scale_var.get()),
                                    bg=self.COLORS['bg'], fg=self.COLORS['accent'],
                                    font=("Microsoft YaHei", 10, "bold"), width=6)
        self.scale_label.pack(side='right')
        
        scale_slider = tk.Scale(scale_frame, from_=0.3, to=1.0, resolution=0.05,
                                orient="horizontal", variable=self.scale_var,
                                bg=self.COLORS['bg'], fg=self.COLORS['fg'],
                                troughcolor=self.COLORS['entry_bg'],
                                highlightthickness=0, label="", showvalue=False,
                                length=300, command=self._on_scale_change)
        scale_slider.pack(side='left', fill='x', expand=True)
        row += 1
        
        # 截图处理
        tk.Label(tab, text="截图处理", bg=self.COLORS['bg'], fg=self.COLORS['fg'],
                 anchor="w", font=("Microsoft YaHei", 10, "bold")).grid(
            row=row, column=0, sticky="w", padx=20, pady=(16, 4))
        row += 1
        
        self.ss_var = tk.StringVar(value=self.config.config.screenshot_action.value)
        ss_frame = tk.Frame(tab, bg=self.COLORS['bg'])
        ss_frame.grid(row=row, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 4))
        
        tk.Radiobutton(ss_frame, text="移入回收站", variable=self.ss_var, value="recycle",
                       bg=self.COLORS['bg'], fg=self.COLORS['fg'],
                       selectcolor=self.COLORS['bg'], activebackground=self.COLORS['bg'],
                       activeforeground=self.COLORS['fg'],
                       font=("Microsoft YaHei", 10)).pack(side="left", padx=(0, 20))
        tk.Radiobutton(ss_frame, text="保留到图片", variable=self.ss_var, value="archive",
                       bg=self.COLORS['bg'], fg=self.COLORS['fg'],
                       selectcolor=self.COLORS['bg'], activebackground=self.COLORS['bg'],
                       activeforeground=self.COLORS['fg'],
                       font=("Microsoft YaHei", 10)).pack(side="left")
    
    def _create_ai_tab(self):
        """创建 AI 助手选项卡"""
        tab = tk.Frame(self.notebook, bg=self.COLORS['bg'])
        self.notebook.add(tab, text='  AI 助手  ')
        
        row = 0
        
        # 启用 AI 助手
        self.ai_enabled_var = tk.BooleanVar(value=self.config.agent_config.enabled)
        tk.Checkbutton(tab, text="启用 AI 助手", variable=self.ai_enabled_var,
                      bg=self.COLORS['bg'], fg=self.COLORS['fg'],
                      selectcolor=self.COLORS['bg'], activebackground=self.COLORS['bg'],
                      activeforeground=self.COLORS['fg'],
                      font=("Microsoft YaHei", 10, "bold")).grid(
            row=row, column=0, sticky="w", padx=20, pady=(20, 8))
        row += 1
        
        # 网关类型
        tk.Label(tab, text="网关类型", bg=self.COLORS['bg'], fg=self.COLORS['fg'],
                 anchor="w", font=("Microsoft YaHei", 10)).grid(
            row=row, column=0, sticky="w", padx=20, pady=(8, 4))
        
        self.agent_type_var = tk.StringVar(value=self.config.agent_config.agent_type.value)
        type_frame = tk.Frame(tab, bg=self.COLORS['bg'])
        type_frame.grid(row=row, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 4))
        
        for value, text in [('openclaw', 'OpenClaw'), ('hermes', 'Hermes'), ('custom', '自定义')]:
            tk.Radiobutton(type_frame, text=text, variable=self.agent_type_var, value=value,
                          bg=self.COLORS['bg'], fg=self.COLORS['fg'],
                          selectcolor=self.COLORS['bg'], activebackground=self.COLORS['bg'],
                          activeforeground=self.COLORS['fg'],
                          font=("Microsoft YaHei", 10)).pack(side="left", padx=(0, 16))
        row += 1
        
        # 网关地址
        tk.Label(tab, text="网关地址", bg=self.COLORS['bg'], fg=self.COLORS['fg'],
                 anchor="w", font=("Microsoft YaHei", 10)).grid(
            row=row, column=0, sticky="w", padx=20, pady=(8, 4))
        row += 1
        
        self.endpoint_var = tk.StringVar(value=self.config.agent_config.endpoint)
        tk.Entry(tab, textvariable=self.endpoint_var, bg=self.COLORS['entry_bg'],
                fg=self.COLORS['fg'], insertbackground=self.COLORS['fg'],
                relief="flat", font=("Microsoft YaHei", 10)).grid(
            row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 4))
        row += 1
        
        # API Token
        tk.Label(tab, text="API Token", bg=self.COLORS['bg'], fg=self.COLORS['fg'],
                 anchor="w", font=("Microsoft YaHei", 10)).grid(
            row=row, column=0, sticky="w", padx=20, pady=(8, 4))
        row += 1
        
        self.token_var = tk.StringVar(value=self.config.agent_config.api_key)
        tk.Entry(tab, textvariable=self.token_var, bg=self.COLORS['entry_bg'],
                fg=self.COLORS['fg'], insertbackground=self.COLORS['fg'],
                relief="flat", font=("Microsoft YaHei", 10), show="*").grid(
            row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 4))
        row += 1
        
        # 超时时间
        tk.Label(tab, text="请求超时（秒）", bg=self.COLORS['bg'], fg=self.COLORS['fg'],
                 anchor="w", font=("Microsoft YaHei", 10)).grid(
            row=row, column=0, sticky="w", padx=20, pady=(8, 4))
        
        self.timeout_var = tk.IntVar(value=self.config.agent_config.timeout)
        tk.Spinbox(tab, textvariable=self.timeout_var, from_=5, to=120,
                  bg=self.COLORS['entry_bg'], fg=self.COLORS['fg'],
                  insertbackground=self.COLORS['fg'], relief="flat",
                  font=("Microsoft YaHei", 10), width=10).grid(
            row=row, column=1, sticky="w", padx=20, pady=(8, 4))
        row += 1
        
        # 测试连接按钮
        tk.Button(tab, text="测试连接", command=self._test_connection,
                 bg=self.COLORS['accent'], fg="#fff", relief="flat",
                 cursor="hand2", padx=20, pady=4).grid(
            row=row, column=0, columnspan=2, pady=(20, 4))
    
    def _create_reminder_tab(self):
        """创建定时提醒选项卡"""
        tab = tk.Frame(self.notebook, bg=self.COLORS['bg'])
        self.notebook.add(tab, text='  定时提醒  ')
        
        # 提醒列表
        list_frame = tk.Frame(tab, bg=self.COLORS['bg'])
        list_frame.pack(fill='both', expand=True, padx=20, pady=(20, 10))
        
        # 标题栏
        header_frame = tk.Frame(list_frame, bg=self.COLORS['bg'])
        header_frame.pack(fill='x', pady=(0, 8))
        
        tk.Label(header_frame, text="提醒列表", bg=self.COLORS['bg'], fg=self.COLORS['fg'],
                 font=("Microsoft YaHei", 10, "bold")).pack(side='left')
        
        tk.Button(header_frame, text="+ 添加提醒", command=self._add_reminder,
                 bg=self.COLORS['accent'], fg="#fff", relief="flat",
                 cursor="hand2", padx=8, pady=2).pack(side='right')
        
        # 提醒列表（使用 Treeview）
        columns = ('name', 'time', 'repeat', 'enabled')
        self.reminder_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        
        # 配置列
        self.reminder_tree.heading('name', text='名称')
        self.reminder_tree.heading('time', text='时间')
        self.reminder_tree.heading('repeat', text='重复')
        self.reminder_tree.heading('enabled', text='状态')
        
        self.reminder_tree.column('name', width=150)
        self.reminder_tree.column('time', width=100)
        self.reminder_tree.column('repeat', width=100)
        self.reminder_tree.column('enabled', width=60, anchor='center')
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.reminder_tree.yview)
        self.reminder_tree.configure(yscrollcommand=scrollbar.set)
        
        self.reminder_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 操作按钮
        btn_frame = tk.Frame(tab, bg=self.COLORS['bg'])
        btn_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        tk.Button(btn_frame, text="编辑", command=self._edit_reminder,
                 bg=self.COLORS['border'], fg=self.COLORS['fg'], relief="flat",
                 cursor="hand2", padx=12, pady=2).pack(side='left', padx=(0, 8))
        
        tk.Button(btn_frame, text="删除", command=self._delete_reminder,
                 bg=self.COLORS['danger'], fg="#fff", relief="flat",
                 cursor="hand2", padx=12, pady=2).pack(side='left', padx=(0, 8))
        
        # 加载提醒数据
        self._load_reminders()
    
    def _create_buttons(self):
        """创建底部按钮"""
        self.button_frame = tk.Frame(self.window, bg=self.COLORS['bg'])
        self.button_frame.pack(side='bottom', fill='x', padx=20, pady=(0, 16))
        btn_frame = self.button_frame
        
        tk.Button(btn_frame, text="保存", command=self._save,
                 bg=self.COLORS['accent'], fg="#fff", relief="flat",
                 cursor="hand2", padx=32, pady=6,
                 font=("Microsoft YaHei", 10, "bold")).pack(side='right', padx=(8, 0))
        
        tk.Button(btn_frame, text="取消", command=self.window.destroy,
                 bg=self.COLORS['border'], fg=self.COLORS['fg'], relief="flat",
                 cursor="hand2", padx=20, pady=6,
                 font=("Microsoft YaHei", 10)).pack(side='right')
    
    def _browse_dir(self):
        """浏览目录"""
        d = filedialog.askdirectory(title="选择归档目录", initialdir=self.dir_var.get())
        if d:
            self.dir_var.set(d)
    
    def _fmt_scale(self, v):
        """格式化缩放值"""
        return f"{int(float(v)*100)}%"
    
    def _on_scale_change(self, v):
        """缩放值变化"""
        self.scale_label.config(text=self._fmt_scale(v))
    
    def _test_connection(self):
        """测试 AI 网关连接"""
        config = {
            'enabled': True,
            'agent_type': self.agent_type_var.get(),
            'endpoint': self.endpoint_var.get(),
            'api_key': self.token_var.get(),
            'timeout': self.timeout_var.get()
        }
        
        # 测试连接
        try:
            import requests
            response = requests.get(f"{config['endpoint']}/health", timeout=5)
            if response.status_code == 200:
                messagebox.showinfo("测试连接", "连接成功！", parent=self.window)
            else:
                messagebox.showwarning("测试连接", f"连接失败：HTTP {response.status_code}",
                                      parent=self.window)
        except requests.Timeout:
            messagebox.showerror("测试连接", "连接超时", parent=self.window)
        except Exception as e:
            messagebox.showerror("测试连接", f"连接失败：{str(e)}", parent=self.window)
    
    def _load_reminders(self):
        """加载提醒列表"""
        reminders = self.config.reminders
        
        # 清空列表
        for item in self.reminder_tree.get_children():
            self.reminder_tree.delete(item)
        
        # 添加提醒
        for reminder in reminders:
            data = reminder.to_dict() if hasattr(reminder, "to_dict") else reminder
            status = "启用" if data.get('enabled', True) else "禁用"
            self.reminder_tree.insert('', 'end', values=(
                data.get('name', ''),
                data.get('time', ''),
                data.get('repeat', '不重复'),
                status
            ))
    
    def _add_reminder(self):
        """添加提醒"""
        ReminderDialog(self.window, callback=self._on_reminder_added)
    
    def _edit_reminder(self):
        """编辑提醒"""
        selected = self.reminder_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一个提醒", parent=self.window)
            return
        
        # 获取选中的提醒数据
        item = self.reminder_tree.item(selected[0])
        values = item['values']
        
        reminders = self.config.reminders
        for reminder in reminders:
            data = reminder.to_dict() if hasattr(reminder, "to_dict") else reminder
            if data.get('name') == values[0]:
                ReminderDialog(self.window, reminder=data, callback=self._on_reminder_updated)
                break
    
    def _delete_reminder(self):
        """删除提醒"""
        selected = self.reminder_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一个提醒", parent=self.window)
            return
        
        if not messagebox.askyesno("确认", "确定要删除这个提醒吗？", parent=self.window):
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
        """提醒添加回调"""
        from ..core.types import Reminder

        reminders = self.config.reminders
        reminders.append(Reminder.from_dict(reminder))
        self.config.set('reminders', reminders)
        self._load_reminders()
    
    def _on_reminder_updated(self, reminder):
        """提醒更新回调"""
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
    
    def _save(self):
        """保存设置"""
        from ..core.types import AgentType, FileAction, PeriodRecord

        # 保存常规设置
        self.config.set('archive_dir', self.dir_var.get().strip())
        self.config.set('scale', round(self.scale_var.get(), 2))
        self.config.set('screenshot_action', FileAction(self.ss_var.get()))

        # 保存 AI 设置
        agent_config = self.config.agent_config
        agent_config.enabled = self.ai_enabled_var.get()
        agent_config.agent_type = AgentType(self.agent_type_var.get())
        agent_config.endpoint = self.endpoint_var.get().strip()
        agent_config.api_key = self.token_var.get().strip()
        agent_config.timeout = self.timeout_var.get()
        self.config.config.agent = agent_config

        # 保存经期提醒设置
        period = self.config.config.period
        period.enabled = self.period_enabled_var.get()
        period.mode = self.period_mode_var.get()
        period.cycle_days = self.cycle_days_var.get()
        period.period_days = self.period_days_var.get()

        # 更新经期日期
        new_start = self.last_start_var.get().strip()
        new_end = self.last_end_var.get().strip()

        if new_start and new_start != period.last_period_start:
            period.last_period_start = new_start
            # 添加到历史记录
            if new_end:
                period.last_period_end = new_end
                actual_days = 5  # 默认
                try:
                    from datetime import datetime
                    start = datetime.strptime(new_start, '%Y-%m-%d')
                    end = datetime.strptime(new_end, '%Y-%m-%d')
                    actual_days = (end - start).days + 1
                except:
                    pass
                record = PeriodRecord(start_date=new_start, end_date=new_end, actual_days=actual_days)
                period.records.append(record)
                # 只保留最近6次记录
                if len(period.records) > 6:
                    period.records = period.records[-6:]

        # 保存校准偏移
        period.calibration_offset = self.calib_offset_var.get()

        self.config.config.period = period

        # 保存配置
        self.config.save()

        # 触发回调
        if self.on_save_callback:
            self.on_save_callback()

        messagebox.showinfo("设置", "设置已保存！", parent=self.window)
        self.window.destroy()


class ReminderDialog:
    """提醒编辑对话框"""
    
    REPEAT_OPTIONS = ['不重复', '每天', '每周', '每月', '每年']
    
    def __init__(self, parent, reminder: Optional[Dict] = None, callback: Optional[Callable] = None):
        self.parent = parent
        self.reminder = reminder or {}
        self.callback = callback
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("编辑提醒" if reminder else "添加提醒")
        self.dialog.configure(bg='#1a1d27')
        self.dialog.resizable(False, False)
        
        # 居中显示
        self.dialog.update_idletasks()
        sw = self.dialog.winfo_screenwidth()
        sh = self.dialog.winfo_screenheight()
        ww, wh = 360, 320
        self.dialog.geometry(f"{ww}x{wh}+{(sw-ww)//2}+{(sh-wh)//2}")
        self.dialog.attributes("-topmost", True)
        self.dialog.grab_set()
        
        self._create_form()
    
    def _create_form(self):
        """创建表单"""
        bg = '#1a1d27'
        fg = '#e2e8f0'
        entry_bg = '#242837'
        
        row = 0
        
        # 名称
        tk.Label(self.dialog, text="提醒名称", bg=bg, fg=fg,
                 anchor="w", font=("Microsoft YaHei", 10)).grid(
            row=row, column=0, sticky="w", padx=20, pady=(20, 4))
        row += 1
        
        self.name_var = tk.StringVar(value=self.reminder.get('name', ''))
        tk.Entry(self.dialog, textvariable=self.name_var, bg=entry_bg, fg=fg,
                insertbackground=fg, relief="flat", font=("Microsoft YaHei", 10)).grid(
            row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 8))
        row += 1
        
        # 时间
        tk.Label(self.dialog, text="提醒时间 (HH:MM)", bg=bg, fg=fg,
                 anchor="w", font=("Microsoft YaHei", 10)).grid(
            row=row, column=0, sticky="w", padx=20, pady=(8, 4))
        row += 1
        
        self.time_var = tk.StringVar(value=self.reminder.get('time', '09:00'))
        tk.Entry(self.dialog, textvariable=self.time_var, bg=entry_bg, fg=fg,
                insertbackground=fg, relief="flat", font=("Microsoft YaHei", 10)).grid(
            row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 8))
        row += 1
        
        # 重复
        tk.Label(self.dialog, text="重复方式", bg=bg, fg=fg,
                 anchor="w", font=("Microsoft YaHei", 10)).grid(
            row=row, column=0, sticky="w", padx=20, pady=(8, 4))
        row += 1
        
        self.repeat_var = tk.StringVar(value=self.reminder.get('repeat', '不重复'))
        combo = ttk.Combobox(self.dialog, textvariable=self.repeat_var,
                            values=self.REPEAT_OPTIONS, state='readonly',
                            font=("Microsoft YaHei", 10))
        combo.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 8))
        row += 1
        
        # 提醒内容
        tk.Label(self.dialog, text="提醒内容", bg=bg, fg=fg,
                 anchor="w", font=("Microsoft YaHei", 10)).grid(
            row=row, column=0, sticky="w", padx=20, pady=(8, 4))
        row += 1
        
        self.content_var = tk.StringVar(value=self.reminder.get('content', ''))
        tk.Entry(self.dialog, textvariable=self.content_var, bg=entry_bg, fg=fg,
                insertbackground=fg, relief="flat", font=("Microsoft YaHei", 10)).grid(
            row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 8))
        row += 1
        
        # 启用状态
        self.enabled_var = tk.BooleanVar(value=self.reminder.get('enabled', True))
        tk.Checkbutton(self.dialog, text="启用提醒", variable=self.enabled_var,
                      bg=bg, fg=fg, selectcolor=bg, activebackground=bg,
                      activeforeground=fg, font=("Microsoft YaHei", 10)).grid(
            row=row, column=0, sticky="w", padx=20, pady=(8, 4))
        row += 1
        
        # 按钮
        btn_frame = tk.Frame(self.dialog, bg=bg)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=(16, 20))
        
        tk.Button(btn_frame, text="确定", command=self._ok,
                 bg='#6366f1', fg="#fff", relief="flat",
                 cursor="hand2", padx=24, pady=4).pack(side='left', padx=8)
        
        tk.Button(btn_frame, text="取消", command=self.dialog.destroy,
                 bg='#374151', fg=fg, relief="flat",
                 cursor="hand2", padx=16, pady=4).pack(side='left', padx=8)
    
    def _ok(self):
        """确定"""
        name = self.name_var.get().strip()
        time_str = self.time_var.get().strip()
        
        if not name:
            messagebox.showwarning("提示", "请输入提醒名称", parent=self.dialog)
            return
        
        if not time_str:
            messagebox.showwarning("提示", "请输入提醒时间", parent=self.dialog)
            return
        
        # 验证时间格式
        try:
            datetime.strptime(time_str, '%H:%M')
        except ValueError:
            messagebox.showwarning("提示", "时间格式不正确，请使用 HH:MM 格式", parent=self.dialog)
            return
        
        reminder = {
            'name': name,
            'time': time_str,
            'repeat': self.repeat_var.get(),
            'content': self.content_var.get().strip(),
            'enabled': self.enabled_var.get()
        }
        
        if self.callback:
            self.callback(reminder)
        
        self.dialog.destroy()

    def _create_period_tab(self):
        """创建经期提醒选项卡"""
        tab = tk.Frame(self.notebook, bg=self.COLORS['bg'])
        self.notebook.add(tab, text='  经期提醒  ')

        period = self.config.config.period
        row = 0

        # 启用开关
        self.period_enabled_var = tk.BooleanVar(value=period.enabled)
        tk.Checkbutton(tab, text="启用经期提醒", variable=self.period_enabled_var,
                      bg=self.COLORS['bg'], fg=self.COLORS['fg'],
                      selectcolor=self.COLORS['bg'], activebackground=self.COLORS['bg'],
                      activeforeground=self.COLORS['fg'],
                      font=("Microsoft YaHei", 10, "bold")).grid(
            row=row, column=0, sticky="w", padx=20, pady=(20, 8))
        row += 1

        # 性别/模式选择
        tk.Label(tab, text="提醒模式", bg=self.COLORS['bg'], fg=self.COLORS['fg'],
                 anchor="w", font=("Microsoft YaHei", 10, "bold")).grid(
            row=row, column=0, sticky="w", padx=20, pady=(8, 4))
        row += 1

        self.period_mode_var = tk.StringVar(value=period.mode)
        mode_frame = tk.Frame(tab, bg=self.COLORS['bg'])
        mode_frame.grid(row=row, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 8))

        tk.Radiobutton(mode_frame, text="我是女生", variable=self.period_mode_var, value="self",
                      bg=self.COLORS['bg'], fg=self.COLORS['fg'],
                      selectcolor=self.COLORS['bg'], activebackground=self.COLORS['bg'],
                      activeforeground=self.COLORS['fg'],
                      font=("Microsoft YaHei", 10)).pack(side="left", padx=(0, 20))
        tk.Radiobutton(mode_frame, text="伴侣提醒", variable=self.period_mode_var, value="partner",
                      bg=self.COLORS['bg'], fg=self.COLORS['fg'],
                      selectcolor=self.COLORS['bg'], activebackground=self.COLORS['bg'],
                      activeforeground=self.COLORS['fg'],
                      font=("Microsoft YaHei", 10)).pack(side="left")
        row += 1

        # 周期和经期天数
        cycle_frame = tk.Frame(tab, bg=self.COLORS['bg'])
        cycle_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(8, 4))

        tk.Label(cycle_frame, text="周期天数", bg=self.COLORS['bg'], fg=self.COLORS['fg'],
                 font=("Microsoft YaHei", 10)).pack(side='left')
        self.cycle_days_var = tk.IntVar(value=period.cycle_days)
        tk.Spinbox(cycle_frame, textvariable=self.cycle_days_var, from_=21, to=45,
                  bg=self.COLORS['entry_bg'], fg=self.COLORS['fg'],
                  insertbackground=self.COLORS['fg'], relief="flat",
                  font=("Microsoft YaHei", 10), width=5).pack(side='left', padx=(8, 20))

        tk.Label(cycle_frame, text="经期天数", bg=self.COLORS['bg'], fg=self.COLORS['fg'],
                 font=("Microsoft YaHei", 10)).pack(side='left')
        self.period_days_var = tk.IntVar(value=period.period_days)
        tk.Spinbox(cycle_frame, textvariable=self.period_days_var, from_=2, to=10,
                  bg=self.COLORS['entry_bg'], fg=self.COLORS['fg'],
                  insertbackground=self.COLORS['fg'], relief="flat",
                  font=("Microsoft YaHei", 10), width=5).pack(side='left', padx=(8, 0))
        row += 1

        # 上次经期日期
        tk.Label(tab, text="上次经期日期", bg=self.COLORS['bg'], fg=self.COLORS['fg'],
                 anchor="w", font=("Microsoft YaHei", 10, "bold")).grid(
            row=row, column=0, sticky="w", padx=20, pady=(12, 4))
        row += 1

        date_frame = tk.Frame(tab, bg=self.COLORS['bg'])
        date_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 4))

        tk.Label(date_frame, text="首日:", bg=self.COLORS['bg'], fg=self.COLORS['fg'],
                 font=("Microsoft YaHei", 10)).pack(side='left')
        self.last_start_var = tk.StringVar(value=period.last_period_start or "")
        tk.Entry(date_frame, textvariable=self.last_start_var, bg=self.COLORS['entry_bg'],
                fg=self.COLORS['fg'], insertbackground=self.COLORS['fg'],
                relief="flat", font=("Microsoft YaHei", 10), width=12).pack(side='left', padx=(4, 16))

        tk.Label(date_frame, text="结束日:", bg=self.COLORS['bg'], fg=self.COLORS['fg'],
                 font=("Microsoft YaHei", 10)).pack(side='left')
        self.last_end_var = tk.StringVar(value=period.last_period_end or "")
        tk.Entry(date_frame, textvariable=self.last_end_var, bg=self.COLORS['entry_bg'],
                fg=self.COLORS['fg'], insertbackground=self.COLORS['fg'],
                relief="flat", font=("Microsoft YaHei", 10), width=12).pack(side='left', padx=(4, 0))

        tk.Label(date_frame, text="(YYYY-MM-DD)", bg=self.COLORS['bg'], fg='#6b7280',
                font=("Microsoft YaHei", 9)).pack(side='left', padx=(8, 0))
        row += 1

        # 预测结果
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

        self.pred_label = tk.Label(tab, text=pred_text, bg=self.COLORS['bg'], fg=self.COLORS['accent'],
                                  font=("Microsoft YaHei", 10), wraplength=450)
        self.pred_label.grid(row=row, column=0, columnspan=2, padx=20, pady=(8, 4))
        row += 1

        # 校准区域
        tk.Label(tab, text="校准调整", bg=self.COLORS['bg'], fg=self.COLORS['fg'],
                 anchor="w", font=("Microsoft YaHei", 10, "bold")).grid(
            row=row, column=0, sticky="w", padx=20, pady=(12, 4))
        row += 1

        calib_frame = tk.Frame(tab, bg=self.COLORS['bg'])
        calib_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 8))

        tk.Label(calib_frame, text="偏移天数:", bg=self.COLORS['bg'], fg=self.COLORS['fg'],
                 font=("Microsoft YaHei", 10)).pack(side='left')

        self.calib_offset_var = tk.IntVar(value=period.calibration_offset)

        tk.Button(calib_frame, text="-1天", command=lambda: self._adjust_calibration(-1),
                 bg=self.COLORS['border'], fg=self.COLORS['fg'], relief="flat",
                 cursor="hand2", padx=8, pady=2).pack(side='left', padx=(8, 4))

        self.calib_label = tk.Label(calib_frame, text=str(period.calibration_offset),
                                   bg=self.COLORS['entry_bg'], fg=self.COLORS['fg'],
                                   font=("Microsoft YaHei", 10), width=4)
        self.calib_label.pack(side='left', padx=4)

        tk.Button(calib_frame, text="+1天", command=lambda: self._adjust_calibration(1),
                 bg=self.COLORS['border'], fg=self.COLORS['fg'], relief="flat",
                 cursor="hand2", padx=8, pady=2).pack(side='left', padx=(4, 16))

        tk.Button(calib_frame, text="重置", command=lambda: self._adjust_calibration(0, reset=True),
                 bg=self.COLORS['border'], fg=self.COLORS['fg'], relief="flat",
                 cursor="hand2", padx=8, pady=2).pack(side='left')
        row += 1

        # 历史记录
        if period.records:
            tk.Label(tab, text="历史记录 (最近3次)", bg=self.COLORS['bg'], fg=self.COLORS['fg'],
                     anchor="w", font=("Microsoft YaHei", 10, "bold")).grid(
                row=row, column=0, sticky="w", padx=20, pady=(8, 4))
            row += 1

            for i, record in enumerate(period.records[-3:]):
                days = record.actual_days if record.actual_days else period.period_days
                record_text = f"  {record.start_date} ~ {record.end_date} ({days}天)"
                tk.Label(tab, text=record_text, bg=self.COLORS['bg'], fg='#9ca3af',
                        font=("Microsoft YaHei", 9)).grid(
                    row=row, column=0, sticky="w", padx=30, pady=1)
                row += 1

    def _adjust_calibration(self, delta, reset=False):
        """调整校准偏移"""
        if reset:
            new_offset = 0
        else:
            new_offset = self.calib_offset_var.get() + delta

        self.calib_offset_var.set(new_offset)
        self.calib_label.config(text=str(new_offset))


# The period-tab helpers belong to SettingsPanel; bind them explicitly so the
# panel can be created even though the legacy methods live near ReminderDialog.
SettingsPanel._create_period_tab = ReminderDialog._create_period_tab
SettingsPanel._adjust_calibration = ReminderDialog._adjust_calibration
