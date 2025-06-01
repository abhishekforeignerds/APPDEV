# -*- mode: python ; coding: utf-8 -*-

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 1) List your image‐and‐asset files here. Each tuple is ("source_filename", "destination_folder_inside_EXE").
datas = [
    ("overlay-bg.jpg", "."),
    ("background.jpg", "."),
    ("golden-clubs.png", "."),
    ("golden-diamond.png", "."),
    ("golden-hearts.png", "."),
    ("golden-spades.png", "."),
    ("golden-k.png", "."),
    ("golden-j.png", "."),
    ("golden-q.png", "."),
]

# 2) Force PyInstaller to bundle every ReportLab barcode submodule automatically.
#    This will include code128, code93, code39, eanbc, usps, gs1, qr, itextpdf, etc.
#    In practice, it collects all .py files under reportlab.graphics.barcode.
hidden_imports = collect_submodules("reportlab.graphics.barcode")

# 3) If your .py files (login_page.py, main_app.py, wheel_module.py, etc.) live in a subfolder,
#    add that folder path here. Otherwise, leave as an empty list.
pathex = []

block_cipher = None

a = Analysis(
    ["login_page.py"],
    pathex=pathex,
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="login_page",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,   # <-- same as --noconsole
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name="login_page",
)
