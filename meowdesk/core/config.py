"""
配置管理模块
使用类型系统定义配置结构
"""

import os
import json
from typing import Dict, Any, Optional

from .types import (
    AppConfig, CategoryConfig, AgentConfig, Reminder,
    FileAction, AgentType
)


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self._config: AppConfig = self._load()

    @property
    def config(self) -> AppConfig:
        """获取配置对象"""
        return self._config

    def _load(self) -> AppConfig:
        """加载配置文件"""
        default = AppConfig.get_default()

        if not os.path.exists(self.config_path):
            self._save(default)
            return default

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return self._merge(default, data)
        except Exception as e:
            print(f"配置加载失败: {e}，使用默认配置")
            return default

    def _merge(self, default: AppConfig, data: Dict[str, Any]) -> AppConfig:
        """合并配置"""
        # 基础配置
        config = AppConfig(
            archive_dir=data.get('archive_dir', default.archive_dir),
            temp_dir=data.get('temp_dir', default.temp_dir),
            window_opacity=data.get('window_opacity', default.window_opacity),
            auto_open_html=data.get('auto_open_html', default.auto_open_html),
            screenshot_action=FileAction(data.get('screenshot_action', 'recycle')),
            window_position=tuple(data['window_position']) if data.get('window_position') else None,
            scale=data.get('scale', 0.5),
        )

        # 分类配置
        categories = default.categories.copy()
        for name, cat_data in data.get('categories', {}).items():
            categories[name] = CategoryConfig(
                name=name,
                exts=cat_data.get('exts', []),
                action=FileAction(cat_data.get('action', 'archive'))
            )
        config.categories = categories

        # AI Agent 配置
        config.agent = AgentConfig.from_dict(data.get('agent', {}))

        # 提醒配置
        config.reminders = [Reminder.from_dict(r) for r in data.get('reminders', [])]

        return config

    def _save(self, config: Optional[AppConfig] = None) -> bool:
        """保存配置文件"""
        if config is None:
            config = self._config

        data = {
            'archive_dir': config.archive_dir,
            'temp_dir': config.temp_dir,
            'window_opacity': config.window_opacity,
            'auto_open_html': config.auto_open_html,
            'screenshot_action': config.screenshot_action.value,
            'window_position': list(config.window_position) if config.window_position else None,
            'scale': config.scale,
            'categories': {
                name: {'exts': cat.exts, 'action': cat.action.value}
                for name, cat in config.categories.items()
            },
            'agent': config.agent.to_dict(),
            'reminders': [r.to_dict() for r in config.reminders]
        }

        try:
            config_dir = os.path.dirname(self.config_path)
            if config_dir:
                os.makedirs(config_dir, exist_ok=True)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"配置保存失败: {e}")
            return False

    def save(self) -> bool:
        """保存当前配置"""
        return self._save()

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项（兼容旧接口）"""
        return getattr(self._config, key, default)

    def set(self, key: str, value: Any) -> bool:
        """设置配置项"""
        if hasattr(self._config, key):
            setattr(self._config, key, value)
            return self.save()
        return False

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

    @property
    def reminders(self) -> list:
        return self._config.reminders
