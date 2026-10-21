# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Configuration, service setup, and runtime helpers for Dashboard FastAPI App."""

from __future__ import annotations

import os as _os
import sys
import threading
import webbrowser
from pathlib import Path
from typing import Any

from fastapi.templating import Jinja2Templates

from src.analytics.dashboard_service import DashboardService
from src.auth.config import AuthConfig
from src.auth.middleware import SessionMiddleware
from src.auth.rbac import Permission, get_current_user, require_permission
from src.auth.routes import router as auth_router
from src.config.logging_config import get_logger

logger = get_logger(__name__)

_ALLOWED_ORIGINS: list[str] = [
    o.strip()
    for o in _os.environ.get(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:8080",
    ).split(",")
    if o.strip()
]

dashboard_service = DashboardService()

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
STATIC_DIR = BASE_DIR / "static"


def _facade() -> Any:
    """Return the src.api.dashboard.app module object if loaded."""
    mod = sys.modules.get("src.api.dashboard.app")
    if mod is not None and hasattr(mod, "dashboard_service"):
        return mod
    return sys.modules[__name__]


def run_dashboard(
    port: int = 8080,
    open_browser: bool = True,
    host: str = "0.0.0.0",
) -> None:
    """Run dashboard server."""
    if open_browser:
        threading.Timer(
            1.5, lambda: webbrowser.open(f"http://localhost:{port}")
        ).start()

    import uvicorn

    uvicorn.run(
        "src.api.dashboard.app:app",
        host=host,
        port=port,
        reload=True,
    )


__all__ = [
    "AuthConfig",
    "BASE_DIR",
    "DashboardService",
    "Permission",
    "STATIC_DIR",
    "SessionMiddleware",
    "_ALLOWED_ORIGINS",
    "_facade",
    "auth_router",
    "dashboard_service",
    "get_current_user",
    "logger",
    "require_permission",
    "run_dashboard",
    "templates",
]
