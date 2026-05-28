"""
类型定义模块
使用 dataclass 定义核心数据结构
"""

import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any


# ========== 枚举类型 ==========

class FileAction(Enum):
    """文件处理动作"""
    ARCHIVE = "archive"      # 归档
    RECYCLE = "recycle"      # 回收站
    SKIP = "skip"            # 跳过


class AgentType(Enum):
    """支持的 Agent 类型"""
    OPENCLAW = "openclaw"
    HERMES = "hermes"
    CUSTOM = "custom"


class Platform(Enum):
    """平台类型"""
    WINDOWS = "win32"
    MACOS = "darwin"
    LINUX = "linux"


# ========== 配置相关 ==========

@dataclass
class CategoryConfig:
    """分类配置"""
    name: str
    exts: List[str]
    action: FileAction

    def matches_ext(self, ext: str) -> bool:
        """检查扩展名是否匹配"""
        return ext.lower() in self.exts


@dataclass
class AgentConfig:
    """AI Agent 配置"""
    enabled: bool = False
    agent_type: AgentType = AgentType.OPENCLAW
    endpoint: str = "http://localhost:8080"
    api_key: str = ""
    timeout: int = 30

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentConfig':
        """从字典创建"""
        return cls(
            enabled=data.get('enabled', False),
            agent_type=AgentType(data.get('agent_type', 'openclaw')),
            endpoint=data.get('endpoint', 'http://localhost:8080').rstrip('/'),
            api_key=data.get('api_key', ''),
            timeout=data.get('timeout', 30)
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'enabled': self.enabled,
            'agent_type': self.agent_type.value,
            'endpoint': self.endpoint,
            'api_key': self.api_key,
            'timeout': self.timeout
        }


@dataclass
class Reminder:
    """提醒配置"""
    name: str
    time: str                # HH:MM 格式
    repeat: str = "不重复"    # 不重复/每天/每周/每月/每年
    content: str = ""
    enabled: bool = True
    last_triggered: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'time': self.time,
            'repeat': self.repeat,
            'content': self.content,
            'enabled': self.enabled,
            'last_triggered': self.last_triggered
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Reminder':
        """从字典创建"""
        return cls(
            name=data.get('name', ''),
            time=data.get('time', '09:00'),
            repeat=data.get('repeat', '不重复'),
            content=data.get('content', ''),
            enabled=data.get('enabled', True),
            last_triggered=data.get('last_triggered', '')
        )


@dataclass
class AppConfig:
    """应用配置"""
    archive_dir: str = ""
    temp_dir: str = ""
    window_opacity: float = 0.85
    auto_open_html: bool = False
    screenshot_action: FileAction = FileAction.RECYCLE
    window_position: Optional[Tuple[int, int]] = None
    scale: float = 0.5
    categories: Dict[str, CategoryConfig] = field(default_factory=dict)
    agent: AgentConfig = field(default_factory=AgentConfig)
    reminders: List[Reminder] = field(default_factory=list)

    @classmethod
    def get_default(cls) -> 'AppConfig':
        """获取默认配置"""
        # 根据平台设置默认路径
        if sys.platform == 'win32':
            archive_dir = os.path.expanduser("~/MeowDesk/file")
            temp_dir = os.path.expanduser("~/MeowDesk/temp")
        elif sys.platform == 'darwin':
            archive_dir = os.path.expanduser("~/MeowDesk/file")
            temp_dir = os.path.expanduser("~/MeowDesk/temp")
        else:
            archive_dir = os.path.expanduser("~/meow-file")
            temp_dir = os.path.expanduser("~/meow-temp")

        return cls(
            archive_dir=archive_dir,
            temp_dir=temp_dir,
            categories=cls._default_categories()
        )

    @staticmethod
    def _default_categories() -> Dict[str, CategoryConfig]:
        """默认分类配置"""
        return {
            "截图": CategoryConfig("截图", [".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tiff"], FileAction.RECYCLE),
            "文档": CategoryConfig("文档", [".doc", ".docx", ".pdf", ".txt", ".rtf", ".odt", ".md", ".csv", ".xlsx", ".xls", ".ppt", ".pptx"], FileAction.ARCHIVE),
            "图片": CategoryConfig("图片", [".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tiff", ".svg", ".ico"], FileAction.ARCHIVE),
            "视频": CategoryConfig("视频", [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"], FileAction.ARCHIVE),
            "音频": CategoryConfig("音频", [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"], FileAction.ARCHIVE),
            "代码": CategoryConfig("代码", [".py", ".js", ".ts", ".html", ".css", ".json", ".xml", ".java", ".cpp", ".c", ".h", ".go", ".rs", ".rb", ".php", ".sh", ".bat", ".ps1", ".sql", ".yaml", ".yml", ".toml", ".ini", ".cfg"], FileAction.ARCHIVE),
            "压缩包": CategoryConfig("压缩包", [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"], FileAction.ARCHIVE),
            "安装包": CategoryConfig("安装包", [".exe", ".msi", ".dmg", ".deb", ".rpm", ".appimage"], FileAction.ARCHIVE),
            "设计稿": CategoryConfig("设计稿", [".psd", ".ai", ".sketch", ".fig", ".xd", ".eps"], FileAction.ARCHIVE),
            "电子书": CategoryConfig("电子书", [".epub", ".mobi", ".azw", ".azw3", ".djvu"], FileAction.ARCHIVE),
        }


# ========== 数据相关 ==========

@dataclass
class ClassifyResult:
    """分类结果"""
    category: str
    action: FileAction
    is_screenshot: bool = False

    @property
    def should_recycle(self) -> bool:
        return self.action == FileAction.RECYCLE

    @property
    def should_archive(self) -> bool:
        return self.action == FileAction.ARCHIVE


@dataclass
class FileRecord:
    """文件记录"""
    original_name: str
    original_path: str
    category: str
    action: str
    destination: str = ""
    file_size: int = 0
    md5: str = ""
    timestamp: str = ""
    date: str = ""
    time: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'original_name': self.original_name,
            'original_path': self.original_path,
            'category': self.category,
            'action': self.action,
            'destination': self.destination,
            'file_size': self.file_size,
            'md5': self.md5,
            'timestamp': self.timestamp,
            'date': self.date,
            'time': self.time
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileRecord':
        """从字典创建"""
        return cls(
            original_name=data.get('original_name', ''),
            original_path=data.get('original_path', ''),
            category=data.get('category', ''),
            action=data.get('action', ''),
            destination=data.get('destination', ''),
            file_size=data.get('file_size', 0),
            md5=data.get('md5', ''),
            timestamp=data.get('timestamp', ''),
            date=data.get('date', ''),
            time=data.get('time', '')
        )


@dataclass
class ArchiveResult:
    """归档结果"""
    success: bool
    destination: str = ""
    error: Optional[str] = None

    @classmethod
    def ok(cls, dest: str) -> 'ArchiveResult':
        return cls(success=True, destination=dest)

    @classmethod
    def fail(cls, error: str) -> 'ArchiveResult':
        return cls(success=False, error=error)


@dataclass
class ProcessResult:
    """文件处理结果"""
    recycled: int = 0
    archived: int = 0
    duplicated: int = 0
    errors: int = 0

    @property
    def total(self) -> int:
        return self.recycled + self.archived + self.duplicated + self.errors

    def summary(self) -> str:
        """生成摘要"""
        parts = []
        if self.recycled:
            parts.append(f"{self.recycled} 截图回收")
        if self.archived:
            parts.append(f"{self.archived} 已归档")
        if self.duplicated:
            parts.append(f"{self.duplicated} 重复跳过")
        if self.errors:
            parts.append(f"{self.errors} 失败")
        return " · ".join(parts) if parts else "完成"


# ========== 平台检测 ==========

def get_platform() -> Platform:
    """获取当前平台"""
    if sys.platform == 'win32':
        return Platform.WINDOWS
    elif sys.platform == 'darwin':
        return Platform.MACOS
    return Platform.LINUX
