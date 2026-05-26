"""
平台窗口基类
"""

from abc import ABC, abstractmethod
from typing import Tuple, Callable, Optional
from PIL import Image


class PlatformWindow(ABC):
    """平台窗口抽象基类"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.x = 0
        self.y = 0
        self.on_drop_callback: Optional[Callable] = None
        self.on_click_callback: Optional[Callable] = None
        self.on_right_click_callback: Optional[Callable] = None
        self.on_drag_start_callback: Optional[Callable] = None
        self.on_drag_end_callback: Optional[Callable] = None
    
    @abstractmethod
    def create(self):
        """创建窗口"""
        pass
    
    @abstractmethod
    def show(self):
        """显示窗口"""
        pass
    
    @abstractmethod
    def hide(self):
        """隐藏窗口"""
        pass
    
    @abstractmethod
    def set_position(self, x: int, y: int):
        """设置窗口位置"""
        pass
    
    @abstractmethod
    def get_position(self) -> Tuple[int, int]:
        """获取窗口位置"""
        pass
    
    def set_size(self, width: int, height: int):
        """设置窗口大小"""
        self.width = width
        self.height = height
    
    @abstractmethod
    def render(self, image: Image.Image):
        """渲染图像到窗口"""
        pass
    
    @abstractmethod
    def set_topmost(self, topmost: bool):
        """设置窗口置顶"""
        pass
    
    @abstractmethod
    def enable_drag_drop(self):
        """启用拖放功能"""
        pass
    
    def on_drop(self, callback: Callable):
        """设置拖放回调"""
        self.on_drop_callback = callback
    
    def on_click(self, callback: Callable):
        """设置点击回调"""
        self.on_click_callback = callback
    
    def on_right_click(self, callback: Callable):
        """设置右键回调"""
        self.on_right_click_callback = callback
    
    def on_drag_start(self, callback: Callable):
        """设置拖动开始回调"""
        self.on_drag_start_callback = callback
    
    def on_drag_end(self, callback: Callable):
        """设置拖动结束回调，参数为 (x, y)"""
        self.on_drag_end_callback = callback
    
    @abstractmethod
    def run(self):
        """运行事件循环"""
        pass
    
    @abstractmethod
    def quit(self):
        """退出程序"""
        pass
