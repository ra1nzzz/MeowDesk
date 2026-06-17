"""
Windows 平台实现 - 使用 UpdateLayeredWindow 实现透明窗口
按照 1.2.3 版本的成熟方案重写
"""

import ctypes
from ctypes import wintypes
import tkinter as tk
from PIL import Image
from typing import Tuple

from .base import PlatformWindow


# Win32 常量
WS_EX_LAYERED = 0x00080000
WS_EX_TOOLWINDOW = 0x00000080
GWL_EXSTYLE = -20
ULW_ALPHA = 2
AC_SRC_ALPHA = 1

# Win32 API
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

# Win32 结构定义
class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [
        ("BlendOp", ctypes.c_ubyte),
        ("BlendFlags", ctypes.c_ubyte),
        ("SourceConstantAlpha", ctypes.c_ubyte),
        ("AlphaFormat", ctypes.c_ubyte),
    ]

class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", ctypes.c_uint32),
        ("biWidth", ctypes.c_int32),
        ("biHeight", ctypes.c_int32),
        ("biPlanes", ctypes.c_uint16),
        ("biBitCount", ctypes.c_uint16),
        ("biCompression", ctypes.c_uint32),
        ("biSizeImage", ctypes.c_uint32),
        ("biXPelsPerMeter", ctypes.c_int32),
        ("biYPelsPerMeter", ctypes.c_int32),
        ("biClrUsed", ctypes.c_uint32),
        ("biClrImportant", ctypes.c_uint32),
    ]

# 设置函数签名（按照旧版本）
user32.GetWindowLongW.restype = ctypes.c_int64
user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
user32.SetWindowLongW.restype = ctypes.c_int64
user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_int64]
user32.GetDC.restype = wintypes.HDC
user32.GetDC.argtypes = [wintypes.HWND]
user32.ReleaseDC.restype = ctypes.c_int
user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
user32.UpdateLayeredWindow.restype = wintypes.BOOL
user32.UpdateLayeredWindow.argtypes = [
    wintypes.HWND, wintypes.HDC, ctypes.c_void_p,
    ctypes.POINTER(wintypes.SIZE), wintypes.HDC, ctypes.POINTER(wintypes.POINT),
    ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32,
]
gdi32.CreateCompatibleDC.restype = wintypes.HDC
gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi32.DeleteDC.restype = ctypes.c_int
gdi32.DeleteDC.argtypes = [wintypes.HDC]
gdi32.CreateDIBSection.restype = wintypes.HANDLE
gdi32.CreateDIBSection.argtypes = [
    wintypes.HDC, ctypes.c_void_p, ctypes.c_uint32,
    ctypes.POINTER(ctypes.c_void_p), wintypes.HANDLE, ctypes.c_uint32,
]
gdi32.SelectObject.restype = wintypes.HANDLE
gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HANDLE]
gdi32.DeleteObject.restype = ctypes.c_int
gdi32.DeleteObject.argtypes = [wintypes.HANDLE]


class WindowsWindow(PlatformWindow):
    """Windows 平台窗口实现"""
    
    def __init__(self, width: int, height: int):
        super().__init__(width, height)
        self.root = None
        self.hwnd = None
        
        # ULW 渲染器
        self.ulw_renderer = None
        
        # 拖动状态
        self._dragging = False
        self._drag_start_rootx = 0
        self._drag_start_rooty = 0
        self._drag_start_winx = 0
        self._drag_start_winy = 0
        self._press_time = 0
        self._has_moved = False
    
    def _setup_win32_api(self):
        """设置 Win32 API 签名（已全局设置）"""
        pass
    
    def create(self):
        """创建窗口（按照旧版本方案）"""
        self.root = tk.Tk()
        self.root.title("MeowDesk")
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        
        # 设置初始尺寸
        self.root.geometry(f"{self.width}x{self.height}")
        
        # 获取窗口句柄
        self.root.update_idletasks()
        self.hwnd = int(self.root.winfo_id())
        
        # 设置分层窗口样式
        ex_style = user32.GetWindowLongW(self.hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(self.hwnd, GWL_EXSTYLE, ex_style | WS_EX_LAYERED | WS_EX_TOOLWINDOW)
        
        # 创建 ULW 渲染器
        self.ulw_renderer = ULWRenderer()
        
        # 绑定事件 - 按照旧版本的成熟方案
        self.root.bind("<Enter>", lambda e: self._on_enter())
        self.root.bind("<Leave>", lambda e: self._on_leave())
        self.root.bind("<ButtonPress-1>", self._on_press)
        self.root.bind("<B1-Motion>", self._on_motion)
        self.root.bind("<ButtonRelease-1>", self._on_release)
        self.root.bind("<ButtonPress-3>", self._on_right_click)
        self.root.protocol("WM_DELETE_WINDOW", self.hide)
        
        # 初始化拖动状态
        self._dragging = False
        self._has_moved = False
    
    def _on_enter(self):
        """鼠标进入"""
        self._touch()
    
    def _on_leave(self):
        """鼠标离开"""
        pass
    
    def _on_press(self, event):
        """鼠标按下（按照旧版本方案）"""
        self._touch()
        
        # 记录按下时间和位置
        self._press_time = event.time
        self._has_moved = False
        
        # 开始拖动
        self._dragging = True
        self._drag_start_rootx = event.x_root
        self._drag_start_rooty = event.y_root
        self._drag_start_winx = self.root.winfo_x()
        self._drag_start_winy = self.root.winfo_y()
        
        # 通知主窗口开始拖动（切换SHY状态）
        if self.on_drag_start_callback:
            self.on_drag_start_callback()
    
    def _on_motion(self, event):
        """鼠标移动（拖动）"""
        if not self._dragging:
            return
        
        dx = event.x_root - self._drag_start_rootx
        dy = event.y_root - self._drag_start_rooty
        
        # 检测是否有移动（超过3像素视为拖动）
        if abs(dx) > 3 or abs(dy) > 3:
            self._has_moved = True
        
        x = self._drag_start_winx + dx
        y = self._drag_start_winy + dy
        
        # 边界检查（按照旧版本）
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = max(0, min(sw - self.width, x))
        y = max(0, min(sh - self.height, y))
        
        self.set_position(int(x), int(y))
    
    def _on_release(self, event):
        """鼠标释放"""
        if self._dragging:
            self._dragging = False
            
            # 如果没有移动，视为点击
            if not self._has_moved:
                if self.on_click_callback:
                    self.on_click_callback()
            else:
                # 拖动结束，保存位置
                if self.on_drag_end_callback:
                    x, y = self.get_position()
                    self.on_drag_end_callback(x, y)
    
    def _on_right_click(self, event):
        """右键点击"""
        if self.on_right_click_callback:
            # 传递鼠标位置给回调
            self.on_right_click_callback(event.x_root, event.y_root)
    
    def _touch(self):
        """触摸（重置交互时间）"""
        # 这个方法会被主窗口管理器调用
        pass
    
    def show(self):
        """显示窗口"""
        if self.root:
            self.root.deiconify()
    
    def hide(self):
        """隐藏窗口"""
        if self.root:
            self.root.withdraw()
    
    def set_position(self, x: int, y: int):
        """设置窗口位置"""
        self.x = x
        self.y = y
        if self.root:
            self.root.geometry(f"+{x}+{y}")
    
    def get_position(self) -> Tuple[int, int]:
        """获取窗口位置"""
        if self.root:
            try:
                self.root.update_idletasks()
                return self.root.winfo_x(), self.root.winfo_y()
            except Exception:
                pass
        return self.x, self.y
    
    def set_size(self, width: int, height: int):
        """设置窗口大小"""
        self.width = width
        self.height = height
        if self.root:
            # 使用 geometry 设置大小，保持当前位置不变
            x, y = self.get_position()
            self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def render(self, image: Image.Image):
        """渲染图像（帧已在 AnimationManager 中预乘 alpha）"""
        if not self.hwnd or not self.ulw_renderer:
            return
        
        # 直接渲染，alpha 预乘已在动画加载时完成
        self.ulw_renderer.render(self.hwnd, image)
    
    def set_topmost(self, topmost: bool):
        """设置置顶"""
        if self.root:
            self.root.attributes('-topmost', topmost)
    
    def enable_drag_drop(self):
        """启用拖放（按照旧版本使用windnd）"""
        if self.root:
            try:
                import windnd
                windnd.hook_dropfiles(self.root, func=self._on_drop_internal, force_unicode=True)
            except ImportError:
                print("警告: windnd 未安装，拖放功能不可用")
    
    def _on_drop_internal(self, files):
        """内部拖放处理（按照旧版本）"""
        if self.on_drop_callback:
            # windnd 返回的是 bytes 列表，需要解码
            if files and isinstance(files[0], bytes):
                files = [f.decode('utf-8') if isinstance(f, bytes) else f for f in files]
            self.on_drop_callback(files)
    
    def run(self):
        """运行事件循环"""
        if self.root:
            self.root.mainloop()
    
    def quit(self):
        """退出"""
        if self.ulw_renderer:
            self.ulw_renderer.cleanup()
        if self.root:
            try:
                self.root.quit()
                self.root.destroy()
            except Exception:
                pass


class ULWRenderer:
    """UpdateLayeredWindow 渲染器（按照旧版本）"""
    
    def __init__(self):
        self._hdc_mem = None
        self._hbitmap = None
        self._old_bitmap = None
        self._pbits = None
        self._dib_w = 0
        self._dib_h = 0
    
    def _ensure_dib(self, w, h):
        """确保 DIB 位图存在且尺寸正确"""
        if w == self._dib_w and h == self._dib_h and self._hbitmap:
            return
        
        # 清理旧位图
        if self._hbitmap and self._hdc_mem:
            gdi32.SelectObject(self._hdc_mem, self._old_bitmap or 0)
            gdi32.DeleteObject(self._hbitmap)
            self._hbitmap = None
            self._old_bitmap = None
        
        # 创建内存 DC
        if not self._hdc_mem:
            hdc = user32.GetDC(0)
            self._hdc_mem = gdi32.CreateCompatibleDC(hdc)
            user32.ReleaseDC(0, hdc)
        
        # 创建 DIB Section
        bmi = BITMAPINFOHEADER(
            biSize=40,
            biWidth=w,
            biHeight=h,
            biPlanes=1,
            biBitCount=32,
            biCompression=0,
            biSizeImage=w * h * 4,
        )
        
        self._pbits = ctypes.c_void_p(0)
        self._hbitmap = gdi32.CreateDIBSection(
            self._hdc_mem,
            ctypes.byref(bmi),
            0,
            ctypes.byref(self._pbits),
            None,
            0
        )
        
        if self._hbitmap:
            self._old_bitmap = gdi32.SelectObject(self._hdc_mem, self._hbitmap)
        
        self._dib_w = w
        self._dib_h = h
    
    def render(self, hwnd, pil_img):
        """渲染图像到窗口"""
        w, h = pil_img.size
        self._ensure_dib(w, h)
        
        if not self._hbitmap or not self._pbits.value:
            return False
        
        # 转换为 BGRA 并上下翻转
        r, g, b, a = pil_img.split()
        bgra = Image.merge("RGBA", (b, g, r, a)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        
        # 复制像素数据到 DIB
        ctypes.memmove(self._pbits.value, bgra.tobytes(), w * h * 4)
        
        # 调用 UpdateLayeredWindow（按照旧版本）
        hdc_screen = user32.GetDC(0)
        sz = wintypes.SIZE(w, h)
        src_pt = wintypes.POINT(0, 0)
        blend = BLENDFUNCTION(0, 0, 255, AC_SRC_ALPHA)
        
        ok = user32.UpdateLayeredWindow(
            hwnd,
            hdc_screen,
            None,
            ctypes.byref(sz),
            self._hdc_mem,
            ctypes.byref(src_pt),
            0,
            ctypes.byref(blend),
            ULW_ALPHA
        )
        
        user32.ReleaseDC(0, hdc_screen)
        return bool(ok)
    
    def cleanup(self):
        """清理资源"""
        if self._hbitmap and self._hdc_mem:
            gdi32.SelectObject(self._hdc_mem, self._old_bitmap or 0)
            gdi32.DeleteObject(self._hbitmap)
        if self._hdc_mem:
            gdi32.DeleteDC(self._hdc_mem)

_APP_NAME = "MeowDesk"
_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _startup_value() -> tuple:
    import sys as _sys
    from pathlib import Path as _Path
    if getattr(_sys, 'frozen', False):
        return str(_sys.executable), f'"{_sys.executable}"'
    python = str(_sys.executable)
    script = str(_Path(__file__).resolve().parents[1] / "meowdesk_main.py")
    return python, f'"{python}" "{script}"'


def set_launch_at_startup(enabled: bool) -> bool:
    import winreg
    value_name, value_data = _startup_value()
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                winreg.SetValueEx(key, _APP_NAME, 0, winreg.REG_SZ, value_data)
            else:
                try:
                    winreg.DeleteValue(key, _APP_NAME)
                except FileNotFoundError:
                    pass
        return True
    except OSError:
        return False


def is_launch_at_startup() -> bool:
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_READ) as key:
            val, _ = winreg.QueryValueEx(key, _APP_NAME)
            return bool(val)
    except FileNotFoundError:
        return False
    except OSError:
        return False

