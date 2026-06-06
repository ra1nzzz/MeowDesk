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
class PeriodRecord:
    """经期记录"""
    start_date: str      # YYYY-MM-DD
    end_date: str        # YYYY-MM-DD
    actual_days: int = 0  # 实际天数

    def to_dict(self) -> Dict[str, Any]:
        return {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'actual_days': self.actual_days
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PeriodRecord':
        return cls(
            start_date=data.get('start_date', ''),
            end_date=data.get('end_date', ''),
            actual_days=data.get('actual_days', 0)
        )


@dataclass
class PeriodConfig:
    """经期提醒配置"""
    enabled: bool = False
    mode: str = "self"           # self=我是女生, partner=伴侣提醒
    cycle_days: int = 28         # 周期天数
    period_days: int = 5         # 经期天数
    last_period_start: str = ""  # 上次经期首日 YYYY-MM-DD
    last_period_end: str = ""    # 上次经期结束日 YYYY-MM-DD
    records: List[PeriodRecord] = field(default_factory=list)  # 历史记录
    calibration_offset: int = 0  # 校准偏移天数 (+/-)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'enabled': self.enabled,
            'mode': self.mode,
            'cycle_days': self.cycle_days,
            'period_days': self.period_days,
            'last_period_start': self.last_period_start,
            'last_period_end': self.last_period_end,
            'records': [r.to_dict() for r in self.records],
            'calibration_offset': self.calibration_offset
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PeriodConfig':
        records = [PeriodRecord.from_dict(r) for r in data.get('records', [])]
        return cls(
            enabled=data.get('enabled', False),
            mode=data.get('mode', 'self'),
            cycle_days=data.get('cycle_days', 28),
            period_days=data.get('period_days', 5),
            last_period_start=data.get('last_period_start', ''),
            last_period_end=data.get('last_period_end', ''),
            records=records,
            calibration_offset=data.get('calibration_offset', 0)
        )

    def get_predicted_dates(self) -> Dict[str, str]:
        """获取预测的下次经期日期"""
        if not self.last_period_start:
            return {}

        from datetime import datetime, timedelta
        try:
            last_start = datetime.strptime(self.last_period_start, '%Y-%m-%d')
            # 应用校准偏移
            next_start = last_start + timedelta(days=self.cycle_days + self.calibration_offset)
            next_end = next_start + timedelta(days=self.period_days - 1)

            return {
                'predicted_start': next_start.strftime('%Y-%m-%d'),
                'predicted_end': next_end.strftime('%Y-%m-%d'),
                'days_until': (next_start - datetime.now()).days
            }
        except ValueError:
            return {}

    def calibrate(self, offset: int) -> None:
        """校准偏移"""
        self.calibration_offset = offset


@dataclass
class AppConfig:
    """应用配置"""

    # ---- scalar fields (auto-serialised via dataclasses.fields) ----
    archive_dir: str = ""
    temp_dir: str = ""
    window_opacity: float = 0.85
    auto_open_html: bool = False
    screenshot_action: FileAction = FileAction.RECYCLE
    window_position: Optional[Tuple[int, int]] = None
    scale: float = 0.5

    # ---- container / nested fields (require custom (de)serialisation) ----
    # These are deliberately listed *after* the scalar fields so
    # :meth:`scalar_field_names` can use ``fields()`` up to this
    # marker, and the rest are looked up by name from this dict.
    categories: Dict[str, CategoryConfig] = field(default_factory=dict)
    agent: AgentConfig = field(default_factory=AgentConfig)
    reminders: List[Reminder] = field(default_factory=list)
    period: PeriodConfig = field(default_factory=PeriodConfig)

    SCALAR_FIELDS = (
        "archive_dir",
        "temp_dir",
        "window_opacity",
        "auto_open_html",
        "screenshot_action",
        "window_position",
        "scale",
    )

    @classmethod
    def scalar_field_names(cls) -> Tuple[str, ...]:
        """Names of fields whose value can be ``setattr``'d directly from a
        primitive in the persisted JSON."""

        return cls.SCALAR_FIELDS

    @classmethod
    def container_field_names(cls) -> Tuple[str, ...]:
        """Names of fields that need bespoke deserialisation."""

        return ("categories", "agent", "reminders", "period")

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the whole config to a JSON-safe dict."""

        data: Dict[str, Any] = {}
        for name in self.scalar_field_names():
            value = getattr(self, name)
            if name == "screenshot_action":
                data[name] = value.value
            elif name == "window_position" and value is not None:
                data[name] = list(value)
            else:
                data[name] = value

        data["categories"] = {
            name: {"exts": cat.exts, "action": cat.action.value}
            for name, cat in self.categories.items()
        }
        data["agent"] = self.agent.to_dict()
        data["reminders"] = [r.to_dict() for r in self.reminders]
        data["period"] = self.period.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any], defaults: 'AppConfig' = None) -> 'AppConfig':
        """Reconstruct an ``AppConfig`` from a persisted dict.

        ``defaults`` supplies values for scalar fields that aren't
        present in ``data``; when omitted, the dataclass defaults are
        used.  Passing ``defaults`` is the cheap way to inherit a
        previous config when a new one is missing fields.
        """

        defaults = defaults or cls()
        kwargs: Dict[str, Any] = {}

        for name in cls.scalar_field_names():
            if name in data:
                value = data[name]
                if name == "screenshot_action":
                    kwargs[name] = FileAction(value)
                elif name == "window_position":
                    kwargs[name] = tuple(value) if value else None
                else:
                    kwargs[name] = value
            else:
                kwargs[name] = getattr(defaults, name)

        # container fields
        categories = defaults.categories.copy()
        for cat_name, cat_data in data.get("categories", {}).items():
            categories[cat_name] = CategoryConfig(
                name=cat_name,
                exts=cat_data.get("exts", []),
                action=FileAction(cat_data.get("action", "archive")),
            )
        kwargs["categories"] = categories

        kwargs["agent"] = AgentConfig.from_dict(data.get("agent", {}))
        kwargs["reminders"] = [Reminder.from_dict(r) for r in data.get("reminders", [])]
        kwargs["period"] = PeriodConfig.from_dict(data.get("period", {}))

        return cls(**kwargs)

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
