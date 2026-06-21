#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MeowDesk macOS 打包配置 (py2app)

使用方法:
    python setup_macos.py py2app
"""

from setuptools import setup
import os

APP = ['meowdesk_main.py']
DATA_FILES = [
    ('assets', [
        'assets/happy.apng',
        'assets/icon.ico',
        'assets/idle.apng',
        'assets/receiving.apng',
        'assets/shy.apng',
        'assets/sleeping.apng',
        'assets/surprised.apng',
    ]),
    ('', ['config.json']),
]

OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'assets/icon.icns',  # 需要创建 .icns 文件
    'plist': {
        'CFBundleName': 'MeowDesk',
        'CFBundleDisplayName': '妙喵桌宠',
        'CFBundleIdentifier': 'com.meowdesk.app',
        'CFBundleVersion': '1.5.0',
        'CFBundleShortVersionString': '1.5.0',
        'LSMinimumSystemVersion': '10.15.0',
        'NSHighResolutionCapable': True,
        'LSUIElement': False,  # 显示在 Dock
        'NSRequiresAquaSystemAppearance': False,  # 支持深色模式
    },
    'packages': [
        'meowdesk',
        'PIL',
        'send2trash',
    ],
    'includes': [
        'Cocoa',
        'Foundation',
        'AppKit',
    ],
    'excludes': [
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
    ],
    'resources': DATA_FILES,
    'optimize': 2,
}

setup(
    name='MeowDesk',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
