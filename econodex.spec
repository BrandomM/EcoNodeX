# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for EcoNodeX.
Build with: pyinstaller econodex.spec
"""
from pathlib import Path
import sys

ROOT = Path(SPECPATH)

block_cipher = None

a = Analysis(
    [str(ROOT / 'main.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        # Include the built React frontend
        (str(ROOT / 'frontend' / 'dist'), 'frontend/dist'),
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        'fastapi',
        'sqlalchemy',
        'sqlalchemy.dialects.sqlite',
        'pydantic',
        'multipart',
        'PIL._imaging',
        'PIL.Image',
        'PIL.ExifTags',
        'qrcode',
        'qrcode.image.pil',
        'openpyxl',
        'numpy',
        'matplotlib',
        'matplotlib.backends.backend_agg',
        'aiofiles',
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
