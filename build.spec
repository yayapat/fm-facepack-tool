# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for FM Player Face Tool Pro.

Builds a single-file executable with the app icon and bundled assets.
Usage:
    pyinstaller build.spec
"""

import sys
from pathlib import Path

block_cipher = None
root = Path(SPECPATH)

a = Analysis(
    [str(root / "fm_tool.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / "assets"), "assets"),
    ],
    hiddenimports=[
        "PIL",
        "rembg",
        "PyQt6",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Choose icon by platform
icon_file = str(root / "assets" / ("icon.ico" if sys.platform == "win32" else "icon.png"))

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="FMFaceTool",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon=icon_file,
)
