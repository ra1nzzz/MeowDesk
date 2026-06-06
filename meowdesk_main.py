#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MeowDesk 主程序
妙喵桌宠 - 智能桌面文件分类归档工具 + AI 助手
"""

import logging
import os
import sys

# 设置标准输出编码（兼容 Windows 控制台，打包时 stdout 可能为 None）
if sys.platform == 'win32':
    import io
    if sys.stdout is not None and hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if sys.stderr is not None and hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from meowdesk import setup_logging
from meowdesk.core import ConfigManager, FileDatabase
from meowdesk.ui import MeowWindow


_log = logging.getLogger("meowdesk.main")


def get_app_dir():
    """获取应用目录"""
    if getattr(sys, 'frozen', False):
        # 打包后的 EXE
        return os.path.dirname(sys.executable)
    else:
        # 开发环境
        return os.path.dirname(os.path.abspath(__file__))


def get_bundle_dir():
    """获取资源目录"""
    if getattr(sys, 'frozen', False):
        # 打包后
        if sys.platform == 'darwin':
            # macOS .app 包
            # 资源在 Contents/Resources/
            if hasattr(sys, '_MEIPASS'):
                return sys._MEIPASS
            else:
                # py2app
                return os.path.dirname(os.path.dirname(sys.executable))
        else:
            # Windows PyInstaller
            return sys._MEIPASS
    else:
        # 开发环境
        return os.path.dirname(os.path.abspath(__file__))


def main():
    """主函数"""
    setup_logging()

    _log.info("=" * 60)
    _log.info("MeowDesk 妙喵桌宠 starting")
    _log.info("=" * 60)

    # 目录
    app_dir = get_app_dir()
    bundle_dir = get_bundle_dir()
    assets_dir = os.path.join(bundle_dir, 'assets')

    _log.info("app dir: %s", app_dir)
    _log.info("assets dir: %s", assets_dir)

    # 配置文件
    config_file = os.path.join(app_dir, 'config.json')
    _log.info("loading config: %s", config_file)
    config = ConfigManager(config_file)

    # 数据库文件（放在应用目录，而非归档目录，避免归档目录不可写导致 DB 无法创建）
    db_file = os.path.join(app_dir, '.filedb.json')
    _log.info("database: %s", db_file)
    db = FileDatabase(db_file)

    # 统计信息
    stats = db.get_stats()
    _log.info("archived files: %d", stats['total_files'])
    _log.info("total size: %.2f MB", stats['total_size'] / 1024 / 1024)

    # 创建主窗口
    _log.info("creating window")
    window = MeowWindow(config, db, assets_dir)

    try:
        window.create()
        _log.info("window ready; entering main loop")
        window.run()
    except KeyboardInterrupt:
        _log.info("interrupted by user")
    except Exception:
        _log.exception("fatal error in main loop")
    finally:
        _log.info("shutting down")
        window.quit()


if __name__ == '__main__':
    main()
