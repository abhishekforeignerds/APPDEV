# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['login_page.py'],
    pathex=[],
    binaries=[],
    datas=[('overlay-bg.jpg', '.'), ('background.jpg', '.'), ('golden-clubs.png', '.'), ('golden-diamond.png', '.'), ('golden-hearts.png', '.'), ('golden-spades.png', '.'), ('golden-k.png', '.'), ('golden-j.png', '.'), ('golden-q.png', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='login_page',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
