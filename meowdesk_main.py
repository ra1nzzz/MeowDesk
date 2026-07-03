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
from meowdesk.platform import register_meow_locate_protocol
from meowdesk.updater import UpdateManager, start_background_check
from meowdesk.ui import MeowWindow


_log = logging.getLogger("meowdesk.main")


def _handle_locate_arg(url: str) -> None:
    """--locate 模式:解析 meow-locate:// URL 并在文件资源管理器中定位文件。

    由打包后的 EXE 通过 locate.bat 自调,执行完立即退出,不创建窗口。
    """
    import base64
    import subprocess
    try:
        u = url.replace("meow-locate://", "")
        p = base64.b64decode(u).decode("utf-8")
        subprocess.Popen(["explorer", "/select,", p])
    except Exception:
        _log.exception("failed to handle --locate url: %s", url)


def get_app_dir():
    """获取应用目录"""
    if getattr(sys, 'frozen', False):
        # 打包后的 EXE
        return os.path.dirname(sys.executable)
    else:
        # 开发环境
        return os.path.dirname(os.path.abspath(__file__))


def get_log_file(app_dir):
    """Return a writable crash log path for packaged builds."""
    if not getattr(sys, 'frozen', False):
        return None
    if sys.platform == 'win32':
        local_appdata = os.environ.get('LOCALAPPDATA')
        if local_appdata:
            return os.path.join(local_appdata, 'MeowDesk', 'meowdesk.log')
    return os.path.join(app_dir, 'meowdesk.log')


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
    # --locate 模式:由 meow-locate:// 协议经 locate.bat 自调,仅定位文件后退出
    if len(sys.argv) > 2 and sys.argv[1] == "--locate":
        _handle_locate_arg(sys.argv[2])
        return

    app_dir = get_app_dir()
    log_file = get_log_file(app_dir)
    setup_logging(log_file=log_file)

    _log.info("=" * 60)
    _log.info("MeowDesk 妙喵桌宠 starting")
    _log.info("=" * 60)

    # 目录
    bundle_dir = get_bundle_dir()
    assets_dir = os.path.join(bundle_dir, 'assets')

    _log.info("app dir: %s", app_dir)
    if log_file:
        _log.info("log file: %s", log_file)
    _log.info("assets dir: %s", assets_dir)

    # 注册 meow-locate:// 协议,使导航页"定位"按钮可调起文件资源管理器
    if register_meow_locate_protocol(app_dir):
        _log.info("meow-locate:// protocol registered")
    else:
        _log.warning("failed to register meow-locate:// protocol")

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

    # OTA: 检测更新后状态,若由 updater.bat 启动则调度验证标记
    update_mgr = UpdateManager(config, app_dir)
    if update_mgr.is_post_update():
        _log.info("post-update state detected, scheduling verification")

    try:
        window.create()

        # 窗口创建成功 → 如果是更新后首次启动,调度验证标记(5 秒后)
        # 5 秒内崩溃则标记不会创建,updater.bat 会自动回滚
        if update_mgr.is_post_update() and window.parent is not None:
            update_mgr.schedule_verification(window.parent)
            _log.info("update verification scheduled")

        # 启动后台检查更新(daemon 线程,不影响退出)
        start_background_check(window, config, app_dir)

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
