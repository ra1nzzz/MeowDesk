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

if sys.platform == 'darwin':
    try:
        from Cocoa import (
            NSApplication, NSWindow, NSView, NSImage, NSBitmapImageRep,
            NSWindowStyleMaskBorderless, NSBackingStoreBuffered,
            NSFloatingWindowLevel, NSApplicationActivationPolicyAccessory,
            NSColor, NSMakeRect, NSMakePoint, NSMakeSize,
            NSScreen, NSEvent, NSLeftMouseDown, NSRightMouseDown,
            NSLeftMouseDragged, NSLeftMouseUp,
            NSMenu, NSMenuItem
        )
        from AppKit import NSDragOperationCopy, NSFilenamesPboardType
        from Foundation import NSObject
        import objc
        MACOS_AVAILABLE = True
    except ImportError:
        MACOS_AVAILABLE = False
        print("警告: PyObjC 未安装，macOS 支持不可用")
        print("安装: pip install pyobjc-framework-Cocoa")
else:
    MACOS_AVAILABLE = False


class MacOSWindow(PlatformWindow):

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
        self.on_position_changed = None

    def create(self):
        self.app = NSApplication.sharedApplication()
        self.app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)

        rect = NSMakeRect(100, 100, self.width, self.height)
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect,
            NSWindowStyleMaskBorderless,
            NSBackingStoreBuffered,
            False
        )

        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(NSColor.clearColor())
        self.window.setLevel_(NSFloatingWindowLevel)
        self.window.setIgnoresMouseEvents_(False)
        self.window.setAcceptsMouseMovedEvents_(True)

        self.view = MacOSDropView.alloc().initWithFrame_(rect)
        self.view.window_ref = self
        self.window.setContentView_(self.view)

        print("✅ macOS 窗口创建成功")

    def show(self):
        if self.window:
            self.window.makeKeyAndOrderFront_(None)
            self.window.orderFrontRegardless()

    def hide(self):
        if self.window:
            self.window.orderOut_(None)

    def set_position(self, x: int, y: int):
        self.x = x
        self.y = y
        if self.window:
            screen_height = NSScreen.mainScreen().frame().size.height
            mac_y = screen_height - y - self.height
            self.window.setFrameOrigin_(NSMakePoint(x, mac_y))

    def get_position(self) -> Tuple[int, int]:
        if self.window:
            frame = self.window.frame()
            screen_height = NSScreen.mainScreen().frame().size.height
            x = int(frame.origin.x)
            y = int(screen_height - frame.origin.y - self.height)
            return x, y
        return self.x, self.y

    def render(self, image: Image.Image):
        if not self.view:
            return

        try:
            ns_image = self._pil_to_nsimage(image)
            self.view.setImage_(ns_image)
            self.view.setNeedsDisplay_(True)
            self.current_image = image
        except Exception as e:
            print(f"渲染失败: {e}")

    def _pil_to_nsimage(self, pil_image: Image.Image):
        if pil_image.mode != 'RGBA':
            pil_image = pil_image.convert('RGBA')

        img_buffer = io.BytesIO()
        pil_image.save(img_buffer, format='PNG')
        img_data = img_buffer.getvalue()

        from Foundation import NSData
        ns_data = NSData.dataWithBytes_length_(img_data, len(img_data))
        ns_image = NSImage.alloc().initWithData_(ns_data)

        return ns_image

    def set_topmost(self, topmost: bool):
        if self.window:
            level = NSFloatingWindowLevel if topmost else 0
            self.window.setLevel_(level)

    def enable_drag_drop(self):
        if self.view:
            self.view.registerForDraggedTypes_([NSFilenamesPboardType])
            print("✅ macOS 拖放已启用")

    def get_screen_size(self) -> Tuple[int, int]:
        if NSScreen.mainScreen():
            frame = NSScreen.mainScreen().frame()
            return int(frame.size.width), int(frame.size.height)
        return 1920, 1080

    def get_mouse_position(self) -> Tuple[int, int]:
        point = NSEvent.mouseLocation()
        screen_height = NSScreen.mainScreen().frame().size.height
        x = int(point.x)
        y = int(screen_height - point.y)
        return x, y

    def run(self):
        if self.app:
            try:
                self.app.run()
            except KeyboardInterrupt:
                print("\n用户中断")

    def quit(self):
        if self.app:
            self.app.terminate_(None)


if MACOS_AVAILABLE:
    class MenuActionHandler(NSObject):

        def init(self):
            self = objc.super(MenuActionHandler, self).init()
            if self:
                self.callback = None
            return self

        def menuAction_(self, sender):
            if self.callback:
                self.callback()

    class MacOSDropView(NSView):

        def initWithFrame_(self, frame):
            self = objc.super(MacOSDropView, self).initWithFrame_(frame)
            if self:
                self.window_ref = None
                self.image = None
                self.mouse_down_point = None
                self.animation_callback = None
            return self

        def setImage_(self, image):
            self.image = image

        def drawRect_(self, rect):
            NSColor.clearColor().set()
            from AppKit import NSRectFill
            NSRectFill(self.bounds())

            if self.image:
                self.image.drawInRect_(self.bounds())

        def isOpaque(self):
            return False

        def draggingEntered_(self, sender):
            return NSDragOperationCopy

        def performDragOperation_(self, sender):
            pasteboard = sender.draggingPasteboard()
            files = pasteboard.propertyListForType_(NSFilenamesPboardType)

            if files and self.window_ref and self.window_ref.on_drop_callback:
                file_list = list(files)
                self.window_ref.on_drop_callback(file_list)

            return True

        def mouseDown_(self, event):
            if self.window_ref and self.window_ref.on_click_callback:
                self.window_ref.on_click_callback()

            self.mouse_down_point = event.locationInWindow()

        def mouseDragged_(self, event):
            if not self.mouse_down_point:
                return

            window = self.window()
            if not window:
                return

            current_location = event.locationInWindow()
            dx = current_location.x - self.mouse_down_point.x
            dy = current_location.y - self.mouse_down_point.y

            frame = window.frame()
            new_origin = NSMakePoint(frame.origin.x + dx, frame.origin.y + dy)
            window.setFrameOrigin_(new_origin)

        def mouseUp_(self, event):
            self.mouse_down_point = None

            if self.window_ref:
                x, y = self.window_ref.get_position()
                if self.window_ref.on_position_changed:
                    self.window_ref.on_position_changed(x, y)

        def rightMouseDown_(self, event):
            if self.window_ref and self.window_ref.on_right_click_callback:
                self.window_ref.on_right_click_callback()

        def acceptsFirstResponder(self):
            return True

        def animationTick_(self, timer):
            if self.animation_callback:
                self.animation_callback()

    def show_context_menu(view, menu_items):
        menu = NSMenu.alloc().init()
        menu.setAutoenablesItems_(False)
        handlers = []

        for item in menu_items:
            if item is None:
                menu.addItem_(NSMenuItem.separatorItem())
            else:
                label, callback = item
                handler = MenuActionHandler.alloc().init()
                handler.callback = callback
                handlers.append(handler)
                menu_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    label, "menuAction:", ""
                )
                menu_item.setTarget_(handler)
                menu.setEnabled_forItem_(True, menu_item)
                menu.addItem_(menu_item)

        menu.popUpContextMenu_withEvent_forView_(
            menu, view.window().currentEvent(), view
        )

        return handlers
