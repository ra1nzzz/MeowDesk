"""
文件处理模块
使用类型系统定义结果
"""

import os
import shutil
import hashlib
from datetime import datetime
from send2trash import send2trash

from .types import ArchiveResult, FileRecord


class FileHandler:
    """文件处理器"""

    def __init__(self, archive_dir: str, temp_dir: str):
        self.archive_dir = archive_dir
        self.temp_dir = temp_dir

        # 确保目录存在
        os.makedirs(archive_dir, exist_ok=True)
        os.makedirs(temp_dir, exist_ok=True)

    def archive_file(self, filepath: str, category: str) -> ArchiveResult:
        """
        归档文件

        Args:
            filepath: 源文件路径
            category: 分类名称

        Returns:
            ArchiveResult 对象
        """

        try:
            dest_path = self._get_archive_path(filepath, category)
        except OSError as e:
            return ArchiveResult.fail(f"无法创建归档目录: {e}")

        dest_path = self._handle_duplicate(dest_path)
        try:
            shutil.move(filepath, dest_path)
            return ArchiveResult.ok(dest_path)
        except Exception as e:
            self._cleanup_empty_category_dir(dest_path)
            return ArchiveResult.fail(str(e))

    def recycle_file(self, filepath: str) -> ArchiveResult:
        """
        移入回收站

        Args:
            filepath: 文件路径

        Returns:
            ArchiveResult 对象
        """
        try:
            send2trash(filepath)
            return ArchiveResult.ok("(已回收)")
        except Exception as e:
            return ArchiveResult.fail(str(e))

    def _get_archive_path(self, filepath: str, category: str) -> str:
        """生成归档路径（按类型/年-月/文件名）"""
        date_str = datetime.now().strftime("%Y-%m")
        category_dir = os.path.join(self.archive_dir, category, date_str)
        os.makedirs(category_dir, exist_ok=True)
        return os.path.join(category_dir, os.path.basename(filepath))

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

    def _cleanup_empty_category_dir(self, dest_path: str) -> None:
        """Best-effort removal of an empty ``<archive>/<category>/<YYYY-MM>``
        directory that may have been created by :meth:`_get_archive_path`
        before a move failed.

        Walks up the path and ``os.rmdir`` s every empty parent up to
        ``self.archive_dir``.  Stops at the first non-empty parent so
        we never delete directories the user filled with real content.
        """

        current = os.path.dirname(dest_path)
        archive_root = os.path.abspath(self.archive_dir)
        while True:
            current_abs = os.path.abspath(current)
            if current_abs == archive_root or not current_abs.startswith(archive_root + os.sep):
                return
            try:
                os.rmdir(current)
            except OSError:
                return
            current = os.path.dirname(current)

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

    def create_record(self, filepath: str, category: str, action: str,
                      destination: str = "") -> FileRecord:
        """创建文件记录"""
        now = datetime.now()
        return FileRecord(
            original_name=os.path.basename(filepath),
            original_path=filepath,
            category=category,
            action=action,
            destination=destination,
            file_size=self.get_file_size(filepath),
            md5=self.calculate_md5(filepath),
            timestamp=now.isoformat(),
            date=now.strftime('%Y-%m-%d'),
            time=now.strftime('%H:%M:%S')
        )
