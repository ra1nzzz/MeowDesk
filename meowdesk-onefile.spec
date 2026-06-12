# -*- mode: python ; coding: utf-8 -*-
# Single file mode (--onefile): All dependencies packed into one exe
# MeowDesk v1.4.0 - New modular architecture

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
    a.binaries,
    a.datas,
    [],
    exclude_binaries=False,
    name='MeowDesk',
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
    icon='assets/icon.ico',
)
