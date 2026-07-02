"""
跨平台抽象层
"""

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import PlatformWindow

def get_platform_window() -> 'PlatformWindow':
    """获取当前平台的窗口实现"""
    if sys.platform == 'win32':
        from .windows import WindowsWindow
        return WindowsWindow
    elif sys.platform == 'darwin':
        from .macos import MacOSWindow
        return MacOSWindow
    else:
        raise NotImplementedError(f"不支持的平台: {sys.platform}")

__all__ = ['get_platform_window', 'set_launch_at_startup', 'is_launch_at_startup', 'register_meow_locate_protocol']

def set_launch_at_startup(enabled: bool) -> bool:
    if sys.platform == 'win32':
        from .windows import set_launch_at_startup as _impl
        return _impl(enabled)
    return False


def is_launch_at_startup() -> bool:
    if sys.platform == 'win32':
        from .windows import is_launch_at_startup as _impl
        return _impl()
    return False


def register_meow_locate_protocol(app_dir: str) -> bool:
    """注册 meow-locate:// 协议,使导航页"定位"按钮可调起文件资源管理器。

    非 Windows 平台直接返回 False。
    """
    if sys.platform == 'win32':
        from .windows import register_meow_locate_protocol as _impl
        return _impl(app_dir)
    return False
