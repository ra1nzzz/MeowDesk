"""
MeowDesk 核心功能模块
"""

from .config import ConfigManager
from .database import FileDatabase
from .classifier import FileClassifier
from .file_handler import FileHandler
from .types import (
    AppConfig, CategoryConfig, AgentConfig, Reminder, PeriodConfig, PeriodRecord,
    FileAction, AgentType, Platform,
    ClassifyResult, FileRecord, ArchiveResult, ProcessResult,
    get_platform
)

__all__ = [
    'ConfigManager', 'FileDatabase', 'FileClassifier', 'FileHandler',
    'AppConfig', 'CategoryConfig', 'AgentConfig', 'Reminder', 'PeriodConfig', 'PeriodRecord',
    'FileAction', 'AgentType', 'Platform',
    'ClassifyResult', 'FileRecord', 'ArchiveResult', 'ProcessResult',
    'get_platform'
]
