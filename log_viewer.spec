# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['src/log_viewer/log_viewer.py'],
    pathex=['src/log_viewer'],
    binaries=[],
    datas=[('cfg/app.json', './cfg'),
           ('resource/icons/icon.ico', '.'),
           ('resource/icons/*.png', './resource/icons')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', 'pytest-qt', 'pytest-xvfb', 'pyqt6-tools'],
    cipher=block_cipher,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='log_viewer',
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
    icon='resource/icons/icon.ico'
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='release',
)
