"""
配置管理模块
"""

import os
import json
from typing import Dict, Any, Optional


class ConfigManager:
    """配置管理器"""
    
    DEFAULT_CONFIG = {
        "archive_dir": "D:\\meow-file",
        "temp_dir": "D:\\meow-temp",
        "window_opacity": 0.85,
        "auto_open_html": False,
        "screenshot_action": "recycle",
        "window_position": None,
        "categories": {
            "截图": {
                "exts": [".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tiff"],
                "action": "recycle"
            },
            "文档": {
                "exts": [".doc", ".docx", ".pdf", ".txt", ".rtf", ".odt", ".md", 
                        ".csv", ".xlsx", ".xls", ".ppt", ".pptx"],
                "action": "archive"
            },
            "图片": {
                "exts": [".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", 
                        ".tiff", ".svg", ".ico"],
                "action": "archive"
            },
            "视频": {
                "exts": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"],
                "action": "archive"
            },
            "音频": {
                "exts": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"],
                "action": "archive"
            },
            "代码": {
                "exts": [".py", ".js", ".ts", ".html", ".css", ".json", ".xml",
                        ".java", ".cpp", ".c", ".h", ".go", ".rs", ".rb", ".php",
                        ".sh", ".bat", ".ps1", ".sql", ".yaml", ".yml", ".toml",
                        ".ini", ".cfg"],
                "action": "archive"
            },
            "压缩包": {
                "exts": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
                "action": "archive"
            },
            "安装包": {
                "exts": [".exe", ".msi", ".dmg", ".deb", ".rpm", ".appimage"],
                "action": "archive"
            },
            "设计稿": {
                "exts": [".psd", ".ai", ".sketch", ".fig", ".xd", ".eps"],
                "action": "archive"
            },
            "电子书": {
                "exts": [".epub", ".mobi", ".azw", ".azw3", ".djvu"],
                "action": "archive"
            }
        }
    }
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self.load()
    
    def load(self) -> Dict[str, Any]:
        """加载配置文件"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 合并默认配置（处理新增字段）
                return self._merge_config(self.DEFAULT_CONFIG.copy(), config)
            except Exception as e:
                print(f"配置加载失败: {e}，使用默认配置")
                return self.DEFAULT_CONFIG.copy()
        else:
            # 首次运行，创建默认配置
            self.save(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()
    
    def save(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """保存配置文件"""
        if config is None:
            config = self.config
        
        try:
            # 确保目录存在
            config_dir = os.path.dirname(self.config_path)
            if config_dir:  # 如果有目录部分
                os.makedirs(config_dir, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"配置保存失败: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """设置配置项"""
        self.config[key] = value
        return self.save()
    
    def _merge_config(self, base: Dict, override: Dict) -> Dict:
        """递归合并配置（保留新字段）"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                base[key] = self._merge_config(base[key], value)
            else:
                base[key] = value
        return base
