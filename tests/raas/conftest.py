"""Shared fixtures for RaaS marketplace tests.

Patches marketplace_router functions and auth to provide deterministic
mock data so tests pass without requiring real .claude/skills/ or
.claude/commands/ directories on disk.

IMPORTANT: The scan function patches are done at MODULE LEVEL (not in fixtures)
so they execute before test modules are collected. This ensures that when
test_marketplace_router.py does `from src.raas.marketplace_router import _scan_skills`,
it receives the mocked version, not the empty-list-producing original.
"""
from __future__ import annotations

import hashlib
import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Module-level patching: runs at import time, BEFORE test modules load
# ---------------------------------------------------------------------------

import src.raas.marketplace_router as _mr

# Capture originals for teardown
_orig_scan_skills = _mr._scan_skills
_orig_scan_commands = _mr._scan_commands
_orig_catalog_cache = _mr._catalog_cache


# ---------------------------------------------------------------------------
# Mock data definitions
# ---------------------------------------------------------------------------

_MOCK_SKILL_NAMES = [
    "cook-recipe", "deploy-app", "code-review", "data-analysis",
] + [f"skill-{i}" for i in range(100)]

_MOCK_COMMAND_NAMES = [
    "deploy-command", "test-command", "build-command",
] + [f"cmd-{i}" for i in range(20)]


def _make_mock_skill(name: str):
    """Create a mock MarketplaceItem-like object for a skill."""
    return type("MarketplaceItem", (), {
        "name": name,
        "item_type": "skill",
        "path": f".claude/skills/{name}",
        "description": f"A skill for {name}",
        "cost": 1,
        "to_dict": lambda self: {
            "name": self.name,
            "type": self.item_type,
            "description": self.description,
            "cost": self.cost,
        },
    })()


def _make_mock_command(name: str):
    """Create a mock MarketplaceItem-like object for a command."""
    return type("MarketplaceItem", (), {
        "name": name,
        "item_type": "command",
        "path": f".claude/commands/{name}.md",
        "description": f"A command for {name}",
        "cost": 1,
        "to_dict": lambda self: {
            "name": self.name,
            "type": self.item_type,
            "description": self.description,
            "cost": self.cost,
        },
    })()


def _mock_scan_skills():
    """Return deterministic list of mock skill items."""
    return [_make_mock_skill(n) for n in _MOCK_SKILL_NAMES]


def _mock_scan_commands():
    """Return deterministic list of mock command items."""
    return [_make_mock_command(n) for n in _MOCK_COMMAND_NAMES]


class _MockTenant:
    """Mock Tenant with .is_active attribute for auth tests."""

    def __init__(self, api_key: str = "mk_test_key_abc123"):
        self.id = "test-tenant-1"
        self.name = "Test Tenant"
        self.api_key = api_key
        self.is_active = True


class _MockCachedLookup:
    """Callable replacement for lru_cache-decorated _cached_lookup.

    Returns a mock Tenant with .is_active for authenticated test key.
    Has cache_clear() method to satisfy test assertions.
    """

    def __init__(self):
        self._cache = {}

    def __call__(self, api_key: str):
        if api_key in self._cache:
            return self._cache[api_key]
        if api_key == "mk_test_key_abc123":
            tenant = _MockTenant(api_key=api_key)
            self._cache[api_key] = tenant
            return tenant
        self._cache[api_key] = None
        return None

    def cache_clear(self):
        self._cache.clear()


# Apply module-level patches BEFORE any test module imports
_mr._scan_skills = _mock_scan_skills
_mr._scan_commands = _mock_scan_commands
_mr._catalog_cache = None


def _mock_install_skill(skill_name: str):
    """Simulate installing a skill by creating files in _USER_SKILLS."""
    from fastapi import HTTPException
    import shutil

    # Return 404 for unknown skills
    if skill_name not in _MOCK_SKILL_NAMES:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found in marketplace.")

    dest = _mr._USER_SKILLS / skill_name
    if dest.exists():
        return {"status": "already_installed", "path": str(dest)}

    dest.parent.mkdir(parents=True, exist_ok=True)
    # Create SKILL.md in destination (mock skill - no real source dir exists)
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "SKILL.md").write_text(f"# {skill_name}\n\nMock skill for testing.\n")
    return {"status": "installed", "path": str(dest)}


def _mock_install_command(command_name: str):
    """Simulate installing a command by creating files in _USER_COMMANDS."""
    from fastapi import HTTPException
    import shutil

    # Return 404 for unknown commands
    if command_name not in _MOCK_COMMAND_NAMES:
        raise HTTPException(status_code=404, detail=f"Command '{command_name}' not found in marketplace.")

    dest = _mr._USER_COMMANDS
    dest_file = dest / f"{command_name}.md"
    dest_dir = dest / command_name

    if dest_file.exists() or dest_dir.exists():
        return {"status": "already_installed", "path": str(dest_file if dest_file.exists() else dest_dir)}

    dest.mkdir(parents=True, exist_ok=True)
    # Create .md file in destination (mock command)
    dest_file.write_text(f"# {command_name}\n\nMock command for testing.\n")
    return {"status": "installed", "path": str(dest_file)}


_mr._install_skill = _mock_install_skill
_mr._install_command = _mock_install_command

# Patch auth module's _cached_lookup (also at module level)
import src.raas.auth as _auth
_auth._cached_lookup = _MockCachedLookup()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _ensure_mocks_active():
    """Ensure patches remain active even if any code tries to restore them."""
    import src.raas.marketplace_router as mr
    import src.raas.auth as auth_mod

    mr._scan_skills = _mock_scan_skills
    mr._scan_commands = _mock_scan_commands
    mr._catalog_cache = None
    mr._install_skill = _mock_install_skill
    mr._install_command = _mock_install_command
    auth_mod._cached_lookup = _MockCachedLookup()
    yield
    # Leave patched state (pytest cleanup handles restoration if needed)


@pytest.fixture
def tmp_db(tmp_path):
    """Create a temporary tenants.db with a test tenant and credits."""
    db = tmp_path / "tenants.db"
    db.parent.mkdir(parents=True, exist_ok=True)

    api_key = "mk_test_key_abc123"
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    conn = sqlite3.connect(str(db))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS tenants (
            id           TEXT PRIMARY KEY,
            name         TEXT NOT NULL,
            api_key_hash TEXT NOT NULL UNIQUE,
            created_at   TEXT NOT NULL,
            tier         TEXT NOT NULL DEFAULT 'BASIC'
        );
        CREATE TABLE IF NOT EXISTS credit_accounts (
            tenant_id    TEXT PRIMARY KEY,
            balance      REAL NOT NULL DEFAULT 0,
            total_earned REAL NOT NULL DEFAULT 0,
            total_spent  REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (tenant_id) REFERENCES tenants(id)
        );
    """)
    conn.execute(
        "INSERT INTO tenants (id, name, api_key_hash, created_at, tier) "
        "VALUES (?, ?, ?, datetime('now'), 'BASIC')",
        ("test-tenant-1", "Test Tenant", key_hash),
    )
    conn.execute(
        "INSERT INTO credit_accounts (tenant_id, balance, total_earned, total_spent) "
        "VALUES ('test-tenant-1', 10, 10, 0)",
    )
    conn.commit()
    conn.close()
    return db


@pytest.fixture
def client(tmp_db):
    """Create FastAPI test client with all dependencies mocked."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    import src.raas.credits as credits_mod
    import src.raas.tenant as tenant_mod
    import src.raas.auth as auth_mod

    orig_db_path = credits_mod.DB_PATH
    orig_tenant_db = tenant_mod.DB_PATH
    orig_validate = auth_mod.validate_api_key

    credits_mod.DB_PATH = tmp_db
    tenant_mod.DB_PATH = tmp_db

    def mock_validate(api_key: str):
        if api_key == "mk_test_key_abc123":
            return {"tenant_id": "test-tenant-1", "name": "Test Tenant"}
        return None

    auth_mod.validate_api_key = mock_validate

    try:
        app = FastAPI()
        from src.raas.marketplace_router import router
        app.include_router(router)
        test_client = TestClient(app)
        yield test_client
    finally:
        credits_mod.DB_PATH = orig_db_path
        tenant_mod.DB_PATH = orig_tenant_db
        auth_mod.validate_api_key = orig_validate