# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
src/cli/sdlc/__init__.py — SDLC scaffold sub-app package.

Exports the four Typer sub-apps (spec, design, code, deploy) and the
sdlc_app group. Registered in src/cli/app_setup.py.
"""

from src.cli.sdlc.spec import spec_app
from src.cli.sdlc.design import design_app
from src.cli.sdlc.code import code_app
from src.cli.sdlc.deploy import deploy_app

__all__ = ["spec_app", "design_app", "code_app", "deploy_app"]
