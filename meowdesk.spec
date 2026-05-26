# -*- mode: python ; coding: utf-8 -*-
# Directory mode: exe with separate _internal folder

a = Analysis(
    ['lingxi_droplet.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets'), ('_gen_html.py', '.'), ('_locate.py', '.'), ('config.json', '.'), ('filedb.json', '.'), ('index_preview.html', '.'), ('README.md', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['numpy'],
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
