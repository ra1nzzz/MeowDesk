"""
文件数据库模块
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime


class FileDatabase:
    """文件数据库管理器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.records: List[Dict[str, Any]] = []
        self.load()
    
    def load(self) -> bool:
        """加载数据库"""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    self.records = json.load(f)
                return True
            except Exception as e:
                print(f"数据库加载失败: {e}")
                self.records = []
                return False
        else:
            self.records = []
            return True
    
    def save(self) -> bool:
        """保存数据库"""
        try:
            # 确保目录存在
            db_dir = os.path.dirname(self.db_path)
            if db_dir:  # 如果有目录部分
                os.makedirs(db_dir, exist_ok=True)
            
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.records, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"数据库保存失败: {e}")
            return False
    
    def add_record(self, record: Dict[str, Any]) -> bool:
        """添加记录"""
        # 确保必要字段
        if 'timestamp' not in record:
            record['timestamp'] = datetime.now().isoformat()
        
        self.records.append(record)
        return self.save()
    
    def search(self, keyword: Optional[str] = None, 
               category: Optional[str] = None,
               start_date: Optional[str] = None,
               end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        搜索记录
        
        Args:
            keyword: 文件名关键词
            category: 分类
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            匹配的记录列表
        """
        results = self.records
        
        if keyword:
            keyword_lower = keyword.lower()
            results = [r for r in results 
                      if keyword_lower in r.get('original_name', '').lower()]
        
        if category:
            results = [r for r in results if r.get('category') == category]
        
        if start_date:
            results = [r for r in results 
                      if r.get('timestamp', '') >= start_date]
        
        if end_date:
            results = [r for r in results 
                      if r.get('timestamp', '') <= end_date]
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_files = len(self.records)
        total_size = sum(r.get('file_size', 0) for r in self.records)
        
        categories = {}
        for record in self.records:
            cat = record.get('category', '其他')
            if cat not in categories:
                categories[cat] = {'count': 0, 'size': 0}
            categories[cat]['count'] += 1
            categories[cat]['size'] += record.get('file_size', 0)
        
        return {
            'total_files': total_files,
            'total_size': total_size,
            'categories': categories
        }
    
    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的记录"""
        sorted_records = sorted(
            self.records, 
            key=lambda r: r.get('timestamp', ''), 
            reverse=True
        )
        return sorted_records[:limit]
