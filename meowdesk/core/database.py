"""
文件数据库模块
使用类型系统定义记录
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from .types import FileRecord


class FileDatabase:
    """文件数据库管理器"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.records: List[FileRecord] = []
        self.load()

    def load(self) -> bool:
        """加载数据库"""
        if not os.path.exists(self.db_path):
            self.records = []
            return True

        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.records = [FileRecord.from_dict(r) for r in data]
            return True
        except Exception as e:
            print(f"数据库加载失败: {e}")
            self.records = []
            return False

    def save(self) -> bool:
        """保存数据库"""
        try:
            db_dir = os.path.dirname(self.db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)

            data = [r.to_dict() for r in self.records]
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"数据库保存失败: {e}")
            return False

    def add_record(self, record: FileRecord) -> bool:
        """添加记录"""
        if not record.timestamp:
            record.timestamp = datetime.now().isoformat()
        self.records.append(record)
        return self.save()

    def add_record_dict(self, record: Dict[str, Any]) -> bool:
        """添加记录（字典格式，兼容旧接口）"""
        return self.add_record(FileRecord.from_dict(record))

    def search(self, keyword: Optional[str] = None,
               category: Optional[str] = None,
               start_date: Optional[str] = None,
               end_date: Optional[str] = None) -> List[FileRecord]:
        """搜索记录"""
        results = self.records

        if keyword:
            keyword_lower = keyword.lower()
            results = [r for r in results if keyword_lower in r.original_name.lower()]

        if category:
            results = [r for r in results if r.category == category]

        if start_date:
            results = [r for r in results if r.timestamp >= start_date]

        if end_date:
            results = [r for r in results if r.timestamp <= end_date]

        return results

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_files = len(self.records)
        total_size = sum(r.file_size for r in self.records)

        categories: Dict[str, Dict[str, int]] = {}
        for record in self.records:
            cat = record.category or '其他'
            if cat not in categories:
                categories[cat] = {'count': 0, 'size': 0}
            categories[cat]['count'] += 1
            categories[cat]['size'] += record.file_size

        return {
            'total_files': total_files,
            'total_size': total_size,
            'categories': categories
        }

    def get_recent(self, limit: int = 10) -> List[FileRecord]:
        """获取最近的记录"""
        sorted_records = sorted(self.records, key=lambda r: r.timestamp, reverse=True)
        return sorted_records[:limit]
