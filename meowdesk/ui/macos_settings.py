"""
macOS 设置面板启动器 - 使用子进程避免 tkinter 与 PyObjC 冲突
现在使用新的 settings.py SettingsPanel 实现
"""

import os
import sys
import subprocess
import tempfile


def open_settings(config_path: str, on_saved_callback=None):
    """启动 macOS 设置面板（在子进程中运行 tkinter）"""
    
    # Get the project root path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    script = f'''
import sys
import json
import os
import tempfile

config_path = sys.argv[1]

# 添加项目路径以导入新的 settings 模块
project_root = "{project_root}"
sys.path.insert(0, project_root)

from meowdesk.ui.settings import SettingsPanel
from meowdesk.core.config import ConfigManager

config = ConfigManager(config_path)

# 创建一个简单的 parent 对象（用于定位窗口）
import tkinter as tk
root = tk.Tk()
root.withdraw()  # 隐藏主窗口

# Marker 文件路径
marker_file = os.path.join(tempfile.gettempdir(), '.meowdesk_settings_saved')

# 创建设置面板
def on_save():
    """保存时写入 marker 文件"""
    with open(marker_file, 'w') as mf:
        mf.write('saved')

panel = SettingsPanel(root, config, on_save_callback=on_save)

# 运行设置面板
root.mainloop()
'''

    marker_file = os.path.join(tempfile.gettempdir(), '.meowdesk_settings_saved')

    if os.path.exists(marker_file):
        try:
            os.remove(marker_file)
        except Exception:
            pass

    proc = subprocess.Popen(
        [sys.executable, '-c', script, config_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    return proc


def check_settings_saved():
    """检查设置是否已保存（供动画循环调用）"""
    marker_file = os.path.join(tempfile.gettempdir(), '.meowdesk_settings_saved')
    if os.path.exists(marker_file):
        try:
            os.remove(marker_file)
        except Exception:
            pass
        return True
    return False