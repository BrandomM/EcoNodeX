# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for EcoNodeX.
Build with: pyinstaller econodex.spec
"""
from pathlib import Path
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_all

ROOT = Path(SPECPATH)

block_cipher = None

# Collect packages that rely heavily on dynamic imports
_hidden = []
_datas_extra = []
_binaries_extra = []

for pkg in ('sqlalchemy', 'fastapi', 'starlette', 'pydantic', 'anyio',
            'uvicorn', 'multipart', 'aiofiles', 'openpyxl', 'pystray'):
    _d, _b, _h = collect_all(pkg)  # collect_all returns (datas, binaries, hiddenimports)
    _hidden += _h
    _datas_extra += _d
    _binaries_extra += _b

a = Analysis(
    [str(ROOT / 'main.py')],
    pathex=[str(ROOT)],
    binaries=_binaries_extra,
    datas=[
        # Include the built React frontend
        (str(ROOT / 'frontend' / 'dist'), 'frontend/dist'),
        # App icon for system tray
        (str(ROOT / 'assets'), 'assets'),
    ] + _datas_extra,
    hiddenimports=_hidden + [
        'PIL._imaging',
        'PIL.Image',
        'PIL.ExifTags',
        'qrcode',
        'qrcode.image.pil',
        'numpy',
        'matplotlib',
        'matplotlib.backends.backend_agg',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='EcoNodeX',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,   # set to True while debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / 'assets' / 'icon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EcoNodeX',
)
