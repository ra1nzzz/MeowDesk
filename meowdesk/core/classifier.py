"""
文件分类模块
"""

import os
import re
from typing import Tuple, Dict, Any
from PIL import Image


class FileClassifier:
    """文件分类器"""
    
    # 截图识别正则
    SCREENSHOT_PATTERNS = [
        r'^\d{4}[-_]\d{2}[-_]\d{2}',  # 日期开头
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
    
    # 临时目录关键词
    TEMP_DIRS = ['temp', 'tmp', 'appdata', 'clipboard', 'cache']
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.categories = config.get('categories', {})
    
    def classify(self, filepath: str) -> Tuple[str, str]:
        """
        分类文件
        
        Args:
            filepath: 文件路径
            
        Returns:
            (category, action) 元组，如 ("图片", "archive") 或 ("截图", "recycle")
        """
        ext = os.path.splitext(filepath)[1].lower()
        filename = os.path.basename(filepath)
        
        # 检查是否为截图
        if self._is_screenshot(filepath, filename, ext):
            action = self.config.get('screenshot_action', 'recycle')
            return "截图", action
        
        # 根据扩展名分类
        for category, info in self.categories.items():
            if ext in info.get('exts', []):
                return category, info.get('action', 'archive')
        
        return "其他", "archive"
    
    def _is_screenshot(self, filepath: str, filename: str, ext: str) -> bool:
        """
        判断是否为截图
        
        检查条件：
        1. 文件名匹配截图模式
        2. 文件位于临时目录
        3. 图片分辨率接近屏幕分辨率
        """
        # 只检查图片文件
        if ext not in ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.tiff']:
            return False
        
        # 1. 文件名匹配
        if self.SCREENSHOT_RE.search(filename.lower()):
            return True
        
        # 2. 临时目录检查
        filepath_lower = filepath.lower()
        if any(temp_dir in filepath_lower for temp_dir in self.TEMP_DIRS):
            return True
        
        # 3. 分辨率检查（可选，性能考虑）
        try:
            if self._check_screenshot_resolution(filepath):
                return True
        except Exception:
            pass
        
        return False
    
    def _check_screenshot_resolution(self, filepath: str) -> bool:
        """检查图片分辨率是否接近屏幕分辨率"""
        try:
            import ctypes
            
            # 获取屏幕分辨率
            user32 = ctypes.windll.user32
            screen_w = user32.GetSystemMetrics(0)
            screen_h = user32.GetSystemMetrics(1)
            
            # 获取图片分辨率
            with Image.open(filepath) as img:
                img_w, img_h = img.size
            
            # 判断：宽度 >= 屏幕80% 且 高度 >= 屏幕50%
            if img_w >= screen_w * 0.8 and img_h >= screen_h * 0.5:
                return True
            
        except Exception:
            pass
        
        return False
