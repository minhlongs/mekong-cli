"""Mekong CLI — CEO Solo Agentic Harness Engineering Platform
Entry point for the harness engine.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Pin to C.UTF-8 to avoid CPython 3.14 gettext recursion on macOS.
# Verified: C.UTF-8 returns NullTranslations cleanly; en_US.UTF-8 triggers recursion.
os.environ["LANG"] = "C.UTF-8"
os.environ["LC_ALL"] = "C.UTF-8"
os.environ["LANGUAGE"] = "C.UTF-8"

# Load .env from project root (3 levels up from src/main.py) BEFORE any other imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

from src.cli.app_setup import build_app

app = build_app()

if __name__ == "__main__":
    app()
