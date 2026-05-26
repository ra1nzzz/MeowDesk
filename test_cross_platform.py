#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨平台兼容性测试
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试模块导入"""
    print("=" * 60)
    print("测试模块导入")
    print("=" * 60)
    
    try:
        from meowdesk.core import ConfigManager, FileDatabase, FileClassifier, FileHandler
        print("✅ 核心模块导入成功")
    except Exception as e:
        print(f"❌ 核心模块导入失败: {e}")
        return False
    
    try:
        from meowdesk.agent import AgentGateway, CommandRegistry
        print("✅ Agent 模块导入成功")
    except Exception as e:
        print(f"❌ Agent 模块导入失败: {e}")
        return False
    
    try:
        from meowdesk.ui import AnimationManager, MeowWindow
        print("✅ UI 模块导入成功")
    except Exception as e:
        print(f"❌ UI 模块导入失败: {e}")
        return False
    
    # 测试平台模块
    try:
        from meowdesk.platform.base import PlatformWindow
        print("✅ 平台基类导入成功")
    except Exception as e:
        print(f"❌ 平台基类导入失败: {e}")
        return False
    
    if sys.platform == 'win32':
        try:
            from meowdesk.platform.windows import WindowsWindow
            print("✅ Windows 平台模块导入成功")
        except Exception as e:
            print(f"❌ Windows 平台模块导入失败: {e}")
            return False
    elif sys.platform == 'darwin':
        try:
            from meowdesk.platform.macos import MacOSWindow, MACOS_AVAILABLE
            if MACOS_AVAILABLE:
                print("✅ macOS 平台模块导入成功")
            else:
                print("⚠️  macOS 平台模块导入成功，但 PyObjC 不可用")
        except Exception as e:
            print(f"❌ macOS 平台模块导入失败: {e}")
            return False
    
    print()
    return True


def test_config():
    """测试配置管理"""
    print("=" * 60)
    print("测试配置管理")
    print("=" * 60)
    
    try:
        from meowdesk.core import ConfigManager
        import tempfile
        
        # 创建临时配置文件
        temp_config = os.path.join(tempfile.gettempdir(), 'test_config.json')
        
        # 测试创建配置
        config = ConfigManager(temp_config)
        print("✅ 配置管理器创建成功")
        
        # 测试读取配置
        archive_dir = config.get('archive_dir')
        print(f"✅ 读取配置成功: archive_dir = {archive_dir}")
        
        # 测试设置配置
        config.set('test_key', 'test_value')
        value = config.get('test_key')
        assert value == 'test_value', "配置值不匹配"
        print("✅ 设置配置成功")
        
        # 清理
        if os.path.exists(temp_config):
            os.remove(temp_config)
        
    except Exception as e:
        print(f"❌ 配置管理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    return True


def test_database():
    """测试数据库"""
    print("=" * 60)
    print("测试数据库")
    print("=" * 60)
    
    try:
        from meowdesk.core import FileDatabase
        import tempfile
        
        # 创建临时数据库
        temp_db = os.path.join(tempfile.gettempdir(), 'test_db.json')
        
        # 测试创建数据库
        db = FileDatabase(temp_db)
        print("✅ 数据库创建成功")
        
        # 测试添加记录
        record = {
            'timestamp': '2024-01-01T12:00:00',
            'original_name': 'test.txt',
            'category': '文档',
            'action': 'archive',
        }
        db.add_record(record)
        print("✅ 添加记录成功")
        
        # 测试搜索
        results = db.search()
        assert len(results) == 1, "记录数量不匹配"
        print("✅ 搜索记录成功")
        
        # 测试统计
        stats = db.get_stats()
        assert stats['total_files'] == 1, "统计数据不匹配"
        print("✅ 统计数据成功")
        
        # 清理
        if os.path.exists(temp_db):
            os.remove(temp_db)
        
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    return True


def test_animation():
    """测试动画系统"""
    print("=" * 60)
    print("测试动画系统")
    print("=" * 60)
    
    try:
        from meowdesk.ui import AnimationManager
        
        assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        if not os.path.exists(assets_dir):
            print("⚠️  assets 目录不存在，跳过动画测试")
            print()
            return True
        
        # 创建动画管理器
        animation = AnimationManager(assets_dir, scale=0.5)
        print("✅ 动画管理器创建成功")
        
        # 测试获取帧
        frame = animation.get_frame(AnimationManager.IDLE, 0)
        if frame:
            print("✅ 获取动画帧成功")
        else:
            print("⚠️  获取动画帧失败（可能是文件不存在）")
        
        # 测试帧数
        frame_count = animation.get_frame_count(AnimationManager.IDLE)
        print(f"✅ IDLE 状态帧数: {frame_count}")
        
    except Exception as e:
        print(f"❌ 动画系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    return True


def test_platform_detection():
    """测试平台检测"""
    print("=" * 60)
    print("测试平台检测")
    print("=" * 60)
    
    print(f"当前平台: {sys.platform}")
    
    if sys.platform == 'win32':
        print("✅ 检测到 Windows 平台")
        try:
            from meowdesk.platform.windows import WindowsWindow
            print("✅ Windows 平台模块可用")
        except Exception as e:
            print(f"❌ Windows 平台模块不可用: {e}")
            return False
    
    elif sys.platform == 'darwin':
        print("✅ 检测到 macOS 平台")
        try:
            from meowdesk.platform.macos import MacOSWindow, MACOS_AVAILABLE
            if MACOS_AVAILABLE:
                print("✅ macOS 平台模块可用")
            else:
                print("⚠️  macOS 平台模块不可用（PyObjC 未安装）")
                print("安装: pip install pyobjc-framework-Cocoa")
        except Exception as e:
            print(f"❌ macOS 平台模块不可用: {e}")
            return False
    
    else:
        print(f"⚠️  未知平台: {sys.platform}")
    
    print()
    return True


def main():
    """主函数"""
    print("\n🔍 MeowDesk 跨平台兼容性测试\n")
    
    all_passed = True
    
    # 测试导入
    if not test_imports():
        all_passed = False
    
    # 测试配置
    if not test_config():
        all_passed = False
    
    # 测试数据库
    if not test_database():
        all_passed = False
    
    # 测试动画
    if not test_animation():
        all_passed = False
    
    # 测试平台检测
    if not test_platform_detection():
        all_passed = False
    
    # 总结
    print("=" * 60)
    if all_passed:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败")
    print("=" * 60)
    print()
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
