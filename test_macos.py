#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
macOS 平台测试脚本

注意：此脚本只能在 macOS 上运行
"""

import sys
import os

if sys.platform != 'darwin':
    print("❌ 此脚本只能在 macOS 上运行")
    print(f"当前平台: {sys.platform}")
    sys.exit(1)

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试 macOS 模块导入"""
    print("=" * 60)
    print("测试 macOS 模块导入")
    print("=" * 60)
    
    try:
        from meowdesk.platform.macos import MacOSWindow, MACOS_AVAILABLE
        if not MACOS_AVAILABLE:
            print("❌ PyObjC 未安装")
            print("安装: pip install pyobjc-framework-Cocoa")
            return False
        print("✅ macOS 平台模块导入成功")
    except Exception as e:
        print(f"❌ macOS 平台模块导入失败: {e}")
        return False
    
    print()
    return True


def test_window_creation():
    """测试窗口创建"""
    print("=" * 60)
    print("测试窗口创建")
    print("=" * 60)
    
    try:
        from meowdesk.platform.macos import MacOSWindow
        
        window = MacOSWindow(128, 128)
        print("✅ 窗口对象创建成功")
        
        window.create()
        print("✅ 窗口创建成功")
        
        window.set_position(100, 100)
        print("✅ 窗口位置设置成功")
        
        x, y = window.get_position()
        print(f"✅ 窗口位置获取成功: ({x}, {y})")
        
        return True
        
    except Exception as e:
        print(f"❌ 窗口创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        print()


def test_animation():
    """测试动画渲染"""
    print("=" * 60)
    print("测试动画渲染")
    print("=" * 60)
    
    try:
        from meowdesk.platform.macos import MacOSWindow
        from meowdesk.ui import AnimationManager
        
        assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        if not os.path.exists(assets_dir):
            print(f"⚠️  assets 目录不存在: {assets_dir}")
            return False
        
        # 创建窗口
        window = MacOSWindow(128, 128)
        window.create()
        print("✅ 窗口创建成功")
        
        # 创建动画管理器
        animation = AnimationManager(assets_dir, scale=0.5)
        print("✅ 动画管理器创建成功")
        
        # 获取第一帧
        frame = animation.get_frame(0, 0)  # IDLE 状态第 0 帧
        if frame:
            print("✅ 动画帧获取成功")
            
            # 渲染到窗口
            window.render(frame)
            print("✅ 动画渲染成功")
        else:
            print("❌ 动画帧获取失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 动画测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        print()


def test_drag_drop():
    """测试拖放功能"""
    print("=" * 60)
    print("测试拖放功能")
    print("=" * 60)
    
    try:
        from meowdesk.platform.macos import MacOSWindow
        
        window = MacOSWindow(128, 128)
        window.create()
        
        # 设置拖放回调
        def on_drop(files):
            print(f"收到文件: {files}")
        
        window.on_drop(on_drop)
        window.enable_drag_drop()
        print("✅ 拖放功能启用成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 拖放测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        print()


def main():
    """主函数"""
    print("\n🍎 MeowDesk macOS 平台测试\n")
    
    all_passed = True
    
    # 测试导入
    if not test_imports():
        print("\n❌ 导入测试失败，无法继续")
        return
    
    # 测试窗口创建
    if not test_window_creation():
        all_passed = False
    
    # 测试动画
    if not test_animation():
        all_passed = False
    
    # 测试拖放
    if not test_drag_drop():
        all_passed = False
    
    # 总结
    print("=" * 60)
    if all_passed:
        print("✅ 所有测试通过！")
        print("\n可以运行主程序:")
        print("  python meowdesk_main.py")
    else:
        print("❌ 部分测试失败")
        print("\n请检查错误信息并修复")
    print("=" * 60)
    print()


if __name__ == '__main__':
    main()
