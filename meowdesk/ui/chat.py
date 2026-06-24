"""
AI 对话窗口模块
兼容 macOS / Windows
"""

from typing import Dict, Any, List
from datetime import datetime
import threading

# 从 settings 导入颜色配置
try:
    from .settings import resolve_colors, DARK_COLORS
except ImportError:
    DARK_COLORS = {
        'bg': '#121218',
        'fg': '#F0EDE8',
        'entry_bg': '#22222E',
        'accent': '#F4845F',
        'border': '#2D2D3D',
    }
    def resolve_colors(mode):
        return dict(DARK_COLORS)

# 消息颜色 — 暖珊瑚色主题
MSG_COLORS = {
    'user_msg': '#F4845F',
    'ai_msg': '#6EE7A0',
    'system_msg': '#FBBF5C',
    'error_msg': '#F87171',
    'timestamp': '#6B6880',
}

# 跨平台字体
import sys
FONT_FAMILY = "Microsoft YaHei" if sys.platform == 'win32' else "Helvetica"


class ChatWindow:
    """AI 对话窗口"""
    
    MAX_MESSAGES = 100  # 消息数量限制
    
    def __init__(self, parent, config, agent_gateway=None):
        """
        初始化对话窗口
        
        Args:
            parent: 父窗口
            config: ConfigManager 实例
            agent_gateway: AgentGateway 实例
        """
        import tkinter as tk
        from tkinter import ttk, messagebox
        self.tk = tk
        self.ttk = ttk
        self._messagebox = messagebox
        
        self.parent = parent
        self.config = config
        self.agent_gateway = agent_gateway
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.messages: List[Dict] = []
        self._is_sending = False

        # Resolve theme from config
        color_mode = "dark"
        try:
            color_mode = getattr(config.config, 'color_mode', 'dark')
        except Exception:
            pass
        self.COLORS = resolve_colors(color_mode)

        # 创建窗口
        self.window = self.tk.Toplevel(parent)
        self.window.title("AI 助手 - MeowDesk")
        self.window.configure(bg=self.COLORS['bg'])
        self.window.resizable(True, True)
        
        # 居中显示
        self.window.update_idletasks()
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        ww, wh = 550, 700
        self.window.geometry(f"{ww}x{wh}+{(sw-ww)//2}+{(sh-wh)//2}")
        self.window.attributes("-topmost", True)
        
        # 创建 UI
        self._create_ui()
        
        # 添加欢迎消息
        self._add_message("欢迎使用 AI 助手！请输入您的问题。", 'system_msg')
    
    def _create_ui(self):
        """创建界面"""
        # 顶部工具栏
        toolbar = self.tk.Frame(self.window, bg=self.COLORS['border'], height=40)
        toolbar.pack(fill='x')
        toolbar.pack_propagate(False)
        
        self.tk.Label(
            toolbar, text=f"会话: {self.session_id}",
            bg=self.COLORS['border'], fg=self.COLORS['fg'],
            font=(FONT_FAMILY, 9)
        ).pack(side='left', padx=10)
        
        self.tk.Button(
            toolbar, text="清空对话", bg=self.COLORS['border'], fg=self.COLORS['fg'],
            relief="flat", cursor="hand2", padx=8, pady=2,
            command=self._clear_chat
        ).pack(side='right', padx=10)
        
        # 消息显示区域
        msg_frame = self.tk.Frame(self.window, bg=self.COLORS['bg'])
        msg_frame.pack(fill='both', expand=True, padx=10, pady=(10, 0))
        
        self.msg_text = self.tk.Text(
            msg_frame, bg=self.COLORS['bg'], fg=self.COLORS['fg'],
            font=(FONT_FAMILY, 10), wrap='word', state='disabled',
            relief="flat", padx=10, pady=10
        )
        
        scrollbar = self.ttk.Scrollbar(msg_frame, orient='vertical', command=self.msg_text.yview)
        self.msg_text.configure(yscrollcommand=scrollbar.set)
        self.msg_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 配置消息标签
        for tag, color in MSG_COLORS.items():
            font = (FONT_FAMILY, 8) if tag == 'timestamp' else (FONT_FAMILY, 10)
            self.msg_text.tag_configure(tag, foreground=color, font=font)
        
        # 快捷命令区域
        cmd_frame = self.tk.Frame(self.window, bg=self.COLORS['bg'])
        cmd_frame.pack(fill='x', padx=10, pady=(5, 0))
        
        for label, cmd in [("清理磁盘", "帮我清理临时文件"),
                           ("系统信息", "显示系统信息"),
                           ("日期查询", "今天是什么日期？")]:
            self.tk.Button(
                cmd_frame, text=label, bg=self.COLORS['entry_bg'], fg=self.COLORS['fg'],
                relief="flat", cursor="hand2", padx=8, pady=2,
                command=lambda c=cmd: self._send_quick_command(c)
            ).pack(side='left', padx=(0, 5))
        
        # 输入区域
        input_frame = self.tk.Frame(self.window, bg=self.COLORS['border'])
        input_frame.pack(fill='x', padx=10, pady=10)

        self.input_text = self.tk.Text(
            input_frame, bg=self.COLORS['entry_bg'], fg=self.COLORS['fg'],
            font=(FONT_FAMILY, 11), height=5, relief="flat", padx=12, pady=10,
            wrap='word'
        )
        self.input_text.pack(side='left', fill='both', expand=True)
        self.input_text.bind('<Return>', self._on_enter)
        
        self.tk.Button(
            input_frame, text="发送", bg=self.COLORS['accent'], fg="#ffffff",
            relief="flat", cursor="hand2", padx=20, pady=12,
            font=(FONT_FAMILY, 11, "bold"), command=self._send_message
        ).pack(side='right', padx=(8, 0))
        
        # 状态栏
        self.status_label = self.tk.Label(
            self.window, text="就绪", bg=self.COLORS['bg'],
            fg=MSG_COLORS['timestamp'], font=(FONT_FAMILY, 8)
        )
        self.status_label.pack(anchor='w', padx=15, pady=(0, 5))
    
    def _on_enter(self, event):
        """回车键处理"""
        if not event.state & 0x1:  # 没有按 Shift
            self._send_message()
            return 'break'
        return None
    
    def _send_message(self):
        """发送消息"""
        if self._is_sending:
            return
        
        message = self.input_text.get('1.0', 'end').strip()
        if not message:
            return
        
        self.input_text.delete('1.0', 'end')
        self._add_message(f"你: {message}", 'user_msg')
        self._send_to_ai(message)
    
    def _send_quick_command(self, command: str):
        """发送快捷命令"""
        self.input_text.delete('1.0', 'end')
        self.input_text.insert('1.0', command)
        self._send_message()
    
    def _send_to_ai(self, message: str):
        """发送消息到 AI（异步）

        会话管理（参考 Aion 的 messages + acp_sessions）：
        - 构建带角色的消息历史（user/assistant），过滤 system/error
        - 携带 session_id 和 actor 绑定信息
        - 超时/连接失败时给出明确提示
        """
        if not self.agent_gateway:
            self._add_message("AI 助手未配置，请在设置中启用并配置。", 'error_msg')
            return

        if not self.agent_gateway.enabled:
            self._add_message("AI 助手已禁用，请在设置中启用。", 'error_msg')
            return

        self._is_sending = True
        self.status_label.config(text="正在思考...")

        def send_thread():
            try:
                # Build history with proper roles (exclude system/error)
                history = []
                for msg in self.messages:
                    role = msg.get('role', '')
                    content = msg.get('raw_content', '')
                    if role in ('user', 'assistant') and content:
                        history.append({'role': role, 'content': content})
                context = {
                    'session_id': self.session_id,
                    'history': history[-20:],
                }
                result = self.agent_gateway.chat(message, context)
                self.window.after(0, lambda: self._handle_response(result))
            except Exception as e:
                error_msg = str(e)
                self.window.after(0, lambda msg=error_msg: self._handle_error(msg))

        threading.Thread(target=send_thread, daemon=True).start()

    
    def _handle_response(self, result: Dict[str, Any]):
        """处理 AI 响应

        错误恢复策略（参考 Aion 事件总线的错误处理）：
        - 连接失败: 提示检查 Agent 状态
        - 超时: 提示减少输入长度或重试
        - 未知错误: 显示原始错误信息
        """
        self._is_sending = False
        self.status_label.config(text="就绪")

        if result.get('success'):
            response = result.get('response', '无响应')
            if result.get('session_id'):
                self.session_id = result['session_id']
            self._add_message(f"AI: {response}", 'ai_msg')
            for action in result.get('actions', []):
                self._execute_action(action)
        else:
            error = result.get('error', '未知错误')
            if '超时' in error or 'timeout' in error.lower():
                self._add_message("请求超时，请稍后重试或减少输入长度。", 'error_msg')
            elif '连接' in error or 'connect' in error.lower() or 'refused' in error.lower():
                self._add_message("连接失败：请确认 AI Agent 已启动并在设置中检查端点配置。", 'error_msg')
            elif '未启用' in error:
                self._add_message("AI 助手未启用，请在设置中开启。", 'error_msg')
            else:
                self._add_message(f"AI 响应失败: {error}", 'error_msg')

    
    def _handle_error(self, error: str):
        """处理错误"""
        self._is_sending = False
        self.status_label.config(text="就绪")
        self._add_message(f"请求失败: {error}", 'error_msg')
    
    def _execute_action(self, action: Dict[str, Any]):
        """执行 AI 建议的动作"""
        if action.get('type') == 'command':
            self._add_message(f"执行命令: {action.get('command')}", 'system_msg')
    
    def _add_message(self, message: str, tag: str):
        """添加消息到显示区域"""
        timestamp = datetime.now().strftime('%H:%M')
        
        self.msg_text.config(state='normal')
        self.msg_text.insert('end', f"[{timestamp}] ", 'timestamp')
        self.msg_text.insert('end', f"{message}\n\n", tag)
        self.msg_text.see('end')
        self.msg_text.config(state='disabled')
        
        # 记录消息历史 (raw_content 用于构建 API 上下文)
        role = 'user' if tag == 'user_msg' else 'assistant'
        if tag in ('system_msg', 'error_msg'):
            role = 'system'
        self.messages.append({
            'role': role,
            'content': message,
            'raw_content': message,
            'timestamp': timestamp
        })
        
        # 限制消息数量
        if len(self.messages) > self.MAX_MESSAGES:
            self.messages = self.messages[-self.MAX_MESSAGES:]
    
    def _clear_chat(self):
        """清空对话并重置会话"""
        if self._messagebox.askyesno("确认", "确定要清空对话历史吗？", parent=self.window):
            self.msg_text.config(state='normal')
            self.msg_text.delete('1.0', 'end')
            self.msg_text.config(state='disabled')
            self.messages.clear()
            if self.agent_gateway:
                self.agent_gateway.reset_session()
            self._add_message("对话已清空，会话已重置。", 'system_msg')
