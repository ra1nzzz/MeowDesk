"""
配置管理模块
使用类型系统定义配置结构
"""

import os
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional

from ..utils import get_logger
from ..utils.io import atomic_write_json, load_json_with_backup
from .types import AgentConfig, AppConfig, CategoryConfig


_log = get_logger(__name__)


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self._was_first_run = not os.path.exists(self.config_path)
        self._config: AppConfig = self._load()

    @property
    def config(self) -> AppConfig:
        """获取配置对象"""
        return self._config

    @property
    def is_first_run(self) -> bool:
        """是否为首次运行（配置文件之前不存在）。"""
        return self._was_first_run and not self._config.first_run_completed

    def _load(self) -> AppConfig:
        """加载配置文件"""
        default = AppConfig.get_default()

        if not os.path.exists(self.config_path):
            _log.info("config file missing, generating defaults at %s", self.config_path)
            self._save(default)
            return default

        data = load_json_with_backup(self.config_path)
        if data is None:
            _log.warning("config file unreadable, falling back to defaults: %s", self.config_path)
            return default

        return self._merge(default, data)

    def _merge(self, default: AppConfig, data: Dict[str, Any]) -> AppConfig:
        """Merge ``data`` on top of ``default``.

        Delegates the actual field mapping to
        :meth:`AppConfig.from_dict`, which is the single source of
        truth for which fields are serialised and how.
        """

        return AppConfig.from_dict(data, defaults=default)

    def _save(self, config: Optional[AppConfig] = None) -> bool:
        """保存配置文件"""
        if config is None:
            config = self._config

        data = config.to_dict()

        try:
            config_dir = os.path.dirname(self.config_path)
            if config_dir:
                os.makedirs(config_dir, exist_ok=True)

            atomic_write_json(self.config_path, data)
            return True
        except (OSError, TypeError, ValueError) as e:
            _log.error("配置保存失败: %s", e)
            return False

    def save(self) -> bool:
        """保存当前配置"""
        return self._save()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a top-level config field, falling back to ``default`` only
        when the field is absent.

        A sentinel distinguishes "field missing" from "field present but
        set to ``None``", so callers that explicitly persist a
        ``window_position=None`` get back ``None`` instead of the
        default.
        """

        sentinel = object()
        value = getattr(self._config, key, sentinel)
        return default if value is sentinel else value

    def set(self, key: str, value: Any) -> bool:
        """Set a top-level config field, then persist.

        Returns ``False`` (and logs a warning) for keys that don't
        exist on :class:`AppConfig` — these are almost always typos in
        the caller, and silently accepting them would mask bugs.
        """

        if not hasattr(self._config, key):
            _log.warning("set() rejected unknown key: %r", key)
            return False
        setattr(self._config, key, value)
        return self.save()

    @contextmanager
    def batch_update(self) -> Iterator[None]:
        """批量更新上下文管理器 — 在 with 块内修改字段，
        退出时只保存一次，避免多次磁盘 I/O。

        用法::

            with config.batch_update():
                config.config.scale = 0.6
                config.config.color_mode = 'light'
                config.config.agent = new_agent_config
            # 退出 with 块时自动 save() 一次
        """
        yield
        self.save()

    # ========== 便捷方法 ==========

    @property
    def archive_dir(self) -> str:
        return self._config.archive_dir

    @property
    def temp_dir(self) -> str:
        return self._config.temp_dir

    @property
    def categories(self) -> Dict[str, CategoryConfig]:
        return self._config.categories

    @property
    def agent_config(self) -> AgentConfig:
        return self._config.agent

    def mark_first_run_completed(self) -> bool:
        """标记首次运行流程已完成。"""
        self._config.first_run_completed = True
        return self.save()

    @property
    def reminders(self) -> list:
        return self._config.reminders
