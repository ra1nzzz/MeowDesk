"""
AI 对话窗口模块
"""

import os
import sys
import json
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime
import threading


class ChatWindow:
    """AI 对话窗口"""
    
    # 颜色配置
    COLORS = {
        'bg': '#1a1d27',
        'fg': '#e2e8f0',
        'entry_bg': '#242837',
        'accent': '#6366f1',
        'accent_hover': '#818cf8',
        'user_msg': '#3b82f6',
        'ai_msg': '#22c55e',
        'system_msg': '#f59e0b',
        'error_msg': '#ef4444',
        'border': '#374151',
    }
    
    def __init__(self, parent, config, agent_gateway=None):
        """
        初始化对话窗口
        
        Args:
            parent: 父窗口
            config: ConfigManager 实例
            agent_gateway: AgentGateway 实例
        """
        self.parent = parent
        self.config = config
        self.agent_gateway = agent_gateway
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.messages = []
        
        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("AI 助手 - MeowDesk")
        self.window.configure(bg=self.COLORS['bg'])
        self.window.resizable(True, True)
        
        # 居中显示
        self.window.update_idletasks()
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        ww, wh = 500, 600
        self.window.geometry(f"{ww}x{wh}+{(sw-ww)//2}+{(sh-wh)//2}")
        self.window.attributes("-topmost", True)
        
        # 创建 UI
        self._create_ui()
        
        # 添加欢迎消息
        self._add_system_message("欢迎使用 AI 助手！请输入您的问题。")
    
    def _create_ui(self):
        """创建界面"""
        # 顶部工具栏
        toolbar = tk.Frame(self.window, bg=self.COLORS['border'], height=40)
        toolbar.pack(fill='x')
        toolbar.pack_propagate(False)
        
        # 会话信息
        session_label = tk.Label(
            toolbar,
            text=f"会话: {self.session_id}",
            bg=self.COLORS['border'],
            fg=self.COLORS['fg'],
            font=("Microsoft YaHei", 9)
        )
        session_label.pack(side='left', padx=10)
        
        # 清空按钮
        clear_btn = tk.Button(
            toolbar,
            text="清空对话",
            bg=self.COLORS['border'],
            fg=self.COLORS['fg'],
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=2,
            command=self._clear_chat
        )
        clear_btn.pack(side='right', padx=10)
        
        # 消息显示区域
        msg_frame = tk.Frame(self.window, bg=self.COLORS['bg'])
        msg_frame.pack(fill='both', expand=True, padx=10, pady=(10, 0))
        
        self.msg_text = tk.Text(
            msg_frame,
            bg=self.COLORS['bg'],
            fg=self.COLORS['fg'],
            font=("Microsoft YaHei", 10),
            wrap='word',
            state='disabled',
            relief="flat",
            padx=10,
            pady=10
        )
        
        scrollbar = ttk.Scrollbar(msg_frame, orient='vertical', command=self.msg_text.yview)
        self.msg_text.configure(yscrollcommand=scrollbar.set)
        
        self.msg_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 配置消息标签
        self.msg_text.tag_configure('user_msg', foreground=self.COLORS['user_msg'])
        self.msg_text.tag_configure('ai_msg', foreground=self.COLORS['ai_msg'])
        self.msg_text.tag_configure('system_msg', foreground=self.COLORS['system_msg'])
        self.msg_text.tag_configure('error_msg', foreground=self.COLORS['error_msg'])
        self.msg_text.tag_configure('timestamp', foreground='#6b7280', font=("Microsoft YaHei", 8))
        
        # 快捷命令区域
        cmd_frame = tk.Frame(self.window, bg=self.COLORS['bg'])
        cmd_frame.pack(fill='x', padx=10, pady=(5, 0))
        
        quick_commands = [
            ("清理磁盘", "帮我清理临时文件"),
            ("系统信息", "显示系统信息"),
            ("日期查询", "今天是什么日期？"),
        ]
        
        for label, cmd in quick_commands:
            btn = tk.Button(
                cmd_frame,
                text=label,
                bg=self.COLORS['entry_bg'],
                fg=self.COLORS['fg'],
                relief="flat",
                cursor="hand2",
                padx=8,
                pady=2,
                command=lambda c=cmd: self._send_quick_command(c)
            )
            btn.pack(side='left', padx=(0, 5))
        
        # 输入区域
        input_frame = tk.Frame(self.window, bg=self.COLORS['border'])
        input_frame.pack(fill='x', padx=10, pady=10)
        
        self.input_text = tk.Text(
            input_frame,
            bg=self.COLORS['entry_bg'],
            fg=self.COLORS['fg'],
            font=("Microsoft YaHei", 10),
            height=3,
            relief="flat",
            padx=10,
            pady=8
        )
        self.input_text.pack(side='left', fill='both', expand=True)
        
        # 绑定回车键
        self.input_text.bind('<Return>', self._on_enter)
        self.input_text.bind('<Shift-Return>', lambda e: None)  # Shift+Enter 换行
        
        # 发送按钮
        send_btn = tk.Button(
            input_frame,
            text="发送",
            bg=self.COLORS['accent'],
            fg="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=8,
            font=("Microsoft YaHei", 10, "bold"),
            command=self._send_message
        )
        send_btn.pack(side='right', padx=(5, 0))
        
        # 状态栏
        status_frame = tk.Frame(self.window, bg=self.COLORS['bg'])
        status_frame.pack(fill='x', padx=10, pady=(0, 5))
        
        self.status_label = tk.Label(
            status_frame,
            text="就绪",
            bg=self.COLORS['bg'],
            fg='#6b7280',
            font=("Microsoft YaHei", 8)
        )
        self.status_label.pack(side='left')
    
    def _on_enter(self, event):
        """回车键处理"""
        if not event.state & 0x1:  # 没有按 Shift
            self._send_message()
            return 'break'  # 阻止默认换行
        return None  # 允许 Shift+Enter 换行
    
    def _send_message(self):
        """发送消息"""
        message = self.input_text.get('1.0', 'end').strip()
        if not message:
            return
        
        # 清空输入框
        self.input_text.delete('1.0', 'end')
        
        # 添加用户消息
        self._add_user_message(message)
        
        # 发送到 AI
        self._send_to_ai(message)
    
    def _send_quick_command(self, command: str):
        """发送快捷命令"""
        self.input_text.delete('1.0', 'end')
        self.input_text.insert('1.0', command)
        self._send_message()
    
    def _send_to_ai(self, message: str):
        """发送消息到 AI"""
        if not self.agent_gateway:
            self._add_error_message("AI 助手未配置，请在设置中配置 AI 网关。")
            return
        
        # 更新状态
        self.status_label.config(text="正在思考...")
        
        # 在新线程中发送请求
        def send_thread():
            try:
                # 构建上下文
                context = {
                    'session_id': self.session_id,
                    'history': self.messages[-10:]  # 最近 10 条消息
                }
                
                # 发送请求
                result = self.agent_gateway.chat(message, context)
                
                # 在主线程中更新 UI
                self.window.after(0, lambda: self._handle_ai_response(result))
            except Exception as e:
                self.window.after(0, lambda: self._handle_ai_error(str(e)))
        
        thread = threading.Thread(target=send_thread, daemon=True)
        thread.start()
    
    def _handle_ai_response(self, result: Dict[str, Any]):
        """处理 AI 响应"""
        self.status_label.config(text="就绪")
        
        if result.get('success'):
            response = result.get('response', '无响应')
            self._add_ai_message(response)
            
            # 处理动作
            actions = result.get('actions', [])
            for action in actions:
                self._execute_action(action)
        else:
            error = result.get('error', '未知错误')
            self._add_error_message(f"AI 响应失败: {error}")
    
    def _handle_ai_error(self, error: str):
        """处理 AI 错误"""
        self.status_label.config(text="就绪")
        self._add_error_message(f"请求失败: {error}")
    
    def _execute_action(self, action: Dict[str, Any]):
        """执行 AI 建议的动作"""
        action_type = action.get('type')
        
        if action_type == 'command':
            command = action.get('command')
            params = action.get('params', {})
            self._add_system_message(f"执行命令: {command}")
            
            # TODO: 执行命令并返回结果
    
    def _add_user_message(self, message: str):
        """添加用户消息"""
        timestamp = datetime.now().strftime('%H:%M')
        
        self.msg_text.config(state='normal')
        self.msg_text.insert('end', f"[{timestamp}] 你:\n", 'timestamp')
        self.msg_text.insert('end', f"{message}\n\n", 'user_msg')
        self.msg_text.see('end')
        self.msg_text.config(state='disabled')
        
        self.messages.append({
            'role': 'user',
            'content': message,
            'timestamp': timestamp
        })
    
    def _add_ai_message(self, message: str):
        """添加 AI 消息"""
        timestamp = datetime.now().strftime('%H:%M')
        
        self.msg_text.config(state='normal')
        self.msg_text.insert('end', f"[{timestamp}] AI:\n", 'timestamp')
        self.msg_text.insert('end', f"{message}\n\n", 'ai_msg')
        self.msg_text.see('end')
        self.msg_text.config(state='disabled')
        
        self.messages.append({
            'role': 'assistant',
            'content': message,
            'timestamp': timestamp
        })
    
    def _add_system_message(self, message: str):
        """添加系统消息"""
        timestamp = datetime.now().strftime('%H:%M')
        
        self.msg_text.config(state='normal')
        self.msg_text.insert('end', f"[{timestamp}] 系统: {message}\n\n", 'system_msg')
        self.msg_text.see('end')
        self.msg_text.config(state='disabled')
    
    def _add_error_message(self, message: str):
        """添加错误消息"""
        timestamp = datetime.now().strftime('%H:%M')
        
        self.msg_text.config(state='normal')
        self.msg_text.insert('end', f"[{timestamp}] 错误: {message}\n\n", 'error_msg')
        self.msg_text.see('end')
        self.msg_text.config(state='disabled')
    
    def _clear_chat(self):
        """清空对话"""
        if messagebox.askyesno("确认", "确定要清空对话历史吗？", parent=self.window):
            self.msg_text.config(state='normal')
            self.msg_text.delete('1.0', 'end')
            self.msg_text.config(state='disabled')
            self.messages.clear()
            self._add_system_message("对话已清空。")
