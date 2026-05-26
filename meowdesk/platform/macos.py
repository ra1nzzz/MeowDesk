"""
macOS 平台实现 - 使用 PyObjC 实现透明窗口

依赖：
    pip install pyobjc-framework-Cocoa
"""

import sys
from typing import Tuple, Optional
from PIL import Image
import io

from .base import PlatformWindow

# 延迟导入 macOS 特定库
if sys.platform == 'darwin':
    try:
        from Cocoa import (
            NSApplication, NSWindow, NSView, NSImage, NSBitmapImageRep,
            NSWindowStyleMaskBorderless, NSBackingStoreBuffered,
            NSFloatingWindowLevel, NSApplicationActivationPolicyAccessory,
            NSColor, NSMakeRect, NSMakePoint, NSMakeSize,
            NSScreen, NSEvent, NSLeftMouseDown, NSRightMouseDown,
            NSLeftMouseDragged, NSLeftMouseUp
        )
        from AppKit import NSDragOperationCopy, NSFilenamesPboardType
        from Foundation import NSObject
        MACOS_AVAILABLE = True
    except ImportError:
        MACOS_AVAILABLE = False
        print("警告: PyObjC 未安装，macOS 支持不可用")
        print("安装: pip install pyobjc-framework-Cocoa")
else:
    MACOS_AVAILABLE = False


class MacOSWindow(PlatformWindow):
    """macOS 平台窗口实现"""
    
    def __init__(self, width: int, height: int):
        if not MACOS_AVAILABLE:
            raise ImportError(
                "macOS 支持需要安装 pyobjc-framework-Cocoa:\n"
                "pip install pyobjc-framework-Cocoa"
            )
        
        super().__init__(width, height)
        self.app = None
        self.window = None
        self.view = None
        self.current_image = None
    
    def create(self):
        """创建窗口"""
        # 创建应用
        self.app = NSApplication.sharedApplication()
        self.app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
        
        # 创建无边框窗口
        rect = NSMakeRect(100, 100, self.width, self.height)
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect,
            NSWindowStyleMaskBorderless,
            NSBackingStoreBuffered,
            False
        )
        
        # 设置窗口属性
        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(NSColor.clearColor())
        self.window.setLevel_(NSFloatingWindowLevel)
        self.window.setIgnoresMouseEvents_(False)
        self.window.setAcceptsMouseMovedEvents_(True)
        
        # 创建自定义视图
        self.view = MacOSDropView.alloc().initWithFrame_(rect)
        self.view.window_ref = self
        self.window.setContentView_(self.view)
        
        print("✅ macOS 窗口创建成功")
    
    def show(self):
        """显示窗口"""
        if self.window:
            self.window.makeKeyAndOrderFront_(None)
            self.window.orderFrontRegardless()
    
    def hide(self):
        """隐藏窗口"""
        if self.window:
            self.window.orderOut_(None)
    
    def set_position(self, x: int, y: int):
        """设置窗口位置（macOS 坐标系原点在左下角）"""
        self.x = x
        self.y = y
        if self.window:
            # 转换坐标系：从左上角到左下角
            screen_height = NSScreen.mainScreen().frame().size.height
            mac_y = screen_height - y - self.height
            self.window.setFrameOrigin_(NSMakePoint(x, mac_y))
    
    def get_position(self) -> Tuple[int, int]:
        """获取窗口位置（转换为左上角坐标系）"""
        if self.window:
            frame = self.window.frame()
            screen_height = NSScreen.mainScreen().frame().size.height
            x = int(frame.origin.x)
            y = int(screen_height - frame.origin.y - self.height)
            return x, y
        return self.x, self.y
    
    def render(self, image: Image.Image):
        """渲染图像"""
        if not self.view:
            return
        
        try:
            # 转换 PIL Image 到 NSImage
            ns_image = self._pil_to_nsimage(image)
            
            # 设置到视图
            self.view.setImage_(ns_image)
            self.view.setNeedsDisplay_(True)
            
            # 保存当前图像
            self.current_image = image
            
        except Exception as e:
            print(f"渲染失败: {e}")
    
    def _pil_to_nsimage(self, pil_image: Image.Image):
        """将 PIL Image 转换为 NSImage"""
        # 确保是 RGBA 模式
        if pil_image.mode != 'RGBA':
            pil_image = pil_image.convert('RGBA')
        
        # 转换为 PNG 字节流
        img_buffer = io.BytesIO()
        pil_image.save(img_buffer, format='PNG')
        img_data = img_buffer.getvalue()
        
        # 创建 NSData
        from Foundation import NSData
        ns_data = NSData.dataWithBytes_length_(img_data, len(img_data))
        
        # 创建 NSImage
        ns_image = NSImage.alloc().initWithData_(ns_data)
        
        return ns_image
    
    def set_topmost(self, topmost: bool):
        """设置窗口置顶"""
        if self.window:
            level = NSFloatingWindowLevel if topmost else 0
            self.window.setLevel_(level)
    
    def enable_drag_drop(self):
        """启用拖放"""
        if self.view:
            self.view.registerForDraggedTypes_([NSFilenamesPboardType])
            print("✅ macOS 拖放已启用")
    
    def get_screen_size(self) -> Tuple[int, int]:
        """获取屏幕尺寸"""
        if NSScreen.mainScreen():
            frame = NSScreen.mainScreen().frame()
            return int(frame.size.width), int(frame.size.height)
        return 1920, 1080  # 默认值
    
    def run(self):
        """运行事件循环"""
        if self.app:
            try:
                self.app.run()
            except KeyboardInterrupt:
                print("\n用户中断")
    
    def quit(self):
        """退出"""
        if self.app:
            self.app.terminate_(None)


if MACOS_AVAILABLE:
    class MacOSDropView(NSView):
        """支持拖放的自定义视图"""
        
        def initWithFrame_(self, frame):
            self = super(MacOSDropView, self).initWithFrame_(frame)
            if self:
                self.window_ref = None
                self.image = None
                self.mouse_down_point = None
                self.animation_callback = None
            return self
        
        def setImage_(self, image):
            """设置要显示的图像"""
            self.image = image
        
        def drawRect_(self, rect):
            """绘制视图"""
            # 清除背景
            NSColor.clearColor().set()
            from AppKit import NSRectFill
            NSRectFill(self.bounds())
            
            # 绘制图像
            if self.image:
                self.image.drawInRect_(self.bounds())
        
        def isOpaque(self):
            """视图是否不透明"""
            return False
        
        # 拖放支持
        def draggingEntered_(self, sender):
            """拖入事件"""
            return NSDragOperationCopy
        
        def performDragOperation_(self, sender):
            """拖放事件"""
            pasteboard = sender.draggingPasteboard()
            files = pasteboard.propertyListForType_(NSFilenamesPboardType)
            
            if files and self.window_ref and self.window_ref.on_drop_callback:
                # 转换为 Python 列表
                file_list = list(files)
                self.window_ref.on_drop_callback(file_list)
            
            return True
        
        # 鼠标事件
        def mouseDown_(self, event):
            """鼠标按下"""
            if self.window_ref and self.window_ref.on_click_callback:
                self.window_ref.on_click_callback()
            
            # 记录鼠标位置用于拖动
            self.mouse_down_point = event.locationInWindow()
        
        def mouseDragged_(self, event):
            """鼠标拖动（移动窗口）"""
            if not self.mouse_down_point:
                return
            
            window = self.window()
            if not window:
                return
            
            # 计算偏移
            current_location = event.locationInWindow()
            dx = current_location.x - self.mouse_down_point.x
            dy = current_location.y - self.mouse_down_point.y
            
            # 移动窗口
            frame = window.frame()
            new_origin = NSMakePoint(frame.origin.x + dx, frame.origin.y + dy)
            window.setFrameOrigin_(new_origin)
        
        def mouseUp_(self, event):
            """鼠标释放"""
            self.mouse_down_point = None
            
            # 保存窗口位置
            if self.window_ref:
                x, y = self.window_ref.get_position()
                if hasattr(self.window_ref, 'on_position_changed'):
                    self.window_ref.on_position_changed(x, y)
        
        def rightMouseDown_(self, event):
            """右键点击"""
            if self.window_ref and self.window_ref.on_right_click_callback:
                self.window_ref.on_right_click_callback()
        
        def acceptsFirstResponder(self):
            """接受第一响应者状态"""
            return True
        
        def animationTick_(self, timer):
            """动画定时器回调"""
            if self.animation_callback:
                self.animation_callback()
