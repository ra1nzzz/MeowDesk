#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MeowDesk 演示程序 - 展示新架构的使用
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from meowdesk.core import ConfigManager, FileDatabase, FileClassifier, FileHandler
from meowdesk.agent import AgentGateway, CommandRegistry


def demo_core_modules():
    """演示核心模块"""
    print("=" * 60)
    print("MeowDesk 核心模块演示")
    print("=" * 60)
    print()
    
    # 1. 配置管理
    print("1️⃣  配置管理")
    print("-" * 60)
    config = ConfigManager("demo_config.json")
    print(f"✅ 归档目录: {config.get('archive_dir')}")
    print(f"✅ 临时目录: {config.get('temp_dir')}")
    print(f"✅ 窗口透明度: {config.get('window_opacity')}")
    print()
    
    # 2. 文件分类
    print("2️⃣  文件分类")
    print("-" * 60)
    classifier = FileClassifier(config.config)
    
    test_files = [
        ("报告.pdf", "文档"),
        ("Screenshot_2026.png", "截图"),
        ("视频.mp4", "视频"),
        ("main.py", "代码"),
        ("archive.zip", "压缩包"),
    ]
    
    for filename, expected in test_files:
        category, action = classifier.classify(f"D:\\Downloads\\{filename}")
        status = "✅" if category == expected else "❌"
        print(f"{status} {filename:25s} -> {category:10s} ({action})")
    print()
    
    # 3. 数据库操作
    print("3️⃣  数据库操作")
    print("-" * 60)
    db = FileDatabase("demo_db.json")
    
    # 添加测试记录
    for i in range(3):
        db.add_record({
            'original_name': f'测试文件{i+1}.txt',
            'category': '文档',
            'action': 'archive',
            'file_size': 1024 * (i + 1),
            'date': '2026-05-26'
        })
    
    stats = db.get_stats()
    print(f"✅ 总文件数: {stats['total_files']}")
    print(f"✅ 总大小: {stats['total_size']} bytes")
    print(f"✅ 分类: {list(stats['categories'].keys())}")
    print()
    
    # 清理演示文件
    for f in ["demo_config.json", "demo_db.json"]:
        if os.path.exists(f):
            os.remove(f)


def demo_agent_commands():
    """演示 Agent 命令"""
    print("=" * 60)
    print("AI Agent 命令演示")
    print("=" * 60)
    print()
    
    registry = CommandRegistry()
    
    # 1. 日期查询
    print("1️⃣  日期查询")
    print("-" * 60)
    result = registry.execute('check_date')
    if result['success']:
        data = result['result']
        print(f"✅ 今天: {data['today']} {data['weekday']}")
        print(f"✅ 距离周末: {data['days_to_weekend']} 天")
        print(f"✅ 距离月底: {data['days_to_month_end']} 天")
    print()
    
    # 2. 假期查询
    print("2️⃣  假期查询")
    print("-" * 60)
    result = registry.execute('check_holidays')
    if result['success']:
        holidays = result['result']['upcoming_holidays']
        for h in holidays[:3]:
            print(f"✅ {h['name']:10s} {h['date']} (还有 {h['days_left']} 天)")
    print()
    
    # 3. 系统信息
    print("3️⃣  系统信息")
    print("-" * 60)
    result = registry.execute('system_info')
    if result['success']:
        data = result['result']
        print(f"✅ 操作系统: {data['os']}")
        print(f"✅ CPU: {data['cpu_count']} 核心, {data['cpu_percent']}% 使用率")
        print(f"✅ 内存: {data['memory_used_gb']:.1f}/{data['memory_total_gb']:.1f} GB ({data['memory_percent']}%)")
        print(f"✅ 磁盘: {data['disk_used_gb']:.1f}/{data['disk_total_gb']:.1f} GB ({data['disk_percent']}%)")
    print()


def demo_agent_gateway():
    """演示 Agent Gateway"""
    print("=" * 60)
    print("AI Agent Gateway 演示")
    print("=" * 60)
    print()
    
    config = {
        'enabled': True,
        'agent_type': 'openclaw',
        'endpoint': 'http://localhost:8080',
        'timeout': 5
    }
    
    gateway = AgentGateway(config)
    
    print("🔍 检查 Agent 可用性...")
    if gateway.is_available():
        print("✅ Agent 可用！")
        print()
        
        # 对话示例
        print("💬 对话示例:")
        print("-" * 60)
        response = gateway.chat("今天天气怎么样？")
        if response['success']:
            print(f"Agent: {response.get('response', '无响应')}")
        else:
            print(f"❌ {response.get('error')}")
    else:
        print("❌ Agent 不可用")
        print()
        print("💡 提示:")
        print("   1. 确保 Agent 正在运行")
        print("   2. 检查端点配置: http://localhost:8080")
        print("   3. 查看 Agent 日志")
    print()


def main():
    """主函数"""
    print()
    print("🐱 MeowDesk 模块化架构演示")
    print()
    
    try:
        # 演示核心模块
        demo_core_modules()
        
        # 演示 Agent 命令
        demo_agent_commands()
        
        # 演示 Agent Gateway
        demo_agent_gateway()
        
        print("=" * 60)
        print("✅ 演示完成！")
        print("=" * 60)
        print()
        print("📚 更多信息:")
        print("   - 架构文档: docs/ARCHITECTURE.md")
        print("   - macOS 支持: docs/MACOS_SUPPORT.md")
        print("   - Agent 集成: docs/AGENT_INTEGRATION.md")
        print("   - 开发路线图: docs/ROADMAP.md")
        print()
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
