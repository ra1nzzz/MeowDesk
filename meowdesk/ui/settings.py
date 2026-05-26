"""
设置面板模块
"""

import os
import sys
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, Callable, Optional, List
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
        ww, wh = 520, 480
        self.window.geometry(f"{ww}x{wh}+{(sw-ww)//2}+{(sh-wh)//2}")
        self.window.attributes("-topmost", True)
        self.window.grab_set()
        
        # 创建选项卡
        self._create_notebook()
        
        # 创建按钮
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
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 创建各个选项卡
        self._create_general_tab()
        self._create_ai_tab()
        self._create_reminder_tab()
    
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
        
        self.dir_var = tk.StringVar(value=self.config.get('archive_dir'))
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
        
        self.scale_var = tk.DoubleVar(value=self.config.get('scale', 0.5))
        
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
        
        self.ss_var = tk.StringVar(value=self.config.get('screenshot_action', 'recycle'))
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
        self.ai_enabled_var = tk.BooleanVar(value=self.config.get('ai_enabled', False))
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
        
        self.agent_type_var = tk.StringVar(value=self.config.get('agent_type', 'openclaw'))
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
        
        self.endpoint_var = tk.StringVar(value=self.config.get('agent_endpoint', 'http://localhost:8080'))
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
        
        self.token_var = tk.StringVar(value=self.config.get('agent_token', ''))
        tk.Entry(tab, textvariable=self.token_var, bg=self.COLORS['entry_bg'],
                fg=self.COLORS['fg'], insertbackground=self.COLORS['fg'],
                relief="flat", font=("Microsoft YaHei", 10), show="*").grid(
            row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 4))
        row += 1
        
        # 超时时间
        tk.Label(tab, text="请求超时（秒）", bg=self.COLORS['bg'], fg=self.COLORS['fg'],
                 anchor="w", font=("Microsoft YaHei", 10)).grid(
            row=row, column=0, sticky="w", padx=20, pady=(8, 4))
        
        self.timeout_var = tk.IntVar(value=self.config.get('agent_timeout', 30))
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
        btn_frame = tk.Frame(self.window, bg=self.COLORS['bg'])
        btn_frame.pack(fill='x', padx=20, pady=(0, 20))
        
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
        from ..agent import AgentGateway
        
        config = {
            'enabled': True,
            'agent_type': self.agent_type_var.get(),
            'endpoint': self.endpoint_var.get(),
            'api_key': self.token_var.get(),
            'timeout': self.timeout_var.get()
        }
        
        gateway = AgentGateway(config)
        
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
        reminders = self.config.get('reminders', [])
        
        # 清空列表
        for item in self.reminder_tree.get_children():
            self.reminder_tree.delete(item)
        
        # 添加提醒
        for reminder in reminders:
            status = "启用" if reminder.get('enabled', True) else "禁用"
            self.reminder_tree.insert('', 'end', values=(
                reminder.get('name', ''),
                reminder.get('time', ''),
                reminder.get('repeat', '不重复'),
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
        
        reminders = self.config.get('reminders', [])
        for reminder in reminders:
            if reminder.get('name') == values[0]:
                ReminderDialog(self.window, reminder=reminder, callback=self._on_reminder_updated)
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
        
        reminders = self.config.get('reminders', [])
        reminders = [r for r in reminders if r.get('name') != name]
        self.config.set('reminders', reminders)
        
        self._load_reminders()
    
    def _on_reminder_added(self, reminder):
        """提醒添加回调"""
        reminders = self.config.get('reminders', [])
        reminders.append(reminder)
        self.config.set('reminders', reminders)
        self._load_reminders()
    
    def _on_reminder_updated(self, reminder):
        """提醒更新回调"""
        reminders = self.config.get('reminders', [])
        for i, r in enumerate(reminders):
            if r.get('name') == reminder.get('name'):
                reminders[i] = reminder
                break
        self.config.set('reminders', reminders)
        self._load_reminders()
    
    def _save(self):
        """保存设置"""
        # 保存常规设置
        self.config.set('archive_dir', self.dir_var.get().strip())
        self.config.set('scale', round(self.scale_var.get(), 2))
        self.config.set('screenshot_action', self.ss_var.get())
        
        # 保存 AI 设置
        self.config.set('ai_enabled', self.ai_enabled_var.get())
        self.config.set('agent_type', self.agent_type_var.get())
        self.config.set('agent_endpoint', self.endpoint_var.get().strip())
        self.config.set('agent_token', self.token_var.get().strip())
        self.config.set('agent_timeout', self.timeout_var.get())
        
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
