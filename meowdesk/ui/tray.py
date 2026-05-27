"""
系统托盘模块
"""

import os
import sys
import webbrowser
import subprocess
from typing import Optional, Callable


class SystemTray:
    """系统托盘图标"""
    
    def __init__(self, icon_path: str, config=None, 
                 on_show_callback: Optional[Callable] = None,
                 on_hide_callback: Optional[Callable] = None,
                 on_quit_callback: Optional[Callable] = None):
        self.icon_path = icon_path
        self.config = config
        self.on_show_callback = on_show_callback
        self.on_hide_callback = on_hide_callback
        self.on_quit_callback = on_quit_callback
        self.tray_icon = None
        
        # 根据平台选择实现
        if sys.platform == 'win32':
            self._init_windows()
        elif sys.platform == 'darwin':
            self._init_macos()
    
    def _init_windows(self):
        """Windows 托盘实现"""
        try:
            import pystray
            from PIL import Image
            
            # 加载图标
            if os.path.exists(self.icon_path):
                icon_image = Image.open(self.icon_path)
            else:
                # 创建默认图标
                icon_image = Image.new('RGB', (64, 64), color='gray')
            
            # 创建菜单
            menu = pystray.Menu(
                pystray.MenuItem('打开导航页', self._open_html),
                pystray.MenuItem('打开归档目录', self._open_archive),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem('显示窗口', self._show_window),
                pystray.MenuItem('隐藏窗口', self._hide_window),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem('退出', self._quit)
            )
            
            # 创建托盘图标
            self.tray_icon = pystray.Icon(
                'MeowDesk',
                icon_image,
                '妙喵桌宠',
                menu
            )
            
        except ImportError:
            print("警告: pystray 未安装，系统托盘功能不可用")
            print("安装: pip install pystray")
    
    def _init_macos(self):
        """macOS 托盘实现"""
        try:
            import rumps
            
            class MeowDeskApp(rumps.App):
                def __init__(self, tray_instance):
                    super().__init__("MeowDesk", icon=tray_instance.icon_path)
                    self.tray_instance = tray_instance
                    self.menu = [
                        rumps.MenuItem('打开导航页', callback=self.open_html),
                        rumps.MenuItem('打开归档目录', callback=self.open_archive),
                        None,
                        rumps.MenuItem('显示窗口', callback=self.show_window),
                        rumps.MenuItem('隐藏窗口', callback=self.hide_window),
                    ]
                
                def open_html(self, _):
                    self.tray_instance._open_html()
                
                def open_archive(self, _):
                    self.tray_instance._open_archive()
                
                def show_window(self, _):
                    self.tray_instance._show_window()
                
                def hide_window(self, _):
                    self.tray_instance._hide_window()
            
            self.tray_icon = MeowDeskApp(self)
            
        except ImportError:
            print("警告: rumps 未安装，系统托盘功能不可用")
            print("安装: pip install rumps")
    
    def run(self):
        """运行托盘（阻塞）"""
        if self.tray_icon:
            if sys.platform == 'win32':
                self.tray_icon.run()
            elif sys.platform == 'darwin':
                self.tray_icon.run()
    
    def run_detached(self):
        """后台运行托盘（非阻塞）"""
        if self.tray_icon and sys.platform == 'win32':
            import threading
            thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            thread.start()
    
    def stop(self):
        """停止托盘"""
        if self.tray_icon:
            if sys.platform == 'win32':
                self.tray_icon.stop()
    
    def _open_html(self):
        """打开 HTML 导航页"""
        archive_dir = self.config.get('archive_dir') if self.config else 'D:\\meow-file'
        html_file = os.path.join(archive_dir, 'index.html')
        if os.path.exists(html_file):
            webbrowser.open(f'file:///{html_file}')
        else:
            print(f"HTML 文件不存在: {html_file}")
    
    def _open_archive(self):
        """打开归档目录"""
        archive_dir = self.config.get('archive_dir') if self.config else 'D:\\meow-file'
        if os.path.exists(archive_dir):
            if sys.platform == 'win32':
                os.startfile(archive_dir)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', archive_dir])
            else:
                subprocess.Popen(['xdg-open', archive_dir])
        else:
            print(f"归档目录不存在: {archive_dir}")
    
    def _show_window(self):
        """显示窗口"""
        if self.on_show_callback:
            self.on_show_callback()
    
    def _hide_window(self):
        """隐藏窗口"""
        if self.on_hide_callback:
            self.on_hide_callback()
    
    def _quit(self):
        """退出"""
        if self.on_quit_callback:
            self.on_quit_callback()
        self.stop()
