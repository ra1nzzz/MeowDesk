"""
文件处理模块
"""

import os
import shutil
import hashlib
from typing import Optional, Tuple
from datetime import datetime
from send2trash import send2trash


class FileHandler:
    """文件处理器"""
    
    def __init__(self, archive_dir: str, temp_dir: str):
        self.archive_dir = archive_dir
        self.temp_dir = temp_dir
        
        # 确保目录存在
        os.makedirs(archive_dir, exist_ok=True)
        os.makedirs(temp_dir, exist_ok=True)
    
    def archive_file(self, filepath: str, category: str) -> Tuple[bool, str, Optional[str]]:
        """
        归档文件
        
        Args:
            filepath: 源文件路径
            category: 分类名称
            
        Returns:
            (success, destination, error_msg) 元组
        """
        try:
            # 生成目标路径
            dest_path = self._get_archive_path(filepath, category)
            
            # 处理重名文件
            dest_path = self._handle_duplicate(dest_path)
            
            # 移动文件
            shutil.move(filepath, dest_path)
            
            return True, dest_path, None
            
        except Exception as e:
            return False, "", str(e)
    
    def recycle_file(self, filepath: str) -> Tuple[bool, Optional[str]]:
        """
        移入回收站
        
        Args:
            filepath: 文件路径
            
        Returns:
            (success, error_msg) 元组
        """
        try:
            send2trash(filepath)
            return True, None
        except Exception as e:
            return False, str(e)
    
    def _get_archive_path(self, filepath: str, category: str) -> str:
        """生成归档路径（按类型/年-月/文件名）"""
        date_str = datetime.now().strftime("%Y-%m")
        category_dir = os.path.join(self.archive_dir, category, date_str)
        os.makedirs(category_dir, exist_ok=True)
        
        filename = os.path.basename(filepath)
        return os.path.join(category_dir, filename)
    
    def _handle_duplicate(self, filepath: str) -> str:
        """处理重名文件（添加序号）"""
        if not os.path.exists(filepath):
            return filepath
        
        base, ext = os.path.splitext(filepath)
        counter = 1
        
        while True:
            new_path = f"{base}_{counter}{ext}"
            if not os.path.exists(new_path):
                return new_path
            counter += 1
    
    @staticmethod
    def calculate_md5(filepath: str, chunk_size: int = 8192) -> str:
        """计算文件 MD5"""
        md5 = hashlib.md5()
        try:
            with open(filepath, 'rb') as f:
                while chunk := f.read(chunk_size):
                    md5.update(chunk)
            return md5.hexdigest()
        except Exception:
            return ""
    
    @staticmethod
    def get_file_size(filepath: str) -> int:
        """获取文件大小"""
        try:
            return os.path.getsize(filepath)
        except Exception:
            return 0
