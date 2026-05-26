#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Windows 功能
"""

import os
import sys

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
        from meowdesk.platform.windows import WindowsWindow
        print("✅ Windows 平台模块导入成功")
    except Exception as e:
        print(f"❌ Windows 平台模块导入失败: {e}")
        return False
    
    try:
        from meowdesk.ui import MeowWindow, AnimationManager, ContextMenu
        print("✅ UI 模块导入成功")
    except Exception as e:
        print(f"❌ UI 模块导入失败: {e}")
        return False
    
    print()
    return True


def test_commands():
    """测试命令系统"""
    print("=" * 60)
    print("测试命令系统")
    print("=" * 60)
    
    from meowdesk.agent import CommandRegistry
    
    registry = CommandRegistry()
    commands = registry.list_commands()
    
    print(f"可用命令: {len(commands)} 个")
    for cmd in commands:
        print(f"  - {cmd}")
    
    # 测试日期查询
    print("\n测试 check_date:")
    result = registry.execute('check_date')
    if result['success']:
        data = result['result']
        print(f"  今天: {data['today']} {data['weekday']}")
        print(f"  距离周末: {data['days_to_weekend']} 天")
    else:
        print(f"  失败: {result.get('error')}")
    
    print()
    return True


def test_animation():
    """测试动画系统"""
    print("=" * 60)
    print("测试动画系统")
    print("=" * 60)
    
    from meowdesk.ui import AnimationManager
    
    assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
    
    if not os.path.exists(assets_dir):
        print(f"❌ assets 目录不存在: {assets_dir}")
        return False
    
    animation = AnimationManager(assets_dir, scale=0.5)
    
    # 检查各状态的帧数
    states = {
        0: 'IDLE',
        1: 'HOVER',
        2: 'RECEIVING',
        3: 'CARRYING',
        4: 'HAPPY',
        5: 'SLEEPING',
        6: 'SHY',
        7: 'SURPRISED',
    }
    
    for state_id, state_name in states.items():
        frame_count = animation.get_frame_count(state_id)
        print(f"  {state_name}: {frame_count} 帧")
    
    print()
    return True


def main():
    """主函数"""
    print("\n🐱 MeowDesk Windows 功能测试\n")
    
    all_passed = True
    
    # 测试导入
    if not test_imports():
        all_passed = False
    
    # 测试命令
    if not test_commands():
        all_passed = False
    
    # 测试动画
    if not test_animation():
        all_passed = False
    
    # 总结
    print("=" * 60)
    if all_passed:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败")
    print("=" * 60)
    print()


if __name__ == '__main__':
    main()
