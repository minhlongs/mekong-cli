"""GDPR Test Configuration and Shared Fixtures"""

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, Generator
import pytest
from fastapi import Request
from fastapi.testclient import TestClient

# Set test environment
os.environ["MEKONG_API_URL"] = "http://localhost:8000"
os.environ["MEKONG_ADMIN_TOKEN"] = "test-admin-token-xyz"


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    """Create temporary config directory for GDPR tests."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def mock_state(temp_config_dir: Path, monkeypatch):
    """Mock the _state module to use temporary directory."""
    import src.api.vn_pilot_state as state_module

    # Save original CONFIG_DIR
    original_dir = state_module.CONFIG_DIR

    # Patch to use temp directory
    monkeypatch.setattr(state_module, "CONFIG_DIR", temp_config_dir)

    yield temp_config_dir

    # Restore (though monkeypatch auto-reverts after test)
    monkeypatch.setattr(state_module, "CONFIG_DIR", original_dir)


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    from src.gateway import app
    return TestClient(app)


@pytest.fixture
def admin_auth_headers() -> Dict[str, str]:
    """Headers with admin authorization."""
    return {
        "Authorization": f"Bearer {os.environ.get('MEKONG_ADMIN_TOKEN', 'test-token')}"
    }


@pytest.fixture
def mock_auth_dependency(monkeypatch):
    """Override the GDPR auth dependency to allow test access."""
    from src.api.gdpr_user_rights import _gdpr_auth

    def mock_require_scope(scopes):
        async def mock_dependency():
            return {"user_id": "test_admin", "scopes": scopes}
        return mock_dependency

    # Patch the actual dependency used in routes
    from src.api import gdpr_user_rights
    original_auth = gdpr_user_rights._gdpr_auth
    monkeypatch.setattr(gdpr_user_rights, "_gdpr_auth", mock_require_scope(["admin"]))

    yield

    monkeypatch.setattr(gdpr_user_rights, "_gdpr_auth", original_auth)


@pytest.fixture
def sample_request() -> Request:
    """Create a mock Request object for audit logging tests."""
    from fastapi import Request
    from starlette.testclient import TestClient
    client = TestClient(app=None)
    return Request({
        "type": "http",
        "method": "GET",
        "path": "/test",
        "headers": [(b"user-agent", b"test-client")],
        "client": ("127.0.0.1", 12345)
    })


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "gdpr: mark test as GDPR compliance related"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
