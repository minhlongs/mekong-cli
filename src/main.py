# Mekong CLI — MIT License
# Copyright (c) 2026 Mekong CLI Contributors
# See LICENSE file for details.

"""Mekong CLI — CEO Solo Agentic Harness Engineering Platform
Entry point for the harness engine.
"""
import os

# Pin to C.UTF-8 to avoid CPython 3.14 gettext recursion on macOS.
# Verified: C.UTF-8 returns NullTranslations cleanly; en_US.UTF-8 triggers recursion.
os.environ["LANG"] = "C.UTF-8"
os.environ["LC_ALL"] = "C.UTF-8"
os.environ["LANGUAGE"] = "C.UTF-8"

from src.cli.app_setup import build_app

app = build_app()

if __name__ == "__main__":
    app()
