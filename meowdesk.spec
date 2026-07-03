# -*- mode: python ; coding: utf-8 -*-
# Directory mode: exe with separate _internal folder
# MeowDesk v1.6.0 - New modular architecture

a = Analysis(
    ['meowdesk_main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('meowdesk', 'meowdesk'),
        ('_locate.py', '.'),
        ('config.json', '.'),
        ('README.md', '.'),
    ],
    hiddenimports=[
        'meowdesk.core',
        'meowdesk.agent',
        'meowdesk.platform',
        'meowdesk.ui',
        'meowdesk.updater',
        'windnd',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['numpy', 'matplotlib', 'scipy', 'pandas'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MeowDesk',
    icon='assets/icon.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MeowDesk',
)
