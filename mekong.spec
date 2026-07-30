# mekong.spec — PyInstaller onefile for macOS ARM64
# Build:  pyinstaller mekong.spec
# Output: dist/mekong (~250MB onefile)

from PyInstaller.utils.hooks import collect_submodules
import os

entry = "src.main:app"

a = Analysis(
    [entry],
    pathex=["."],
    binaries=[],
    datas=[
        (".claude/commands", ".claude/commands"),
        (".claude/skills",    ".claude/skills"),
        ("factory/contracts","factory/contracts"),
    ],
    hiddenimports=[
        "uvicorn.protocols.http",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
    ] + collect_submodules("fastapi"),
    hookspath=["scripts/pyinstaller-hooks"],
    runtime_hooks=["scripts/pyinstaller-hooks/runtime-hook-macos.py"],
    excludes=[
        "tkinter", "matplotlib", "numpy", "pandas",
        "PIL", "PyQt5", "PySide2", "sphinx",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="mekong",
    console=True,
    onefile=True,
    icon=None,
)
