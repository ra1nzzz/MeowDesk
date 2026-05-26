#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MeowDesk 主程序
妙喵桌宠 - 智能桌面文件分类归档工具 + AI 助手
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from meowdesk.core import ConfigManager, FileDatabase
from meowdesk.ui import MeowWindow


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
    print("=" * 60)
    print("🐱 MeowDesk - 妙喵桌宠")
    print("=" * 60)
    print()
    
    # 目录
    app_dir = get_app_dir()
    bundle_dir = get_bundle_dir()
    assets_dir = os.path.join(bundle_dir, 'assets')
    
    print(f"应用目录: {app_dir}")
    print(f"资源目录: {assets_dir}")
    print()
    
    # 配置文件
    config_file = os.path.join(app_dir, 'config.json')
    print(f"加载配置: {config_file}")
    config = ConfigManager(config_file)
    
    # 数据库文件
    archive_dir = config.get('archive_dir')
    db_file = os.path.join(archive_dir, '.filedb.json')
    print(f"数据库: {db_file}")
    db = FileDatabase(db_file)
    
    # 统计信息
    stats = db.get_stats()
    print(f"已归档文件: {stats['total_files']} 个")
    print(f"总大小: {stats['total_size'] / 1024 / 1024:.2f} MB")
    print()
    
    # 创建主窗口
    print("创建窗口...")
    window = MeowWindow(config, db, assets_dir)
    
    try:
        window.create()
        print("✅ 窗口创建成功")
        print()
        print("=" * 60)
        print("MeowDesk 正在运行...")
        print("拖入文件到猫猫身上即可自动归档")
        print("右键点击查看菜单")
        print("=" * 60)
        print()
        
        # 运行主循环
        window.run()
        
    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n正在退出...")
        window.quit()
        print("再见！👋")


if __name__ == '__main__':
    main()
