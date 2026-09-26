# -*- mode: python ; coding: utf-8 -*-

from fnmatch import fnmatch

block_cipher = None

# Parts of Qt collected by the PyQt6 hook but not used by the application:
# software OpenGL renderer, translations (no QTranslator is installed), touch
# input plugins and image format plugins except .ico and .svg. Qt loads all
# image format plugins at startup, and the PDF one pulls in Qt6Pdf and
# Qt6Network.
QT_UNUSED = [
    'PyQt6/Qt6/bin/opengl32sw.dll',
    'PyQt6/Qt6/*/*Qt6Pdf*',
    'PyQt6/Qt6/*/*Qt6Network*',
    'PyQt6/Qt6/translations/*',
    'PyQt6/Qt6/plugins/generic/*',
] + [
    f'PyQt6/Qt6/plugins/imageformats/*{name}.*'
    for name in ('qgif', 'qicns', 'qjpeg', 'qpdf', 'qtga', 'qtiff', 'qwbmp',
                 'qwebp')
]


def without_unused_qt(toc):
    return [entry for entry in toc
            if not any(fnmatch(entry[0].replace('\\', '/'), pattern)
                       for pattern in QT_UNUSED)]


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
    excludes=['pytest', 'pytest-cov', 'pytest-qt', 'pytest-xvfb', 'pyqt6-tools'],
    cipher=block_cipher,
    noarchive=False,
    optimize=0,
)
a.binaries = without_unused_qt(a.binaries)
a.datas = without_unused_qt(a.datas)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
splash = Splash(
    'resource/splash.png',
    binaries=a.binaries,
    datas=a.datas,
)

exe = EXE(
    pyz,
    a.scripts,
    splash,
    [],
    exclude_binaries=True,
    name='log_viewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
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
    splash.binaries,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='release',
)
