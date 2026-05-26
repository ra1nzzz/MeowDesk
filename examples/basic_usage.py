"""
基础使用示例
"""

import os
from meowdesk.core import ConfigManager, FileDatabase, FileClassifier, FileHandler


def example_config():
    """配置管理示例"""
    print("=== 配置管理示例 ===\n")
    
    config_path = "example_config.json"
    config = ConfigManager(config_path)
    
    # 读取配置
    print(f"归档目录: {config.get('archive_dir')}")
    print(f"临时目录: {config.get('temp_dir')}")
    print(f"窗口透明度: {config.get('window_opacity')}\n")
    
    # 修改配置
    config.set('window_opacity', 0.9)
    print("✅ 已更新窗口透明度为 0.9\n")
    
    # 清理
    if os.path.exists(config_path):
        os.remove(config_path)


def example_classifier():
    """文件分类示例"""
    print("=== 文件分类示例 ===\n")
    
    config = ConfigManager.DEFAULT_CONFIG
    classifier = FileClassifier(config)
    
    # 测试文件
    test_files = [
        "D:\\Downloads\\报告.pdf",
        "D:\\Desktop\\Screenshot_2026-05-26.png",
        "D:\\Downloads\\视频教程.mp4",
        "D:\\Projects\\main.py",
        "D:\\Downloads\\压缩包.zip",
    ]
    
    for filepath in test_files:
        category, action = classifier.classify(filepath)
        action_text = "回收" if action == "recycle" else "归档"
        print(f"{os.path.basename(filepath):30s} -> {category:10s} ({action_text})")
    
    print()


def example_database():
    """数据库操作示例"""
    print("=== 数据库操作示例 ===\n")
    
    db_path = "example_db.json"
    db = FileDatabase(db_path)
    
    # 添加记录
    record = {
        'original_name': '测试文件.txt',
        'category': '文档',
        'action': 'archive',
        'destination': 'D:\\meow-file\\文档\\2026-05\\测试文件.txt',
        'file_size': 1024,
        'date': '2026-05-26'
    }
    db.add_record(record)
    print("✅ 已添加记录\n")
    
    # 搜索
    results = db.search(keyword='测试')
    print(f"搜索 '测试': 找到 {len(results)} 条记录\n")
    
    # 统计
    stats = db.get_stats()
    print(f"总文件数: {stats['total_files']}")
    print(f"总大小: {stats['total_size']} bytes")
    print(f"分类统计:")
    for cat, info in stats['categories'].items():
        print(f"  {cat}: {info['count']} 个文件\n")
    
    # 清理
    if os.path.exists(db_path):
        os.remove(db_path)


def example_file_handler():
    """文件处理示例"""
    print("=== 文件处理示例 ===\n")
    
    # 创建测试文件
    test_file = "test_file.txt"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("这是一个测试文件")
    
    handler = FileHandler(
        archive_dir="D:\\meow-file",
        temp_dir="D:\\meow-temp"
    )
    
    # 计算 MD5
    md5 = handler.calculate_md5(test_file)
    print(f"文件 MD5: {md5}")
    
    # 获取文件大小
    size = handler.get_file_size(test_file)
    print(f"文件大小: {size} bytes\n")
    
    # 清理
    if os.path.exists(test_file):
        os.remove(test_file)


if __name__ == '__main__':
    example_config()
    example_classifier()
    example_database()
    example_file_handler()
