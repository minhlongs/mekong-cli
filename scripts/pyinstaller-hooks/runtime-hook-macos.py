# runtime-hook-macos.py
# PyInstaller onefile on macOS: fix dylib lookup so bundled .dylibs resolve.
import os, sys
if sys.platform == "darwin":
    _meipass = getattr(sys, "_MEIPASS", None)
    if _meipass:
        os.environ.setdefault("DYLD_LIBRARY_PATH", _meipass)
        os.environ.setdefault("PYTHONHOME", _meipass)
