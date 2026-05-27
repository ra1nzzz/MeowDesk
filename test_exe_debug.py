#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 EXE 资源路径
"""

import os
import sys

print("=" * 60)
print("MeowDesk 资源路径调试")
print("=" * 60)
print()

# 检查是否打包
print(f"sys.frozen: {getattr(sys, 'frozen', False)}")
print(f"sys.platform: {sys.platform}")
print()

# 获取路径
if getattr(sys, 'frozen', False):
    print("运行模式: 打包后的 EXE")
    print(f"sys.executable: {sys.executable}")
    print(f"sys._MEIPASS: {sys._MEIPASS}")
    
    bundle_dir = sys._MEIPASS
    assets_dir = os.path.join(bundle_dir, 'assets')
else:
    print("运行模式: 开发环境")
    bundle_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(bundle_dir, 'assets')

print()
print(f"bundle_dir: {bundle_dir}")
print(f"assets_dir: {assets_dir}")
print()

# 检查目录是否存在
print("目录检查:")
print(f"  bundle_dir 存在: {os.path.exists(bundle_dir)}")
print(f"  assets_dir 存在: {os.path.exists(assets_dir)}")
print()

# 列出 assets 文件
if os.path.exists(assets_dir):
    print("assets 文件列表:")
    for f in os.listdir(assets_dir):
        filepath = os.path.join(assets_dir, f)
        size = os.path.getsize(filepath) if os.path.isfile(filepath) else 0
        print(f"  - {f} ({size:,} bytes)")
else:
    print("❌ assets 目录不存在！")

print()
print("=" * 60)

# 测试加载一个动画文件
if os.path.exists(assets_dir):
    idle_path = os.path.join(assets_dir, 'idle.apng')
    if os.path.exists(idle_path):
        print(f"✅ 找到 idle.apng: {idle_path}")
        
        try:
            from PIL import Image
            img = Image.open(idle_path)
            print(f"✅ 成功加载图像")
            print(f"   尺寸: {img.size}")
            print(f"   模式: {img.mode}")
            print(f"   格式: {img.format}")
            
            # 尝试读取帧
            frame_count = 0
            try:
                while True:
                    img.seek(frame_count)
                    frame_count += 1
            except EOFError:
                pass
            
            print(f"   帧数: {frame_count}")
            
        except Exception as e:
            print(f"❌ 加载图像失败: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"❌ 找不到 idle.apng")

print()
input("按回车键退出...")
