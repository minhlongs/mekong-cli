"""Tests for migrate-tenants-to-particles.py migration script."""

import json
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

# Load the migration script as a module at import time
import importlib.util
_script_path = Path(__file__).parent.parent.parent / "scripts" / "migrate-tenants-to-particles.py"
spec = importlib.util.spec_from_file_location("migration", _script_path)
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)

# Import functions and constants
connect_tenants = migration.connect_tenants
read_tenants = migration.read_tenants
init_particles_db = migration.init_particles_db
migrate_tenant_to_particle = migration.migrate_tenant_to_particle
set_backwards_compatibility_flag = migration.set_backwards_compatibility_flag
verify_migration = migration.verify_migration
rollback_migration = migration.rollback_migration
DEFAULT_CONSTITUTION = migration.DEFAULT_CONSTITUTION
EMPTY_BEHAVIOR_GRAPH = migration.EMPTY_BEHAVIOR_GRAPH
EMPTY_TREASURY = migration.EMPTY_TREASURY


@pytest.fixture
def env_setup(tmp_path):
    """Set up isolated environment and patch paths."""
    # Create fake home structure
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    raas_dir = fake_home / ".mekong" / "raas"
    raas_dir.mkdir(parents=True)

    # Create tenants.db in the fake location
    tenants_db = raas_dir / "tenants.db"
    conn = sqlite3.connect(tenants_db)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE tenants (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            api_key_hash TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1
        )
    """)
    sample_tenants = [
        ("tenant-001", "Acme Corp", "hash1", "2025-01-15T10:00:00Z", 1),
        ("tenant-002", "Beta Ltd", "hash2", "2025-02-20T14:30:00Z", 1),
        ("tenant-003", "Gamma Inc", "hash3", "2025-03-10T09:15:00Z", 0),
    ]
    conn.executemany(
        "INSERT INTO tenants (id, name, api_key_hash, created_at, is_active) VALUES (?, ?, ?, ?, ?)",
        sample_tenants
    )
    conn.commit()
    conn.close()

    particles_db = fake_home / ".mekong" / "raas" / "particles.db"
    settings_path = fake_home / ".mekong" / "settings.json"

    # Create patches
    patchers = [
        patch.object(migration, "TENANTS_DB_PATH", tenants_db),
        patch.object(migration, "PARTICLES_DB_PATH", particles_db),
        patch.object(migration, "SETTINGS_PATH", settings_path),
    ]

    # Start all patchers
    for p in patchers:
        p.start()

    yield {
        "fake_home": fake_home,
        "tenants_db": tenants_db,
        "particles_db": particles_db,
        "settings_path": settings_path,
        "sample_tenants": sample_tenants,
        "patchers": patchers,
    }

    # Stop all patchers
    for p in patchers:
        p.stop()


def test_read_tenants(env_setup):
    """Test reading tenants from database."""
    tenants_db = env_setup["tenants_db"]
    conn = sqlite3.connect(tenants_db)
    conn.row_factory = sqlite3.Row
    tenants = read_tenants(conn)
    conn.close()

    assert len(tenants) == 3
    assert tenants[0]["name"] == "Acme Corp"


def test_init_particles_db(env_setup):
    """Test initializing particles database with all tables."""
    env_setup["particles_db"]
    conn = init_particles_db()

    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row[0] for row in cursor.fetchall()]
    expected_tables = ["particles", "particle_constitutions", "behavior_graphs", "treasuries"]
    for table in expected_tables:
        assert table in tables

    conn.close()


def test_migrate_tenant_to_particle(env_setup):
    """Test migrating a single tenant to particle."""
    particles_db = env_setup["particles_db"]
    particle_conn = init_particles_db()

    # Get sample tenant directly
    tenants_db = env_setup["tenants_db"]
    conn = sqlite3.connect(tenants_db)
    conn.row_factory = sqlite3.Row
    tenant = conn.execute("SELECT * FROM tenants WHERE id = ?", ("tenant-001",)).fetchone()
    conn.close()

    success, msg = migrate_tenant_to_particle(particle_conn, tenant, dry_run=False)
    assert success, f"Migration failed: {msg}"
    particle_conn.close()

    # Verify particle
    particle_conn = sqlite3.connect(particles_db)
    particle_conn.row_factory = sqlite3.Row

    cursor = particle_conn.execute("SELECT * FROM particles WHERE id = ?", ("tenant-001",))
    particle = cursor.fetchone()
    assert particle is not None
    assert particle["name"] == "Acme Corp"
    assert particle["type"] == "opc"
    assert particle["status"] == "active"

    # Verify constitution
    cursor = particle_conn.execute(
        "SELECT * FROM particle_constitutions WHERE particle_id = ?",
        ("tenant-001",)
    )
    constitution_row = cursor.fetchone()
    assert constitution_row is not None
    constitution = json.loads(constitution_row["constitution_json"])
    assert constitution["name"] == "ZenOS Constitution"
    assert len(constitution["principles"]) == 9

    # Verify behavior graph
    cursor = particle_conn.execute(
        "SELECT * FROM behavior_graphs WHERE particle_id = ?",
        ("tenant-001",)
    )
    graph_row = cursor.fetchone()
    assert graph_row is not None
    graph = json.loads(graph_row["graph_json"])
    assert graph["nodes"] == []
    assert graph["edges"] == []
    assert graph["metadata"]["node_count"] == 0
    assert graph["metadata"]["edge_count"] == 0

    # Verify treasury
    cursor = particle_conn.execute(
        "SELECT * FROM treasuries WHERE particle_id = ?",
        ("tenant-001",)
    )
    treasury_row = cursor.fetchone()
    assert treasury_row is not None
    treasury = json.loads(treasury_row["treasury_json"])
    assert treasury["currency_balances"] == {}
    assert "allocation_rules" in treasury

    particle_conn.close()


def test_migrate_inactive_tenant(env_setup):
    """Test that inactive tenants get 'suspended' status."""
    particles_db = env_setup["particles_db"]
    particle_conn = init_particles_db()

    tenants_db = env_setup["tenants_db"]
    conn = sqlite3.connect(tenants_db)
    conn.row_factory = sqlite3.Row
    tenant = conn.execute("SELECT * FROM tenants WHERE id = ?", ("tenant-003",)).fetchone()
    conn.close()

    success, msg = migrate_tenant_to_particle(particle_conn, tenant, dry_run=False)
    assert success

    particle_conn.close()

    # Verify status
    particle_conn = sqlite3.connect(particles_db)
    particle_conn.row_factory = sqlite3.Row
    cursor = particle_conn.execute("SELECT status FROM particles WHERE id = ?", ("tenant-003",))
    status = cursor.fetchone()["status"]
    assert status == "suspended"
    particle_conn.close()


def test_set_backwards_compatibility_flag(env_setup):
    """Test setting the backwards compatibility flag."""
    settings_path = env_setup["settings_path"]

    success, msg = set_backwards_compatibility_flag(settings_path, dry_run=False)
    assert success, msg

    with open(settings_path) as f:
        settings = json.load(f)

    assert "raas" in settings
    assert settings["raas"]["legacy_tenant_compatibility"] is True
    assert "particle_mode" in settings["raas"]
    assert "migration_completed_at" in settings["raas"]


def test_verify_migration(env_setup):
    """Test migration verification."""
    env_setup["particles_db"]
    particle_conn = init_particles_db()

    # Migrate all tenants
    tenants_db = env_setup["tenants_db"]
    conn = sqlite3.connect(tenants_db)
    conn.row_factory = sqlite3.Row
    tenants = conn.execute("SELECT * FROM tenants").fetchall()
    conn.close()

    for tenant in tenants:
        success, _ = migrate_tenant_to_particle(particle_conn, tenant, dry_run=False)
        assert success

    # Verify
    issues = verify_migration(particle_conn, len(tenants))
    assert len(issues) == 0, f"Verification failed: {issues}"

    particle_conn.close()


def test_rollback_migration(env_setup):
    """Test rolling back the migration."""
    particles_db = env_setup["particles_db"]
    particle_conn = init_particles_db()

    # Migrate all tenants
    tenants_db = env_setup["tenants_db"]
    conn = sqlite3.connect(tenants_db)
    conn.row_factory = sqlite3.Row
    tenants = conn.execute("SELECT * FROM tenants").fetchall()
    conn.close()

    for tenant in tenants:
        success, _ = migrate_tenant_to_particle(particle_conn, tenant, dry_run=False)
        assert success

    particle_conn.close()

    # Set compatibility flag
    settings_path = env_setup["settings_path"]
    set_backwards_compatibility_flag(settings_path, dry_run=False)

    # Rollback
    particle_conn = sqlite3.connect(particles_db)
    success, msg = rollback_migration(particle_conn)
    particle_conn.close()

    assert success, f"Rollback failed: {msg}"

    # Verify tables dropped
    particle_conn = sqlite3.connect(particles_db)
    cursor = particle_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    tables = [row[0] for row in cursor.fetchall()]
    particle_conn.close()

    assert "particles" not in tables
    assert "particle_constitutions" not in tables
    assert "behavior_graphs" not in tables
    assert "treasuries" not in tables


def test_dry_run_mode(env_setup):
    """Test dry run mode doesn't create any data."""
    particles_db = env_setup["particles_db"]
    particle_conn = init_particles_db()

    tenants_db = env_setup["tenants_db"]
    conn = sqlite3.connect(tenants_db)
    conn.row_factory = sqlite3.Row
    tenants = conn.execute("SELECT * FROM tenants").fetchall()
    conn.close()

    for tenant in tenants:
        success, msg = migrate_tenant_to_particle(particle_conn, tenant, dry_run=True)
        assert success
        assert "[DRY-RUN]" in msg

    particle_conn.close()

    # Verify no data was inserted
    particle_conn = sqlite3.connect(particles_db)
    particle_conn.row_factory = sqlite3.Row

    cursor = particle_conn.execute("SELECT COUNT(*) FROM particles")
    count = cursor.fetchone()[0]
    assert count == 0

    cursor = particle_conn.execute("SELECT COUNT(*) FROM particle_constitutions")
    count = cursor.fetchone()[0]
    assert count == 0

    particle_conn.close()


def test_default_constitution_structure():
    """Test default constitution has required fields."""
    assert "version" in DEFAULT_CONSTITUTION
    assert "principles" in DEFAULT_CONSTITUTION
    assert len(DEFAULT_CONSTITUTION["principles"]) == 9
    for principle in DEFAULT_CONSTITUTION["principles"]:
        assert "id" in principle
        assert "priority" in principle
        assert "description" in principle


def test_empty_structures():
    """Test empty behavior graph and treasury structures."""
    assert EMPTY_BEHAVIOR_GRAPH["nodes"] == []
    assert EMPTY_BEHAVIOR_GRAPH["edges"] == []
    assert EMPTY_BEHAVIOR_GRAPH["version"] == "1.0"

    assert EMPTY_TREASURY["currency_balances"] == {}
    assert "allocation_rules" in EMPTY_TREASURY
    assert EMPTY_TREASURY["version"] == "1.0"
