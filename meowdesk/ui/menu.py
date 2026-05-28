"""
右键菜单模块
兼容 macOS / Windows
"""

import os
import sys
import tkinter as tk
from tkinter import Menu, messagebox, filedialog
import webbrowser
import subprocess
from datetime import datetime
from .settings import SettingsPanel


class ContextMenu:
    """右键菜单"""
    
    def __init__(self, parent, config, agent_gateway=None, 
                 on_quit_callback=None, on_settings_saved=None):
        self.parent = parent
        self.config = config
        self.agent_gateway = agent_gateway
        self.on_quit_callback = on_quit_callback
        self.on_settings_saved = on_settings_saved
        
        self.menu = None
        self._create_menu()
    
    def _create_menu(self):
        """创建菜单"""
        self.menu = Menu(self.parent, tearoff=0)
        
        # 打开导航页
        self.menu.add_command(
            label="📄 打开导航页",
            command=self._open_html
        )
        
        # 打开归档目录
        self.menu.add_command(
            label="📁 打开归档目录",
            command=self._open_archive_dir
        )
        
        self.menu.add_separator()
        
        # AI 助手子菜单
        ai_menu = Menu(self.menu, tearoff=0)
        ai_menu.add_command(label="💬 自由对话...", command=self._open_chat)
        ai_menu.add_separator()
        ai_menu.add_command(label="🧹 清理磁盘", command=self._clean_disk)
        ai_menu.add_command(label="📅 查看日期", command=self._check_date)
        ai_menu.add_command(label="🎉 假期提醒", command=self._check_holidays)
        ai_menu.add_command(label="💝 经期提醒", command=self._period_reminder)
        ai_menu.add_command(label="💻 系统信息", command=self._system_info)
        
        self.menu.add_cascade(label="🤖 AI 助手", menu=ai_menu)
        
        self.menu.add_separator()
        
        # 设置
        self.menu.add_command(
            label="⚙️ 设置",
            command=self._open_settings
        )
        
        # 关于
        self.menu.add_command(
            label="ℹ️ 关于",
            command=self._show_about
        )
        
        self.menu.add_separator()
        
        # 退出
        self.menu.add_command(
            label="❌ 退出",
            command=self._quit
        )
    
    def show(self, x: int, y: int):
        """显示菜单"""
        try:
            self.menu.tk_popup(x, y)
        finally:
            self.menu.grab_release()
    
    def _open_html(self):
        """打开 HTML 导航页"""
        archive_dir = self.config.archive_dir
        html_file = os.path.join(archive_dir, 'index.html')
        
        if os.path.exists(html_file):
            webbrowser.open(f'file:///{html_file}')
        else:
            print(f"HTML 文件不存在: {html_file}")
    
    def _open_archive_dir(self):
        """打开归档目录"""
        archive_dir = self.config.archive_dir
        
        if os.path.exists(archive_dir):
            if sys.platform == 'win32':
                os.startfile(archive_dir)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', archive_dir])
            else:
                subprocess.Popen(['xdg-open', archive_dir])
        else:
            print(f"归档目录不存在: {archive_dir}")
    
    def _open_chat(self):
        """打开 AI 对话窗口"""
        from .chat import ChatWindow
        ChatWindow(self.parent, self.config, agent_gateway=self.agent_gateway)
    
    def _clean_disk(self):
        """清理磁盘"""
        from ..agent import CommandRegistry
        
        # 确认对话框
        if not messagebox.askyesno("清理磁盘", 
                                   "将清理超过7天的临时文件。\n是否继续？",
                                   parent=self.parent):
            return
        
        registry = CommandRegistry()
        result = registry.execute('clean_disk')
        
        if result['success']:
            data = result['result']
            files = data.get('cleaned_files', 0)
            size_mb = data.get('cleaned_size_mb', 0)
            
            if files > 0:
                msg = f"清理完成！\n\n清理文件: {files} 个\n释放空间: {size_mb:.2f} MB"
                messagebox.showinfo("清理完成", msg, parent=self.parent)
            else:
                messagebox.showinfo("清理完成", "没有需要清理的临时文件。", parent=self.parent)
        else:
            error = result.get('error', '未知错误')
            messagebox.showerror("清理失败", f"清理失败: {error}", parent=self.parent)
    
    def _check_date(self):
        """查看日期"""
        from ..agent import CommandRegistry
        registry = CommandRegistry()
        result = registry.execute('check_date')
        
        if result['success']:
            data = result['result']
            weekday = data['weekday']
            today = data['today']
            days_to_weekend = data['days_to_weekend']
            days_to_month_end = data['days_to_month_end']
            week_of_year = data['week_of_year']
            
            msg = f"📅 {today} {weekday}\n\n"
            msg += f"距离周末: {days_to_weekend} 天\n"
            msg += f"距离月底: {days_to_month_end} 天\n"
            msg += f"本年第 {week_of_year} 周"
            
            messagebox.showinfo("日期信息", msg, parent=self.parent)
        else:
            messagebox.showerror("错误", f"查询失败: {result.get('error')}", parent=self.parent)
    
    def _check_holidays(self):
        """假期提醒"""
        from ..agent import CommandRegistry
        registry = CommandRegistry()
        result = registry.execute('check_holidays')
        
        if result['success']:
            holidays = result['result']['upcoming_holidays']
            if holidays:
                msg = "🎉 即将到来的假期:\n\n"
                for h in holidays[:5]:
                    name = h['name']
                    date = h['date']
                    days_left = h['days_left']
                    
                    if days_left == 0:
                        msg += f"• {name}: {date} (今天!)\n"
                    elif days_left == 1:
                        msg += f"• {name}: {date} (明天)\n"
                    else:
                        msg += f"• {name}: {date} (还有 {days_left} 天)\n"
                
                messagebox.showinfo("假期提醒", msg, parent=self.parent)
            else:
                messagebox.showinfo("假期提醒", "近期没有假期。", parent=self.parent)
        else:
            messagebox.showerror("错误", f"查询失败: {result.get('error')}", parent=self.parent)
    
    def _period_reminder(self):
        """经期提醒 - 打开设置面板"""
        # 直接打开设置面板，用户可以在经期提醒 TAB 中配置
        SettingsPanel(self.parent, self.config, on_save_callback=self._on_settings_saved)
    
    def _system_info(self):
        """系统信息"""
        from ..agent import CommandRegistry
        registry = CommandRegistry()
        result = registry.execute('system_info')
        
        if result['success']:
            data = result['result']
            os_name = data.get('os', '未知')
            os_version = data.get('os_version', '')
            cpu_count = data.get('cpu_count', 0)
            cpu_percent = data.get('cpu_percent', 0)
            memory_total = data.get('memory_total_gb', 0)
            memory_used = data.get('memory_used_gb', 0)
            memory_percent = data.get('memory_percent', 0)
            disk_total = data.get('disk_total_gb', 0)
            disk_used = data.get('disk_used_gb', 0)
            disk_percent = data.get('disk_percent', 0)
            
            msg = f"💻 系统信息\n\n"
            msg += f"系统: {os_name}\n"
            msg += f"CPU: {cpu_count} 核心, {cpu_percent}% 使用率\n"
            
            if memory_total > 0:
                msg += f"内存: {memory_used:.1f}/{memory_total:.1f} GB ({memory_percent}%)\n"
            else:
                msg += f"内存: 信息不可用\n"
            
            if disk_total > 0:
                msg += f"磁盘: {disk_used:.1f}/{disk_total:.1f} GB ({disk_percent}%)"
            else:
                msg += f"磁盘: 信息不可用"
            
            messagebox.showinfo("系统信息", msg, parent=self.parent)
        else:
            messagebox.showerror("错误", f"查询失败: {result.get('error')}", parent=self.parent)
    
    def _open_settings(self):
        """打开设置面板"""
        SettingsPanel(self.parent, self.config, on_save_callback=self._on_settings_saved)
    
    def _on_settings_saved(self):
        """设置保存回调"""
        if self.on_settings_saved:
            self.on_settings_saved()
    
    def _show_about(self):
        """显示关于"""
        from .. import __version__
        msg = f"妙喵桌宠 MeowDesk\n\n"
        msg += f"版本: {__version__}\n"
        msg += f"智能桌面文件分类归档工具\n\n"
        msg += f"GitHub: github.com/ra1nzzz/MeowDesk"
        self._show_message("关于", msg)
    
    def _show_message(self, title: str, message: str):
        """显示消息框"""
        from tkinter import messagebox
        messagebox.showinfo(title, message)
    
    def _quit(self):
        """退出"""
        if self.on_quit_callback:
            self.on_quit_callback()
