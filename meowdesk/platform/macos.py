"""
macOS 平台实现 - 使用 PyObjC 实现透明窗口

依赖：
    pip install pyobjc-framework-Cocoa
"""

import sys
from typing import Tuple, Optional, List
from PIL import Image
import io

from .base import PlatformWindow

if sys.platform == 'darwin':
    try:
        from Cocoa import (
            NSApplication, NSWindow, NSView, NSImage, NSBitmapImageRep,
            NSWindowStyleMaskBorderless, NSBackingStoreBuffered,
            NSFloatingWindowLevel, NSApplicationActivationPolicyRegular,
            NSColor, NSMakeRect, NSMakePoint, NSMakeSize,
            NSScreen, NSEvent, NSLeftMouseDown, NSRightMouseDown,
            NSLeftMouseDragged, NSLeftMouseUp,
            NSMenu, NSMenuItem
        )
        from AppKit import (
            NSDragOperationCopy, NSFilenamesPboardType,
            NSEventTrackingRunLoopMode,
            NSEventMaskLeftMouseDown, NSEventMaskLeftMouseDragged, NSEventMaskLeftMouseUp,
            NSTrackingArea, NSTrackingMouseEnteredAndExited,
            NSTrackingActiveAlways, NSTrackingInVisibleRect
        )
        from Foundation import NSObject, NSDate
        import objc
        MACOS_AVAILABLE = True
    except ImportError:
        MACOS_AVAILABLE = False
        print("警告: PyObjC 未安装，macOS 支持不可用")
        print("安装: pip install pyobjc-framework-Cocoa")
else:
    MACOS_AVAILABLE = False


if MACOS_AVAILABLE:

    class MeowNSWindow(NSWindow):

        def canBecomeKeyWindow(self):
            return True

        def canBecomeMainWindow(self):
            return True

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
                self._menu_handlers = []
                self._is_dragging = False
                self.on_drag_enter_callback = None
                self.on_drag_exit_callback = None
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

        def hitTest_(self, point):
            bounds = self.bounds()
            if (point.x >= 0 and point.x <= bounds.size.width and
                point.y >= 0 and point.y <= bounds.size.height):
                return self
            return None

        def updateTrackingAreas(self):
            objc.super(MacOSDropView, self).updateTrackingAreas()
            for area in self.trackingAreas():
                self.removeTrackingArea_(area)
            options = NSTrackingMouseEnteredAndExited | NSTrackingActiveAlways | NSTrackingInVisibleRect
            tracking_area = NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
                NSMakeRect(0, 0, 0, 0), options, self, None
            )
            self.addTrackingArea_(tracking_area)

        def mouseEntered_(self, event):
            if self.window_ref and hasattr(self.window_ref, 'on_mouse_enter_callback') and self.window_ref.on_mouse_enter_callback:
                self.window_ref.on_mouse_enter_callback()

        def mouseExited_(self, event):
            if self.window_ref and hasattr(self.window_ref, 'on_mouse_exit_callback') and self.window_ref.on_mouse_exit_callback:
                self.window_ref.on_mouse_exit_callback()

        def draggingEntered_(self, sender):
            if self.window_ref and self.window_ref.on_drop_callback:
                if self.on_drag_enter_callback:
                    self.on_drag_enter_callback()
                return NSDragOperationCopy
            return 0

        def draggingUpdated_(self, sender):
            if self.window_ref and self.window_ref.on_drop_callback:
                return NSDragOperationCopy
            return 0

        def draggingExited_(self, sender):
            if self.on_drag_exit_callback:
                self.on_drag_exit_callback()

        def performDragOperation_(self, sender):
            pasteboard = sender.draggingPasteboard()
            files = pasteboard.propertyListForType_(NSFilenamesPboardType)

            if not files:
                url_items = pasteboard.propertyListForType_("public.file-url")
                if url_items:
                    from Foundation import NSURL
                    files = []
                    for item in url_items:
                        if isinstance(item, str):
                            url = NSURL.URLWithString_(item)
                            if url:
                                path = url.path()
                                if path:
                                    files.append(path)
                        elif hasattr(item, 'path'):
                            path = item.path()
                            if path:
                                files.append(path)

            if files and self.window_ref and self.window_ref.on_drop_callback:
                file_list = [str(f) for f in files if f]
                if file_list:
                    self.window_ref.on_drop_callback(file_list)
                    return True
            return False

        def concludeDragOperation_(self, sender):
            pass

        def wantsPeriodicDraggingUpdates_(self, sender):
            return False

        def prepareForDragOperation_(self, sender):
            return True

        def mouseDown_(self, event):
            self.window().makeKeyWindow()

            if event.modifierFlags() & 0x40000:
                if self.window_ref and self.window_ref.on_right_click_callback:
                    mouse_loc = NSEvent.mouseLocation()
                    screen_height = NSScreen.mainScreen().frame().size.height
                    x = int(mouse_loc.x)
                    y = int(screen_height - mouse_loc.y)
                    self.window_ref.on_right_click_callback(x, y)
                return

            if self.window_ref and self.window_ref.on_click_callback:
                self.window_ref.on_click_callback()

            last_screen_loc = NSEvent.mouseLocation()
            has_dragged = False

            mask = NSEventMaskLeftMouseDown | NSEventMaskLeftMouseDragged | NSEventMaskLeftMouseUp
            app = NSApplication.sharedApplication()

            while True:
                next_event = app.nextEventMatchingMask_untilDate_inMode_dequeue_(
                    mask, NSDate.distantFuture(), NSEventTrackingRunLoopMode, True
                )
                if next_event is None:
                    break

                event_type = next_event.type()

                if event_type == NSLeftMouseDragged:
                    if not has_dragged:
                        has_dragged = True
                        self._is_dragging = True
                        if self.window_ref and hasattr(self.window_ref, 'on_drag_start_callback') and self.window_ref.on_drag_start_callback:
                            self.window_ref.on_drag_start_callback()

                    current_screen_loc = NSEvent.mouseLocation()
                    dx = current_screen_loc.x - last_screen_loc.x
                    dy = current_screen_loc.y - last_screen_loc.y
                    origin = self.window().frame().origin
                    new_origin = NSMakePoint(origin.x + dx, origin.y + dy)
                    self.window().setFrameOrigin_(new_origin)
                    last_screen_loc = current_screen_loc

                elif event_type == NSLeftMouseUp:
                    break

            if has_dragged:
                self._is_dragging = False
                if self.window_ref and hasattr(self.window_ref, 'on_drag_end_callback') and self.window_ref.on_drag_end_callback:
                    x, y = self.window_ref.get_position()
                    self.window_ref.on_drag_end_callback(x, y)

            if self.window_ref:
                x, y = self.window_ref.get_position()
                if self.window_ref.on_position_changed:
                    self.window_ref.on_position_changed(x, y)

        def mouseUp_(self, event):
            pass

        def rightMouseDown_(self, event):
            self.window().makeKeyWindow()
            if self.window_ref and self.window_ref.on_right_click_callback:
                mouse_loc = NSEvent.mouseLocation()
                screen_height = NSScreen.mainScreen().frame().size.height
                x = int(mouse_loc.x)
                y = int(screen_height - mouse_loc.y)
                self.window_ref.on_right_click_callback(x, y)

        def otherMouseDown_(self, event):
            self.window().makeKeyWindow()
            if self.window_ref and self.window_ref.on_right_click_callback:
                mouse_loc = NSEvent.mouseLocation()
                screen_height = NSScreen.mainScreen().frame().size.height
                x = int(mouse_loc.x)
                y = int(screen_height - mouse_loc.y)
                self.window_ref.on_right_click_callback(x, y)

        def acceptsFirstResponder(self):
            return True

        def becomeFirstResponder(self):
            return True

        def resignFirstResponder(self):
            return True

        def animationTick_(self, timer):
            if self.animation_callback:
                self.animation_callback()

        def showContextMenu_(self, menu_items):
            try:
                menu = NSMenu.alloc().init()
                menu.setAutoenablesItems_(False)
                self._menu_handlers = []

                for item in menu_items:
                    if item is None:
                        menu.addItem_(NSMenuItem.separatorItem())
                    else:
                        label, callback = item
                        handler = MenuActionHandler.alloc().init()
                        handler.callback = callback
                        self._menu_handlers.append(handler)
                        menu_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                            label, "menuAction:", ""
                        )
                        menu_item.setTarget_(handler)
                        menu_item.setEnabled_(True)
                        menu.addItem_(menu_item)

                mouse_loc = NSEvent.mouseLocation()
                win_frame = self.window().frame()
                local_x = mouse_loc.x - win_frame.origin.x
                local_y = mouse_loc.y - win_frame.origin.y

                menu.popUpMenuPositioningItem_atLocation_inView_(
                    None,
                    NSMakePoint(local_x, local_y),
                    self
                )

            except Exception as e:
                print(f"菜单弹出失败: {e}")
                import traceback
                traceback.print_exc()


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
        self.on_mouse_enter_callback = None
        self.on_mouse_exit_callback = None
        self.on_drag_start_callback = None
        self.on_drag_end_callback = None

    def create(self):
        self.app = NSApplication.sharedApplication()
        self.app.setActivationPolicy_(NSApplicationActivationPolicyRegular)

        rect = NSMakeRect(100, 100, self.width, self.height)
        self.window = MeowNSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
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
        self.window.setMovableByWindowBackground_(False)
        self.window.setHasShadow_(False)

        self.view = MacOSDropView.alloc().initWithFrame_(NSMakeRect(0, 0, self.width, self.height))
        self.view.window_ref = self
        self.window.setContentView_(self.view)

        print("✅ macOS 窗口创建成功")

    def show(self):
        if self.window:
            self.window.makeKeyAndOrderFront_(None)
            self.window.orderFrontRegardless()
            self.app.activateIgnoringOtherApps_(True)

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
            img_w, img_h = image.size
            if img_w != self.width or img_h != self.height:
                self._resize_window(img_w, img_h)

            ns_image = self._pil_to_nsimage(image)
            self.view.setImage_(ns_image)
            self.view.setNeedsDisplay_(True)
            self.current_image = image
        except Exception as e:
            print(f"渲染失败: {e}")

    def _resize_window(self, new_w: int, new_h: int):
        if not self.window:
            return
        frame = self.window.frame()
        new_frame = NSMakeRect(
            frame.origin.x,
            frame.origin.y,
            new_w,
            new_h
        )
        self.window.setFrame_display_(new_frame, False)
        self.view.setFrameSize_(NSMakeSize(new_w, new_h))
        self.width = new_w
        self.height = new_h

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
            self.view.registerForDraggedTypes_([NSFilenamesPboardType, "public.file-url"])
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

    def show_context_menu(self, menu_items: List):
        if self.view:
            self.view.showContextMenu_(menu_items)

    def on_mouse_enter(self, callback):
        self.on_mouse_enter_callback = callback

    def on_mouse_exit(self, callback):
        self.on_mouse_exit_callback = callback

    def on_drag_start(self, callback):
        self.on_drag_start_callback = callback

    def on_drag_end(self, callback):
        self.on_drag_end_callback = callback

    def on_drag_enter(self, callback):
        if self.view:
            self.view.on_drag_enter_callback = callback

    def on_drag_exit(self, callback):
        if self.view:
            self.view.on_drag_exit_callback = callback

    def set_size(self, width: int, height: int):
        if self.window:
            self._resize_window(width, height)

    def run(self):
        if self.app:
            try:
                self.app.run()
            except KeyboardInterrupt:
                print("\n用户中断")

    def quit(self):
        if self.app:
            self.app.terminate_(None)
