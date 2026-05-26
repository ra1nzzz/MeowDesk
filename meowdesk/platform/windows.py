"""
Windows 平台实现 - 使用 UpdateLayeredWindow 实现透明窗口
"""

import ctypes
from ctypes import wintypes
import tkinter as tk
from PIL import Image, ImageMath
from typing import Tuple

from .base import PlatformWindow


class WindowsWindow(PlatformWindow):
    """Windows 平台窗口实现"""
    
    # Win32 常量
    WS_EX_LAYERED = 0x00080000
    WS_EX_TOOLWINDOW = 0x00000080
    GWL_EXSTYLE = -20
    ULW_ALPHA = 2
    AC_SRC_ALPHA = 1
    
    def __init__(self, width: int, height: int):
        super().__init__(width, height)
        self.root = None
        self.hwnd = None
        
        # ULW 渲染器
        self.ulw_renderer = None
        
        # Win32 API
        self.user32 = ctypes.windll.user32
        self.gdi32 = ctypes.windll.gdi32
        
        self._setup_win32_api()
    
    def _setup_win32_api(self):
        """设置 Win32 API 签名"""
        self.user32.GetWindowLongW.restype = ctypes.c_int64
        self.user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
        self.user32.SetWindowLongW.restype = ctypes.c_int64
        self.user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_int64]
        self.user32.UpdateLayeredWindow.restype = wintypes.BOOL
        self.gdi32.CreateCompatibleDC.restype = wintypes.HDC
        self.gdi32.CreateDIBSection.restype = wintypes.HANDLE
    
    def create(self):
        """创建窗口"""
        self.root = tk.Tk()
        self.root.title("MeowDesk")
        self.root.geometry(f"{self.width}x{self.height}+100+100")
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        
        # 获取窗口句柄
        self.root.update_idletasks()
        self.hwnd = int(self.root.winfo_id())
        
        # 设置分层窗口样式
        style = self.user32.GetWindowLongW(self.hwnd, self.GWL_EXSTYLE)
        self.user32.SetWindowLongW(
            self.hwnd,
            self.GWL_EXSTYLE,
            style | self.WS_EX_LAYERED | self.WS_EX_TOOLWINDOW
        )
        
        # 创建 ULW 渲染器
        self.ulw_renderer = ULWRenderer(self.user32, self.gdi32)
        
        # 绑定事件
        self.root.bind("<ButtonPress-1>", lambda e: self._on_click_internal())
        self.root.bind("<ButtonPress-3>", lambda e: self._on_right_click_internal())
        self.root.protocol("WM_DELETE_WINDOW", self.hide)
    
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
            self.root.update_idletasks()
            return self.root.winfo_x(), self.root.winfo_y()
        return self.x, self.y
    
    def render(self, image: Image.Image):
        """渲染图像"""
        if not self.hwnd or not self.ulw_renderer:
            return
        
        # 预乘 alpha（消除白边）
        image_premul = self._premultiply_alpha(image)
        
        # 使用 ULW 渲染
        self.ulw_renderer.render(self.hwnd, image_premul)
    
    def _premultiply_alpha(self, image: Image.Image) -> Image.Image:
        """预乘 alpha 通道"""
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        r, g, b, a = image.split()
        r = ImageMath.unsafe_eval('convert(R * A / 255, "I")', R=r, A=a).convert('L')
        g = ImageMath.unsafe_eval('convert(G * A / 255, "I")', G=g, A=a).convert('L')
        b = ImageMath.unsafe_eval('convert(B * A / 255, "I")', B=b, A=a).convert('L')
        return Image.merge("RGBA", (r, g, b, a))
    
    def set_topmost(self, topmost: bool):
        """设置置顶"""
        if self.root:
            self.root.attributes('-topmost', topmost)
    
    def enable_drag_drop(self):
        """启用拖放"""
        if self.root:
            try:
                import windnd
                windnd.hook_dropfiles(self.root, func=self._on_drop_internal, force_unicode=True)
            except ImportError:
                print("警告: windnd 未安装，拖放功能不可用")
    
    def _on_drop_internal(self, files):
        """内部拖放处理"""
        if self.on_drop_callback:
            # windnd 返回的是 bytes 列表，需要解码
            if files and isinstance(files[0], bytes):
                files = [f.decode('utf-8') if isinstance(f, bytes) else f for f in files]
            self.on_drop_callback(files)
    
    def _on_click_internal(self):
        """内部点击处理"""
        if self.on_click_callback:
            self.on_click_callback()
    
    def _on_right_click_internal(self):
        """内部右键处理"""
        if self.on_right_click_callback:
            self.on_right_click_callback()
    
    def run(self):
        """运行事件循环"""
        if self.root:
            self.root.mainloop()
    
    def quit(self):
        """退出"""
        if self.ulw_renderer:
            self.ulw_renderer.cleanup()
        if self.root:
            self.root.quit()
            self.root.destroy()


class BLENDFUNCTION(ctypes.Structure):
    """Windows BLENDFUNCTION 结构"""
    _fields_ = [
        ("BlendOp", ctypes.c_ubyte),
        ("BlendFlags", ctypes.c_ubyte),
        ("SourceConstantAlpha", ctypes.c_ubyte),
        ("AlphaFormat", ctypes.c_ubyte),
    ]


class BITMAPINFOHEADER(ctypes.Structure):
    """Windows BITMAPINFOHEADER 结构"""
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


class ULWRenderer:
    """UpdateLayeredWindow 渲染器"""
    
    def __init__(self, user32, gdi32):
        self.user32 = user32
        self.gdi32 = gdi32
        
        self.hdc_mem = None
        self.hbitmap = None
        self.old_bitmap = None
        self.pbits = None
        self.dib_width = 0
        self.dib_height = 0
    
    def _ensure_dib(self, width: int, height: int):
        """确保 DIB 位图存在且尺寸正确"""
        if width == self.dib_width and height == self.dib_height and self.hbitmap:
            return
        
        # 清理旧位图
        if self.hbitmap and self.hdc_mem:
            self.gdi32.SelectObject(self.hdc_mem, int(self.old_bitmap) if self.old_bitmap else 0)
            self.gdi32.DeleteObject(int(self.hbitmap))
            self.hbitmap = None
            self.old_bitmap = None
        
        # 创建内存 DC
        if not self.hdc_mem:
            hdc = self.user32.GetDC(0)
            self.hdc_mem = self.gdi32.CreateCompatibleDC(hdc)
            self.user32.ReleaseDC(0, hdc)
        
        # 创建 DIB Section
        bmi = BITMAPINFOHEADER(
            biSize=40,
            biWidth=width,
            biHeight=height,
            biPlanes=1,
            biBitCount=32,
            biCompression=0,
            biSizeImage=width * height * 4,
        )
        
        self.pbits = ctypes.c_void_p(0)
        self.hbitmap = self.gdi32.CreateDIBSection(
            self.hdc_mem,
            ctypes.byref(bmi),
            0,
            ctypes.byref(self.pbits),
            None,
            0
        )
        
        if self.hbitmap:
            self.old_bitmap = self.gdi32.SelectObject(self.hdc_mem, int(self.hbitmap))
        
        self.dib_width = width
        self.dib_height = height
    
    def render(self, hwnd: int, image: Image.Image) -> bool:
        """渲染图像到窗口"""
        width, height = image.size
        self._ensure_dib(width, height)
        
        if not self.hbitmap or not self.pbits.value:
            return False
        
        # 转换为 BGRA 并上下翻转
        r, g, b, a = image.split()
        bgra = Image.merge("RGBA", (b, g, r, a)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        
        # 复制像素数据到 DIB
        ctypes.memmove(self.pbits.value, bgra.tobytes(), width * height * 4)
        
        # 调用 UpdateLayeredWindow
        hdc_screen = self.user32.GetDC(0)
        size = wintypes.SIZE(width, height)
        src_point = wintypes.POINT(0, 0)
        blend = BLENDFUNCTION(0, 0, 255, 1)  # AC_SRC_ALPHA = 1
        
        result = self.user32.UpdateLayeredWindow(
            hwnd,
            hdc_screen,
            None,
            ctypes.byref(size),
            self.hdc_mem,
            ctypes.byref(src_point),
            0,
            ctypes.byref(blend),
            2  # ULW_ALPHA = 2
        )
        
        self.user32.ReleaseDC(0, hdc_screen)
        return bool(result)
    
    def cleanup(self):
        """清理资源"""
        if self.hbitmap and self.hdc_mem:
            self.gdi32.SelectObject(self.hdc_mem, int(self.old_bitmap) if self.old_bitmap else 0)
            self.gdi32.DeleteObject(int(self.hbitmap))
        if self.hdc_mem:
            self.gdi32.DeleteDC(int(self.hdc_mem))
