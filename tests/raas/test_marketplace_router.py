"""Tests for RaaS Marketplace API — browse and install endpoints."""
from __future__ import annotations

import hashlib
import sqlite3

import pytest

from src.raas.marketplace_router import (
    _parse_frontmatter,
    _scan_commands,
    _scan_skills,
)


def _hash_key(key: str) -> str:
    """SHA-256 hash matching TenantStore."""
    return hashlib.sha256(key.encode()).hexdigest()


class TestParseFrontmatter:
    """Frontmatter parsing tests."""

    def test_basic_frontmatter(self):
        text = """---
name: test-skill
description: "A test skill"
---
# Content here
"""
        fm = _parse_frontmatter(text)
        assert fm["name"] == "test-skill"
        assert fm["description"] == "A test skill"

    def test_no_frontmatter(self):
        text = "# Just content\nNo frontmatter here."
        fm = _parse_frontmatter(text)
        assert fm == {}

    def test_empty_frontmatter(self):
        text = "---\n---\n# Content"
        fm = _parse_frontmatter(text)
        assert fm == {}


class TestCatalogScanning:
    """Catalog scanning tests."""

    @pytest.fixture(autouse=True)
    def tmp_marketplace(self, tmp_path, monkeypatch):
        """Point the catalog scan at a temp dir (see TestMarketplaceAPI)."""
        import src.raas.marketplace_router as mp_mod

        skills_dir = tmp_path / "skills"
        commands_dir = tmp_path / "commands"
        skills_dir.mkdir()
        commands_dir.mkdir()

        (skills_dir / "cook" / "SKILL.md").parent.mkdir()
        (skills_dir / "cook" / "SKILL.md").write_text(
            "---\nname: cook\ndescription: \"Cook recipes in bulk\"\n"
            "category: kitchen\ntags: food, batch\n---\n# Cook\n",
            encoding="utf-8",
        )
        (skills_dir / "invoice" / "SKILL.md").parent.mkdir()
        (skills_dir / "invoice" / "SKILL.md").write_text(
            "---\nname: invoice\ndescription: \"Generate TT78 invoices\"\n"
            "category: finance\ntags: tax, invoice\n---\n# Invoice\n",
            encoding="utf-8",
        )
        (skills_dir / "empty").mkdir()

        (commands_dir / "deploy.md").write_text(
            "---\nname: deploy\ndescription: \"Deploy to production\"\n---\n# Deploy\n",
            encoding="utf-8",
        )
        nested = commands_dir / "ops"
        nested.mkdir()
        (nested / "restart.md").write_text(
            "---\nname: restart\ndescription: \"Restart a service\"\n---\n# Restart\n",
            encoding="utf-8",
        )

        monkeypatch.setattr(mp_mod, "_MARKETPLACE_SKILLS", skills_dir)
        monkeypatch.setattr(mp_mod, "_MARKETPLACE_COMMANDS", commands_dir)

    def test_scan_skills_returns_items(self):
        skills = _scan_skills()
        assert len(skills) > 0
        for s in skills:
            assert s.name
            assert s.item_type == "skill"
            assert s.path

    def test_scan_commands_returns_items(self):
        commands = _scan_commands()
        assert len(commands) > 0
        for c in commands:
            assert c.name
            assert c.item_type == "command"
            assert c.path

    def test_skill_item_dict(self):
        skills = _scan_skills()
        d = skills[0].to_dict()
        assert "name" in d
        assert "type" in d
        assert "description" in d
        assert "cost" in d
        assert d["type"] == "skill"

    def test_command_item_dict(self):
        commands = _scan_commands()
        d = commands[0].to_dict()
        assert "name" in d
        assert "type" in d
        assert d["type"] == "command"


class TestMarketplaceAPI:
    """Integration tests for marketplace endpoints with auth + credits."""

    @pytest.fixture(autouse=True)
    def tmp_marketplace(self, tmp_path, monkeypatch):
        """Point the catalog scan at a temp dir with sample skills + commands.

        The production code scans ``.claude/skills/`` and ``.claude/commands/``
        at the repo root, which do not exist on a fresh checkout.  Rather than
        mock the scan functions, we give the real scanner a real directory to
        walk — the tests exercise the same code path a live user gets.
        """
        import src.raas.marketplace_router as mp_mod

        skills_dir = tmp_path / "skills"
        commands_dir = tmp_path / "commands"
        skills_dir.mkdir()
        commands_dir.mkdir()

        # Two sample skills with frontmatter (covers parsing + tags).
        (skills_dir / "cook" / "SKILL.md").parent.mkdir()
        (skills_dir / "cook" / "SKILL.md").write_text(
            "---\nname: cook\ndescription: \"Cook recipes in bulk\"\n"
            "category: kitchen\ntags: food, batch\n---\n# Cook\n",
            encoding="utf-8",
        )
        (skills_dir / "invoice" / "SKILL.md").parent.mkdir()
        (skills_dir / "invoice" / "SKILL.md").write_text(
            "---\nname: invoice\ndescription: \"Generate TT78 invoices\"\n"
            "category: finance\ntags: tax, invoice\n---\n# Invoice\n",
            encoding="utf-8",
        )
        # A skill directory without SKILL.md — must be skipped by the scanner.
        (skills_dir / "empty").mkdir()

        # Flat + nested commands (covers both scan branches).
        (commands_dir / "deploy.md").write_text(
            "---\nname: deploy\ndescription: \"Deploy to production\"\n---\n# Deploy\n",
            encoding="utf-8",
        )
        nested = commands_dir / "ops"
        nested.mkdir()
        (nested / "restart.md").write_text(
            "---\nname: restart\ndescription: \"Restart a service\"\n---\n# Restart\n",
            encoding="utf-8",
        )

        monkeypatch.setattr(mp_mod, "_MARKETPLACE_SKILLS", skills_dir)
        monkeypatch.setattr(mp_mod, "_MARKETPLACE_COMMANDS", commands_dir)
        # Redirect install destinations so tests never touch ~/.claude.
        monkeypatch.setattr(mp_mod, "_USER_SKILLS", tmp_path / "user_skills")
        monkeypatch.setattr(mp_mod, "_USER_COMMANDS", tmp_path / "user_commands")

    @pytest.fixture
    def tmp_db(self, tmp_path):
        """Create a temporary tenants.db with a test tenant + credits."""
        db = tmp_path / "tenants.db"
        db.parent.mkdir(parents=True, exist_ok=True)

        api_key = "mk_test_key_abc123"
        key_hash = _hash_key(api_key)

        conn = sqlite3.connect(str(db))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS tenants (
                id           TEXT PRIMARY KEY,
                name         TEXT NOT NULL,
                api_key_hash TEXT NOT NULL UNIQUE,
                created_at   TEXT NOT NULL,
                is_active    INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS credit_accounts (
                tenant_id    TEXT PRIMARY KEY,
                balance      INTEGER NOT NULL DEFAULT 0,
                total_earned INTEGER NOT NULL DEFAULT 0,
                total_spent  INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS credit_transactions (
                id        TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                amount    INTEGER NOT NULL,
                reason    TEXT NOT NULL,
                timestamp TEXT NOT NULL
            );
        """)
        # Create test tenant with hashed key
        conn.execute(
            "INSERT INTO tenants (id, name, api_key_hash, is_active, created_at) "
            "VALUES ('test-tenant-1', 'Test Tenant', ?, 1, '2026-01-01T00:00:00Z')",
            (key_hash,),
        )
        # Add 10 credits
        conn.execute(
            "INSERT INTO credit_accounts (tenant_id, balance, total_earned, total_spent) "
            "VALUES ('test-tenant-1', 10, 10, 0)",
        )
        conn.commit()
        conn.close()
        return db

    @pytest.fixture
    def client(self, tmp_db):
        """Create test client with patched DB paths."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        import src.raas.credits as credits_mod
        import src.raas.tenant as tenant_mod
        import src.raas.auth as auth_mod

        # Patch DB paths
        credits_mod.DB_PATH = tmp_db
        tenant_mod._DB_PATH = tmp_db
        credits_mod.CreditStore.__init__.__defaults__ = (tmp_db,)
        tenant_mod.TenantStore.__init__.__defaults__ = (tmp_db,)

        # Reset auth singleton so it picks up new DB
        auth_mod._store = tenant_mod.TenantStore(tmp_db)
        auth_mod._cached_lookup.cache_clear()

        from src.raas.marketplace_router import router

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_browse_requires_auth(self, client):
        resp = client.get("/marketplace/browse")
        assert resp.status_code == 401

    def test_browse_with_auth(self, client):
        resp = client.get(
            "/marketplace/browse",
            headers={"Authorization": "Bearer mk_test_key_abc123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        # 2 skills + 2 commands = 4 catalog entries in the temp marketplace
        assert data["total"] == 4
        # Default limit=100 returns the full catalog (skills first, then commands)
        assert len(data["items"]) == 4
        assert data["items"][0]["type"] == "skill"
        assert data["items"][2]["type"] == "command"

    def test_browse_has_both_types(self, client):
        """Browse with large limit returns both types."""
        resp = client.get(
            "/marketplace/browse?limit=500",
            headers={"Authorization": "Bearer mk_test_key_abc123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        types = {i["type"] for i in data["items"]}
        assert "skill" in types
        assert "command" in types

    def test_browse_filter_skill(self, client):
        resp = client.get(
            "/marketplace/browse?item_type=skill",
            headers={"Authorization": "Bearer mk_test_key_abc123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all(i["type"] == "skill" for i in data["items"])

    def test_browse_filter_command(self, client):
        resp = client.get(
            "/marketplace/browse?item_type=command&limit=50",
            headers={"Authorization": "Bearer mk_test_key_abc123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) > 0
        assert all(i["type"] == "command" for i in data["items"])

    def test_browse_search(self, client):
        resp = client.get(
            "/marketplace/browse?q=cook",
            headers={"Authorization": "Bearer mk_test_key_abc123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        # Should find items matching "cook"
        names = [i["name"].lower() for i in data["items"]]
        assert any("cook" in n for n in names)

    def test_list_skills(self, client):
        resp = client.get(
            "/marketplace/skills",
            headers={"Authorization": "Bearer mk_test_key_abc123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "skills" in data
        assert data["total"] > 0

    def test_list_commands(self, client):
        resp = client.get(
            "/marketplace/commands",
            headers={"Authorization": "Bearer mk_test_key_abc123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "commands" in data
        assert data["total"] > 0

    def test_get_skill_detail(self, client):
        skills = _scan_skills()
        name = skills[0].name
        resp = client.get(
            f"/marketplace/skills/{name}",
            headers={"Authorization": "Bearer mk_test_key_abc123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == name
        assert data["type"] == "skill"

    def test_get_command_detail(self, client):
        commands = _scan_commands()
        name = commands[0].name
        resp = client.get(
            f"/marketplace/commands/{name}",
            headers={"Authorization": "Bearer mk_test_key_abc123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == name
        assert data["type"] == "command"

    def test_get_skill_not_found(self, client):
        resp = client.get(
            "/marketplace/skills/nonexistent-skill-xyz",
            headers={"Authorization": "Bearer mk_test_key_abc123"},
        )
        assert resp.status_code == 404

    def test_get_command_not_found(self, client):
        resp = client.get(
            "/marketplace/commands/nonexistent-cmd-xyz",
            headers={"Authorization": "Bearer mk_test_key_abc123"},
        )
        assert resp.status_code == 404

    def test_install_skill_success(self, client, tmp_path):
        """Install a skill successfully with credits."""
        import src.raas.marketplace_router as mp_mod

        # Redirect user destination to tmp
        user_skills = tmp_path / "user_skills"
        user_skills.mkdir()
        orig = mp_mod._USER_SKILLS
        mp_mod._USER_SKILLS = user_skills

        try:
            skills = _scan_skills()
            name = skills[0].name

            resp = client.post(
                f"/marketplace/install/skill/{name}",
                headers={"Authorization": "Bearer mk_test_key_abc123"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "installed"
            assert data["item_type"] == "skill"
            assert data["name"] == name
            assert data["cost"] == 1
            assert data["credit_balance"] == 9  # 10 - 1

            # Verify files copied
            assert (user_skills / name / "SKILL.md").exists()
        finally:
            mp_mod._USER_SKILLS = orig

    def test_install_command_success(self, client, tmp_path):
        """Install a command successfully with credits."""
        import src.raas.marketplace_router as mp_mod

        user_commands = tmp_path / "user_commands"
        user_commands.mkdir()
        orig = mp_mod._USER_COMMANDS
        mp_mod._USER_COMMANDS = user_commands

        try:
            commands = _scan_commands()
            name = commands[0].name

            resp = client.post(
                f"/marketplace/install/command/{name}",
                headers={"Authorization": "Bearer mk_test_key_abc123"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "installed"
            assert data["item_type"] == "command"
            assert data["cost"] == 1
            assert data["credit_balance"] == 9
        finally:
            mp_mod._USER_COMMANDS = orig

    def test_install_skill_insufficient_credits(self, client):
        """Install returns 402 when credits are too low."""
        # Drain credits first
        from src.raas.credits import CreditStore
        cs = CreditStore()
        cs.deduct("test-tenant-1", 10, "drain")

        skills = _scan_skills()
        name = skills[0].name

        resp = client.post(
            f"/marketplace/install/skill/{name}",
            headers={"Authorization": "Bearer mk_test_key_abc123"},
        )
        assert resp.status_code == 402
        data = resp.json()
        assert "Insufficient credits" in data["detail"]
        assert resp.headers.get("X-Credit-Balance") == "0"

    def test_install_already_installed(self, client, tmp_path):
        """Installing again returns already_installed status."""
        import src.raas.marketplace_router as mp_mod

        user_skills = tmp_path / "user_skills"
        user_skills.mkdir()
        orig = mp_mod._USER_SKILLS
        mp_mod._USER_SKILLS = user_skills

        try:
            skills = _scan_skills()
            name = skills[0].name

            # First install
            resp = client.post(
                f"/marketplace/install/skill/{name}",
                headers={"Authorization": "Bearer mk_test_key_abc123"},
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == "installed"

            # Second install — should be already_installed (still deducts credit)
            resp = client.post(
                f"/marketplace/install/skill/{name}",
                headers={"Authorization": "Bearer mk_test_key_abc123"},
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == "already_installed"
            assert resp.json()["credit_balance"] == 8  # 10 - 1 - 1
        finally:
            mp_mod._USER_SKILLS = orig

    def test_install_skill_not_found(self, client):
        resp = client.post(
            "/marketplace/install/skill/nonexistent-skill-xyz",
            headers={"Authorization": "Bearer mk_test_key_abc123"},
        )
        assert resp.status_code == 404

    def test_install_command_not_found(self, client):
        resp = client.post(
            "/marketplace/install/command/nonexistent-cmd-xyz",
            headers={"Authorization": "Bearer mk_test_key_abc123"},
        )
        assert resp.status_code == 404

    def test_browse_pagination(self, client):
        resp = client.get(
            "/marketplace/browse?limit=5&offset=0",
            headers={"Authorization": "Bearer mk_test_key_abc123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 5
        assert data["limit"] == 5
        assert data["offset"] == 0
