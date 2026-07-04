"""Mekong CLI — CEO Solo Agentic Harness Engineering Platform
Entry point for the harness engine.
"""
from src.cli.app_setup import build_app

app = build_app()

if __name__ == "__main__":
    app()
