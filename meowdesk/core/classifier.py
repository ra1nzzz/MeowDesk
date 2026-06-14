"""
文件分类模块
使用类型系统定义分类结果
"""

import os
import re
import sys
from PIL import Image

from .types import FileAction, ClassifyResult, AppConfig


class FileClassifier:
    """文件分类器"""

    # 截图识别正则
    SCREENSHOT_PATTERNS = [
        r'^\d{4}[-_]\d{2}[-_]\d{2}',
        r'screenshot',
        r'screen\s*shot',
        r'截图',
        r'截屏',
        r'微信截图',
        r'微信图片_\d{8}',
        r'QQ截图',
        r'屏幕截图',
        r'snipaste',
        r'capture',
        r'clip_',
        r'paste_',
        r'新建\s*位图图像',
    ]

    SCREENSHOT_RE = re.compile('|'.join(SCREENSHOT_PATTERNS), re.IGNORECASE)
    TEMP_DIRS = ['temp', 'tmp', 'appdata', 'clipboard', 'cache']

    def __init__(self, config: AppConfig):
        self.config = config
        self.categories = config.categories

    def classify(self, filepath: str) -> ClassifyResult:
        """
        分类文件

        Args:
            filepath: 文件路径

        Returns:
            ClassifyResult 对象
        """
        ext = os.path.splitext(filepath)[1].lower()
        filename = os.path.basename(filepath)

        # 检查是否为截图
        if self._is_screenshot(filepath, filename, ext):
            action = self.config.screenshot_action
            return ClassifyResult("截图", action, is_screenshot=True)

        # 根据扩展名分类
        for category, cat_config in self.categories.items():
            if cat_config.matches_ext(ext):
                return ClassifyResult(category, cat_config.action)

        return ClassifyResult("其他", FileAction.ARCHIVE)

    def _is_screenshot(self, filepath: str, filename: str, ext: str) -> bool:
        """判断是否为截图"""
        if ext not in ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.tiff']:
            return False

        if self.SCREENSHOT_RE.search(filename.lower()):
            return True

        filepath_lower = filepath.lower()
        if any(temp_dir in filepath_lower for temp_dir in self.TEMP_DIRS):
            return True

        try:
            if self._check_screenshot_resolution(filepath):
                return True
        except Exception:
            pass

        return False

    def _check_screenshot_resolution(self, filepath: str) -> bool:
        """检查图片分辨率是否接近屏幕分辨率"""
        try:
            screen_w, screen_h = 0, 0

            if sys.platform == 'darwin':
                import AppKit
                size = AppKit.NSScreen.mainScreen().frame().size
                screen_w, screen_h = int(size.width), int(size.height)
            elif sys.platform == 'win32':
                import ctypes
                user32 = ctypes.windll.user32
                screen_w = user32.GetSystemMetrics(0)
                screen_h = user32.GetSystemMetrics(1)
            else:
                return False

            if screen_w <= 0 or screen_h <= 0:
                return False

            with Image.open(filepath) as img:
                img_w, img_h = img.size

            return img_w >= screen_w * 0.8 and img_h >= screen_h * 0.5

        except Exception:
            return False
